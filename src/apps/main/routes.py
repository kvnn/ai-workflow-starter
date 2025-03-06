import asyncio
from datetime import datetime, timedelta
import json
import base64
import os
import mimetypes
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, List
from uuid import uuid4

from fastapi import (
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
    APIRouter,
    UploadFile,
    File,
    Form,
    Header,
    BackgroundTasks,
    HTTPException
)
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel
import redis
import stripe

from config import settings
from llm import ask_llm
from logger import logger

from database import get_session

from .models import ProjectTable, HaikuDetails
from .prompts import get_haiku_prompt


app = FastAPI()
router = APIRouter()

project_events = {}
websocket_connections = {}


''' Haiku Stuff '''
class HaikuRequest(BaseModel):
    description: str
    project_id: int


@router.post("/haiku")
async def generate_haiku(haiku_req: HaikuRequest):
    try:
        llm_query, llm_response_format = get_haiku_prompt(haiku_req.description)
        haiku = await ask_llm(
            messages=[{"role": "user", "content": llm_query}],
            response_format=llm_response_format
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_haiku = haiku.model_dump() if hasattr(haiku, "model_dump") else haiku

    with get_session() as session:
        project = session.query(ProjectTable).filter(ProjectTable.id == haiku_req.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Ensure project.data is a dict with a "haikus" list.
        if project.data is None:
            project.data = {"haikus": []}
        elif "haikus" not in project.data:
            project.data["haikus"] = []

        project.data["haikus"].append(new_haiku)
        session.add(project)
        flag_modified(project, "data")
        session.commit()

    # Trigger the project event to update WebSocket clients.
    if haiku_req.project_id in project_events:
        project_events[haiku_req.project_id].set()

    return new_haiku
    


''' Project Stuff '''
async def get_project_json(project_id: str):
    with get_session() as session:
        project = session.query(ProjectTable).filter(ProjectTable.id == project_id).first()
        if project is None:
            return json.dumps({"error": "Project not found"})
        
        data = project.data if project.data else {}

        # Query HaikuDetails for this project
        haiku_details = session.query(HaikuDetails).filter(HaikuDetails.project_id == int(project_id)).all()
        # Convert details to dicts
        data["haiku_details"] = [
            {
                "id": detail.id,
                "haiku_title": detail.haiku_title,
                "haiku_text": detail.haiku_text,
                "commentary": detail.commentary,
                "subtext": detail.subtext,
                "image": detail.image,
                "created_at": detail.created_at.isoformat() if detail.created_at else None,
            }
            for detail in haiku_details
        ]
        return json.dumps(data)


class ProjectCreate(BaseModel):
    name: str
    purpose: str

@router.post("/")
async def create_project(project: ProjectCreate):
    with get_session() as session:
        new_project = ProjectTable(
            name=project.name,
            data={"purpose": project.purpose}
        )
        session.add(new_project)
        session.commit()
        session.refresh(new_project)
        return {"project_id": new_project.id}




''' New Stuff '''
class HaikuInferRequest(BaseModel):
    project_id: int
    haiku: dict  # expecting the haiku object (e.g. {"title": ..., "haiku": ...})
    directions: str


@router.post("/infer")
async def infer_haiku(infer_req: HaikuInferRequest):
    project_id = infer_req.project_id
    haiku_data = infer_req.haiku
    directions = infer_req.directions

    # Build prompts based on the haiku and directions
    base_text = haiku_data.get("haiku", "")
    chain1_prompt = (f"Provide a creative commentary on the haiku '{base_text}' "
                     f"with directions '{directions}'. Include references to gold specced geckos in O'ahu.")
    chain2_prompt = (f"Generate an additional subtext for the haiku '{base_text}' "
                     f"with directions '{directions}'. Let the subtext be inspired by the elegance of gold specced geckos in O'ahu.")
    chain3_prompt = (f"Generate a base64 encoded image that represents the haiku '{base_text}' "
                     f"with the spirit of gold specced geckos in O'ahu and directions '{directions}'.")

    # Run all inference chains concurrently
    results = await asyncio.gather(
        ask_llm(messages=[{"role": "user", "content": chain1_prompt}]),
        ask_llm(messages=[{"role": "user", "content": chain2_prompt}]),
        ask_llm(messages=[{"role": "user", "content": chain3_prompt}]),
        return_exceptions=True
    )

    # Initialize responses
    commentary, subtext, image = None, None, None

    # Process each result, logging errors if needed.
    if isinstance(results[0], Exception):
        logger.error(f"[infer_haiku] Chain 1 failed: {results[0]}")
    else:
        commentary = results[0]

    if isinstance(results[1], Exception):
        logger.error(f"[infer_haiku] Chain 2 failed: {results[1]}")
    else:
        subtext = results[1]

    if isinstance(results[2], Exception):
        logger.error(f"[infer_haiku] Chain 3 failed: {results[2]}")
    else:
        image = results[2]


    with get_session() as session:
        haiku_detail = HaikuDetails(
            project_id=project_id,
            haiku_title=haiku_data.get("title"),
            haiku_text=base_text,
            commentary=commentary,
            subtext=subtext,
            image=image
        )
        session.add(haiku_detail)
        session.commit()

    # Trigger the project event to update WebSocket clients.
    if project_id in project_events:
        project_events[project_id].set()

    return {
        "commentary": commentary,
        "subtext": subtext,
        "image": image
    }



''' Project UI Sync '''
@router.websocket("/dashboard/{project_id}")
async def dashboard_websocket(websocket: WebSocket, project_id: int):
    await websocket.accept()

    logger.info(f"[dashboard_websocket] connected")
    
    # Initialize the event for this dashboard.
    if project_id not in project_events:
        project_events[project_id] = asyncio.Event()

    # Send initial dashboard data.
    try:
        with get_session() as session:
            project_json = await get_project_json(project_id)
            await websocket.send_text(project_json)
    except Exception as e:
        logger.error(f"[dashboard_websocket] Error sending initial message over WS for dashboard {project_id}: {e}")
        await websocket.close()
        return

    websocket_open = True

    while websocket_open:
        logger.info(f"[dashboard_websocket] waiting for event")
        try:
            await project_events[project_id].wait()
            project_events[project_id].clear()
        except Exception as e:
            logger.error(f"[dashboard_websocket] Error waiting for event : {e}", exc_info=True)
            break


        logger.info(f"[dashboard_websocket] event triggered")

        # asyncio.create_task(improve_dashboard_data())
        
        try:
            project_json = await get_project_json(project_id)
            await websocket.send_text(project_json)
            pass
        except WebSocketDisconnect:
            logger.info(f"[dashboard_websocket] WebSocket disconnected for dashboard {project_id}")
            websocket_open = False
            break
        except Exception as e:
            logger.error(f"[dashboard_websocket] Error sending message over WebSocket project_id={project_id}", exc_info=True)
            websocket_open = False
            break

    # Safely remove the websocket connection.
    if project_id in websocket_connections and websocket in websocket_connections[project_id]:
        websocket_connections[project_id].remove(websocket)
