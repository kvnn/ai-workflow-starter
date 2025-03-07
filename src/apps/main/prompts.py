from .schemas import Haiku, HaikuImagePrompt


def get_haiku_prompt(description: str):
    prompt = f"Generate a haiku about {description}."
    
    return prompt, Haiku


def get_haiku_image_prompt(text: str, further_details: str):
    prompt = f'''Generate an image prompt about the haiku: "{text}".'''
    
    if further_details:
        prompt += further_details
    
    return prompt, HaikuImagePrompt