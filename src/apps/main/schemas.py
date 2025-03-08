from pydantic import BaseModel


class Haiku(BaseModel):
    title: str
    text: str

class HaikuImagePrompt(BaseModel):
    text: str


class HaikuCritique(BaseModel):
    creativity_score: int
    vocabulary_density: int
    rizz_level: int