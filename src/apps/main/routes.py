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

from config import settings
from llm import ask_llm, get_llm_image
from logger import logger

from database import get_session

from .models import (
    ProjectTable, HaikuTable, HaikuImagePromptTable,
    get_project_data, get_haiku_by_id, save_image_prompt, save_generated_image,
    get_image_prompt_by_id,
    save_haiku_critique
)
from .prompts import get_haiku_prompt, get_haiku_image_prompt, get_haiku_critique_prompt
from .schemas import Haiku, HaikuImagePrompt


app = FastAPI()
router = APIRouter()

project_events = {}
websocket_connections = {}



''' Project Stuff '''

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

@router.get("/")
async def get_projects():
    with get_session() as session:
        # Get projects, most recent first
        projects = session.query(ProjectTable).order_by(ProjectTable.id.desc()).all()
        return [{"id": project.id, "name": project.name} for project in projects]


''' Haiku Stuff '''
class HaikuRequest(BaseModel):
    description: str
    project_id: int


@router.post("/haiku")
async def generate_haiku(haiku_req: HaikuRequest):
    try:
        llm_query, llm_response_format = get_haiku_prompt(haiku_req.description)
        haiku, completion, chain_id = await ask_llm(
            messages=[{"role": "user", "content": llm_query}],
            response_format=llm_response_format
        )
    except Exception as e:
        logger.error(f"Error generating haiku", exc_info=True)
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


class HaikuInferRequest(BaseModel):
    haiku_id: int

@router.post("/haiku-critique")
async def generate_haiku_critique(req: HaikuInferRequest, background_tasks: BackgroundTasks):
    haiku_id = req.haiku_id
    haiku = get_haiku_by_id(haiku_id)
    
    if not haiku:
        raise HTTPException(status_code=404, detail="Haiku not found")
    
    prompt_text, response_format = get_haiku_critique_prompt(haiku['text'])

    # Background critique generation
    background_tasks.add_task(process_haiku_critique, haiku_id, prompt_text, response_format)

    return {"message": "Haiku critique is being generated."}


async def process_haiku_critique(haiku_id: int, prompt_text: str, response_format):
    """ Background task for generating haiku critique and storing it in the database """
    try:
        critique, completion, chain_id = await ask_llm(messages=[{"role": "user", "content": prompt_text}], response_format=response_format)

        critique_data = {
            "creativity_score": critique.creativity_score,
            "vocabulary_density": critique.vocabulary_density,
            "rizz_level": critique.rizz_level,
        }

        # Save critique to database
        save_haiku_critique(haiku_id, critique_data)

        # Notify WebSocket clients
        haiku = get_haiku_by_id(haiku_id)
        if haiku and haiku["project_id"] in project_events:
            project_events[haiku["project_id"]].set()

    except Exception as e:
        logger.error(f"[process_haiku_critique] Exception: {e}", exc_info=True)



@router.post("/generate-image-prompts")
async def generate_image_prompts(req: HaikuInferRequest, background_tasks: BackgroundTasks):
    """ 
    Queue background tasks for generating image prompts one by one,  
    notifying the WebSocket after each prompt is saved.
    """
    haiku_id = req.haiku_id
    haiku = get_haiku_by_id(haiku_id)

    if not haiku:
        raise HTTPException(status_code=404, detail="Haiku not found")

    prompts = [
        get_haiku_image_prompt(haiku['text'], further_details=None),
        get_haiku_image_prompt(haiku['text'], further_details="Write an image prompt that would make Genghis Khan proud."),
        get_haiku_image_prompt(haiku['text'], further_details="Write an image prompt for a scene that would make a Gold-specked gecko write this haiku."),
    ]
    
    llm_chain_id = str(uuid4())

    for prompt_text, response_format in prompts:
        background_tasks.add_task(
            process_image_prompt,
            chain_id=llm_chain_id,
            haiku_id=haiku_id,
            response_format=response_format,
            prompt_text=prompt_text,
            project_id=haiku['project_id']
        )

    return {"message": "Image prompts are being generated."}


async def process_image_prompt(chain_id: str, haiku_id: int, prompt_text: str, project_id: int, response_format):
    """ Background task for generating an image prompt and updating WebSocket """
    try:
        image_prompt, completion, chain_id = await ask_llm(chain_id=chain_id, response_format=response_format, messages=[{"role": "user", "content": prompt_text}])
        
        prompt_id = save_image_prompt(
            haiku_id,
            prompt_text=image_prompt.text
        )

        # Notify WebSocket after each image prompt is created
        if project_id in project_events:
            project_events[project_id].set()
    except Exception as e:
        logger.error(f"[process_image_prompt] Error generating prompt for haiku {haiku_id}: {e}")


class UpdateImagePromptRequest(BaseModel):
    prompt_id: str
    new_text: str

@router.put("/update-image-prompt")
async def update_image_prompt(req: UpdateImagePromptRequest):
    """ Update an existing image prompt """
    with get_session() as session:
        prompt = session.query(HaikuImagePromptTable).filter(HaikuImagePromptTable.id == req.prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Image prompt not found")

        prompt.image_prompt = req.new_text
        session.commit()

        # Notify WebSocket clients
        project_id = prompt.haiku.project_id
        if project_id in project_events:
            project_events[project_id].set()

        return {"message": "Image prompt updated successfully"}


class GenerateImageRequest(BaseModel):
    prompt_id: str
    haiku_id: int

@router.post("/generate-image")
async def generate_image(req: GenerateImageRequest, background_tasks: BackgroundTasks):
    """ Generate an image for an image prompt in the background """
    background_tasks.add_task(process_image_generation, req.prompt_id, req.haiku_id)
    return {"message": "Image generation started."}


async def process_image_generation(prompt_id: str, haiku_id: int):
    """ Background task for generating an image and storing it in the database """
    try:
        haiku = get_haiku_by_id(haiku_id)
        if not haiku:
            raise HTTPException(status_code=404, detail="Haiku not found")

        logger.info(f"[process_image_generation] Generating image for prompt_id={prompt_id}")
        
        prompt = get_image_prompt_by_id(prompt_id)
        
        image_data = await get_llm_image(prompt['image_prompt'])
        
        if not image_data or not isinstance(image_data, list) or not image_data[0]:
            raise ValueError("No valid image data returned from LLM. Returned: {image_data}")

        base64_image = base64.b64encode(image_data[0]).decode('utf-8')

        save_generated_image(prompt_id, base64_image)

        logger.info(f"[process_image_generation] Image successfully stored for prompt_id={prompt_id}")

        # Notify WebSocket clients
        if haiku['project_id'] in project_events:
            project_events[haiku['project_id']].set()
    
    except Exception as e:
        logger.error(f"[process_image_generation] Exception: {e}", exc_info=True)


''' Project UI Sync '''
@router.websocket("/dashboard/{project_id}")
async def dashboard_websocket(websocket: WebSocket, project_id: int):
    await websocket.accept()

    logger.info(f"[dashboard_websocket] connected")
    
    # Initialize the event for this dashboard.
    if project_id not in project_events:
        project_events[project_id] = asyncio.Event()

    # Send initial dashboard data.
    project_data = get_project_data(project_id)
    await websocket.send_text(json.dumps(project_data))

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
            project_data = get_project_data(project_id)
            await websocket.send_text(json.dumps(project_data))
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
