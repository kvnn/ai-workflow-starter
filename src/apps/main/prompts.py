from .schemas import Haiku


def get_haiku_prompt(description: str):
    prompt = f"Generate a haiku about {description}."
    
    return prompt, Haiku