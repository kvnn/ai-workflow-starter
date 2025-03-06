# src/apps/storebot/routes.py

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
from .models import ProjectTable


app = FastAPI()
router = APIRouter()

project_events = {}
websocket_connections = {}


''' Project Stuff '''
async def get_project_json(project_id: str):
    with get_session() as session:
        project = session.query(ProjectTable).filter(ProjectTable.id == project_id).first()
        if project is None:
            return {"error": "Project not found"}

        data = project.data if project.data else {}
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


''' Project UI Sync '''
@router.websocket("/dashboard/{project_id}")
async def dashboard_websocket(websocket: WebSocket, project_id: str):
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
