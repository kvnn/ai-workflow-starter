import base64
import json

from openai import AsyncOpenAI

from config import settings
from logger import logger

from database import get_session
from apps.main.models import LLMLogTable


client = AsyncOpenAI(api_key=settings.openai_api_key)

# Defaults
if settings.env == "prod":
    default_model = 'gpt-4o-2024-08-06'
else:
    default_model = 'gpt-4o-mini'

default_image_model = 'dall-e-3'
default_image_size = "1024x1024"
default_image_response_format = 'b64_json' # or url
default_image_style = 'natural' # or vivid


# Inference functions
async def get_llm_image(
        prompt,
        model=default_image_model,
        n=1,
        size=default_image_size,
        response_format=default_image_response_format,
        style=default_image_style
):
    image_response = await client.images.generate(
        prompt=prompt,
        model=model,
        n=n,
        size=size,
        response_format=response_format,
        style=style
    )
    
    with get_session() as session:
        try:
            log_entry = LLMLogTable(
                model=model,
                messages=prompt,
                response=str(image_response)[:100],
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to log LLM call: {e}")
            session.rollback()
        finally:
            session.close()
    
    if response_format == 'b64_json':
        return [base64.b64decode(obj.b64_json) for obj in image_response.data]
    return image_response


async def ask_llm(messages, response_format=None, model=default_model):
    chat_settings = {
        'model': model, # support non-openai models
        'messages': messages,
        'temperature': 0.1, # TODO: make this configurable
    }

    if response_format:
        chat_settings['response_format'] = response_format

    logger.info(f'****\n[ask_llm] messages={json.dumps(messages)[0:100]}...\n***********')

    # Initialize variables for logging
    sql_response_data = {}
    success = False
    answer = None
    response_data = None
    completion = None

    try:
        completion = await client.beta.chat.completions.parse(**chat_settings)
        if response_format:
            answer = completion.choices[0].message.parsed
        else:
            answer = completion.choices[0].message.content
        success = True
    except Exception as e:
        logger.error(f"[ask_llm] Exception during LLM call: {e}")
        answer = f"LLM call failed: {str(e)}"
        response_data = {"error": str(e)}
        success = False

    # Prepare a JSON-serializable version of the completion if not already set
    if response_data is None:
        try:
            if hasattr(completion, "model_dump"):
                sql_response_data = completion.model_dump()
            elif hasattr(completion, "__dict__"):
                sql_response_data = completion.__dict__
            else:
                sql_response_data = {"raw": str(completion)}
        except Exception:
            sql_response_data = {"raw": str(completion)}

    # Ensure answer is a string.
    if not isinstance(answer, str):
        try:
            sql_answer = json.dumps(answer, default=str)
        except Exception:
            sql_answer = str(answer)

    # Save the inference call to the database.
    with get_session() as session:
        try:
            log_entry = LLMLogTable(
                model=model,
                messages=messages,
                response=sql_response_data,
                answer=sql_answer,
                success=success
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to log LLM call: {e}")
            session.rollback()
        finally:
            session.close()

    if not success:
        raise Exception(answer)
    return answer
