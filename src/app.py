import asyncio
from datetime import datetime, timedelta
import importlib
import os
from typing import List
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette.middleware.cors import CORSMiddleware

from apps.main.models import Base
from apps.main.routes import router as main_router
from database import engine
from logger import logger
from config import settings

app = FastAPI()

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        # your domains here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables if using SQLite
@app.on_event("startup")
async def startup_event():
    if settings.db_engine_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite database tables created/updated.")


app.include_router(main_router, prefix='/projects', tags=['projects'])
