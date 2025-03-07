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
from llm import ask_llm, get_llm_image
from logger import logger

from database import get_session

from .models import ProjectTable, HaikuTable, HaikuImagePromptTable
from .prompts import get_haiku_prompt, get_haiku_image_prompt
from .schemas import Haiku, HaikuImagePrompt


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

    with get_session() as session:
        project = session.query(ProjectTable).filter(ProjectTable.id == haiku_req.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        new_haiku = HaikuTable(
            project_id=haiku_req.project_id,
            title=haiku.title,
            text=haiku.text
        )
        session.add(new_haiku)
        session.commit()
        session.refresh(new_haiku)

    # Trigger WebSocket update
    if haiku_req.project_id in project_events:
        project_events[haiku_req.project_id].set()

    return {"success": True}

    


''' Project Stuff '''
async def get_project_json(project_id: int):
    with get_session() as session:
        project = session.query(ProjectTable).filter(ProjectTable.id == project_id).first()
        if not project:
            return json.dumps({"error": "Project not found"})

        # Ensure we're using the correct Haiku model from `models.py`
        haikus = session.query(HaikuTable).filter(HaikuTable.project_id == project_id).order_by(HaikuTable.created_at.desc()).all()

        # Convert haikus to JSON format
        haikus_list = [
            {
                "id": haiku.id,
                "title": haiku.title,
                "text": haiku.text,
                "created_at": haiku.created_at.isoformat()
            }
            for haiku in haikus
        ]

        data = {
            "project_id": project.id,
            "name": project.name,
            "haikus": haikus_list
        }

        logger.info(f"[get_project_json] Sending updated project data: {data}")

        return json.dumps(data)



class ProjectCreate(BaseModel):
    name: str

@router.post("/")
async def create_project(project: ProjectCreate):
    with get_session() as session:
        new_project = ProjectTable(
            name=project.name,
        )
        session.add(new_project)
        session.commit()
        session.refresh(new_project)
        return {"project_id": new_project.id}




''' New Stuff '''
class HaikuInferRequest(BaseModel):
    haiku_id: int


@router.post("/get-image-prompts")
async def get_image_prompts(req: HaikuInferRequest):
    '''
    Get image prompts for the haiku. Note that this function runs 3 inference calls concurrently,
    and waits for them to finish before responding to the client.
    '''
    haiku_id = req.haiku_id
    with get_session() as session:
        haiku = session.query(HaikuTable).filter(HaikuTable.id == haiku_id).first()
        if not haiku:
            raise HTTPException(status_code=404, detail="Haiku not found")
        haiku_text = haiku.text
        project_id = haiku.project_id

    prompt_1, response_format_1 = get_haiku_image_prompt(
        haiku_text, further_details=None
    )
    prompt_2, response_format_2 = get_haiku_image_prompt(
        haiku_text, further_details="Write an image prompt that would make Ghengis Khan proud."
    )
    prompt_3, response_format_3 = get_haiku_image_prompt(
        haiku_text, further_details="Write an image prompt for a scene that would make a Gold-specked gecko write this haiku."
    )

    # Run all inference chains concurrently
    results = await asyncio.gather(
        ask_llm(
            messages=[{"role": "user", "content": prompt_1}],
            response_format=response_format_1
        ),
        ask_llm(
            messages=[{"role": "user", "content": prompt_2}],
            response_format=response_format_2
        ),
        ask_llm(
            messages=[{"role": "user", "content": prompt_3}],
            response_format=response_format_3
        ),
        return_exceptions=True
    )

    with get_session() as session:
        for i, image_prompt in enumerate(results):
            if isinstance(image_prompt, Exception):
                logger.error(f"[get_haiku_image_prompts] Error generating image prompt {i+1}: {image_prompt}")
                continue
            logger.info(f"[get_haiku_image_prompts] Image prompt {i+1}: {image_prompt}")
            new_image_prompt = HaikuImagePromptTable(
                haiku_id=haiku_id,
                image_prompt=image_prompt.text
            )
            session.add(new_image_prompt)
            session.commit()

    if project_id in project_events:
        project_events[project_id].set()

    return {
        "image_prompts": [image_prompt.model_dump() for image_prompt in results if not isinstance(image_prompt, Exception)]
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
