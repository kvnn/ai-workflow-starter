from .schemas import Haiku, HaikuImagePrompt, HaikuCritique


def get_haiku_prompt(description: str):
    prompt = f"Generate a haiku about {description}."
    
    return prompt, Haiku


def get_haiku_image_prompt(text: str, further_details: str):
    prompt = f'''Generate an image prompt about the haiku: "{text}".'''
    
    if further_details:
        prompt += further_details
    
    return prompt, HaikuImagePrompt


def get_haiku_critique_prompt(haiku_text: str):
    prompt = f'''Critique the haiku: "{haiku_text}".
    Return the scores in ascending order from 1-5.'''

    return prompt, HaikuCritique