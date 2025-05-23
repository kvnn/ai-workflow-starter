import datetime
import uuid

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
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy.ext.declarative import declarative_base

from config import settings
from database import get_session


Base = declarative_base()


class LLMLogTable(Base):
    ''' This holds our inference logs '''
    __tablename__ = 'ai_llm_logs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chain_id = Column(String, nullable=False) # unique identifier for a chain of llm logs
    name = Column(String, nullable=True)      # convenience field for analyzing llm logs. E.g. "haiku-generate"
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


''' Database interfaces '''

def get_haiku_by_id(haiku_id):
    """ Fetch a Haiku by its ID, along with its Project ID """
    with get_session() as session:
        haiku = session.query(HaikuTable).filter(HaikuTable.id == haiku_id).first()
        return haiku and {column.name: getattr(haiku, column.name) for column in haiku.__table__.columns}

def get_image_prompt_by_id(prompt_id):
    """ Fetch an Image Prompt by its ID """
    with get_session() as session:
        prompt = session.query(HaikuImagePromptTable).filter(HaikuImagePromptTable.id == prompt_id).first()
        return prompt and {column.name: getattr(prompt, column.name) for column in prompt.__table__.columns}


def save_image_prompt(haiku_id: int, prompt_text: str):
    """ Store a new image prompt for a given Haiku """
    with get_session() as session:
        new_prompt = HaikuImagePromptTable(
            haiku_id=haiku_id,
            image_prompt=prompt_text
        )
        session.add(new_prompt)
        session.commit()
        return new_prompt.id


def save_generated_image(prompt_id: str, base64_image: str):
    """ Store a generated image in the database, linked to its image prompt """
    with get_session() as session:
        new_image = HaikuImageTable(
            haiku_image_prompt_id=prompt_id,
            image_b64=base64_image
        )
        session.add(new_image)
        session.commit()

        return new_image.id  # Return the new image ID if needed


def get_project_data(project_id):
    """ Fetch project data including haikus, image prompts, generated images, and critiques """
    with get_session() as session:
        project = (
            session.query(ProjectTable)
            .options(
                joinedload(ProjectTable.haikus)
                .joinedload(HaikuTable.image_prompts)
                .joinedload(HaikuImagePromptTable.images)
            )
            .filter(ProjectTable.id == project_id)
            .first()
        )

        if not project:
            return None

        return {
            "project_id": project.id,
            "name": project.name,
            "haikus": [
                {
                    "id": haiku.id,
                    "title": haiku.title,
                    "text": haiku.text,
                    "created_at": haiku.created_at.isoformat(),
                    "image_prompts": [
                        {
                            "id": prompt.id,
                            "text": prompt.image_prompt,
                            "images": [
                                {"id": img.id, "b64": img.image_b64} for img in sorted(prompt.images, key=lambda i: i.created_at, reverse=True)
                            ],
                        }
                        for prompt in sorted(haiku.image_prompts, key=lambda p: p.created_at, reverse=True)
                    ],
                    "critiques": [
                        {
                            "creativity_score": critique.creativity_score,
                            "vocabulary_density": critique.vocabulary_density,
                            "rizz_level": critique.rizz_level,
                        }
                        for critique in sorted(haiku.critiques, key=lambda c: c.created_at, reverse=True)
                    ],
                }
                for haiku in sorted(project.haikus, key=lambda h: h.created_at, reverse=True)
            ],
        }



class HaikuCritiqueTable(Base):
    ''' Stores critique scores for haikus '''
    __tablename__ = 'ai_haiku_critique'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    haiku_id = Column(Integer, ForeignKey('ai_haiku.id'))
    creativity_score = Column(Integer, nullable=False)
    vocabulary_density = Column(Integer, nullable=False)
    rizz_level = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    haiku = relationship('HaikuTable', back_populates='critiques')


HaikuTable.critiques = relationship('HaikuCritiqueTable', back_populates='haiku')


def save_haiku_critique(haiku_id, critique_data):
    """ Saves a generated critique for a haiku """
    with get_session() as session:
        critique = HaikuCritiqueTable(
            haiku_id=haiku_id,
            creativity_score=critique_data["creativity_score"],
            vocabulary_density=critique_data["vocabulary_density"],
            rizz_level=critique_data["rizz_level"],
        )
        session.add(critique)
        session.commit()
        return critique.id
