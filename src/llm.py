import json

from openai import AsyncOpenAI

from config import settings
from logger import logger

from database import get_session
from apps.main.models import LLMLogTable


client = AsyncOpenAI(api_key=settings.openai_api_key)

if settings.env == "prod":
    default_model = 'gpt-4o-2024-08-06'
else:
    default_model = 'gpt-4o-mini'
    # default_model = 'gpt-4o-2024-08-06'


async def ask_llm(messages, response_format=None, model=default_model):
    chat_settings = {
        'model': model,
        'messages': messages,
        'temperature': 0.1,
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
    return answer, completion
