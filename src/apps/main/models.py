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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    haikus = relationship('HaikuTable', back_populates='project')


class HaikuTable(Base):
    ''' This holds our haiku data '''
    __tablename__ = 'ai_haiku'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('ai_project.id'))
    title = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    project = relationship('ProjectTable', back_populates='haikus')
    image_prompts = relationship('HaikuImagePromptTable', back_populates='haiku')


class HaikuImagePromptTable(Base):
    __tablename__ = 'ai_haiku_image_prompt'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    haiku_id = Column(Integer, ForeignKey('ai_haiku.id'))
    image_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    haiku = relationship('HaikuTable', back_populates='image_prompts')
    images = relationship('HaikuImageTable', back_populates='image_prompt')


class HaikuImageTable(Base):
    __tablename__ = 'ai_haiku_image'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    haiku_image_prompt_id = Column(String, ForeignKey('ai_haiku_image_prompt.id'))
    image_b64 = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    image_prompt = relationship('HaikuImagePromptTable', back_populates='images')