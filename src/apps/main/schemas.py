from pydantic import BaseModel


class Haiku(BaseModel):
    title: str
    text: str

class HaikuImagePrompt(BaseModel):
    text: str
