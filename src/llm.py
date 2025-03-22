import base64
import json
from uuid import uuid4

from openai import AsyncOpenAI
from slugify import slugify

from config import settings
from logger import logger

from database import get_session
from apps.main.models import LLMLogTable

default_image_model = 'dall-e-3'
default_image_size = "1024x1024"
default_image_response_format = 'b64_json' # or url
default_image_style = 'natural' # or vivid

client = AsyncOpenAI(api_key=settings.openai_api_key)

if settings.env == "prod":
    default_model = 'gpt-4o-2024-08-06'
    default_model = 'o3-mini'
else:
    default_model = 'gpt-4o-mini'
    default_model = 'gpt-4o-2024-08-06'
    default_model = 'o3-mini'


async def ask_llm(messages, response_format=None, model=default_model, chain_id=None, name=None):
    
    if not chain_id:
        chain_id = uuid4()

    chat_settings = {
        'model': model,
        'messages': messages,
    }
    
    if 'o3' not in model:
        chat_settings['temperature'] = 0.1

    if response_format:
        chat_settings['response_format'] = response_format

    if not name:
        try:
            name = slugify(json.dumps(messages)[0:20])
        except Exception as e:
            logger.error(f"Failed to generate name for LLM call: {e}", exc_info=True)

    logger.info(f'****\n[ask_llm] messages={json.dumps(messages)[0:100]}...\n***********')

    # Initialize variables for logging
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
                name=name,
                chain_id=str(chain_id),
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
    return answer, completion, chain_id


async def get_llm_image(
        prompt,
        model=default_image_model,
        n=1,
        size=default_image_size,
        response_format=default_image_response_format,
        style=default_image_style,
        chain_id=None
):
    if not chain_id:
        chain_id = uuid4()
    
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
                chain_id=str(chain_id)
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