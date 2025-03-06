import uuid
import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    DateTime,
    JSON,
    Boolean,
    create_engine
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from config import settings


Base = declarative_base()


class LLMLogTable(Base):
    ''' This holds our inference logs '''
    __tablename__ = 'ai_llm_logs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model = Column(String, nullable=False)
    messages = Column(JSON, nullable=False)
    response = Column(JSON, nullable=True)
    answer = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ProjectTable(Base):
    ''' This holds our project data '''
    __tablename__ = 'ai_project'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class HaikuDetails(Base):
    ''' This holds additional inference details for haikus '''
    __tablename__ = 'ai_haiku_details'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(Integer, nullable=False)
    haiku_title = Column(String, nullable=True)
    haiku_text = Column(Text, nullable=False)
    commentary = Column(Text, nullable=True)
    subtext = Column(Text, nullable=True)
    image = Column(Text, nullable=True)  # base64 encoded image
    created_at = Column(DateTime, default=datetime.datetime.utcnow)