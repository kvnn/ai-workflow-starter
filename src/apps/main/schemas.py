from pydantic import BaseModel


class Haiku(BaseModel):
    title: str
    haiku: str


class HaikuImage(BaseModel):
    haiku: Haiku
    image: str  # base64 encoded image