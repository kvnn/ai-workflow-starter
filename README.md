# A.I. Workflow Starterkit

This project is a modular starter kit designed to jumpstart the development of AI-driven workflows. It integrates a FastAPI-based backend with a modern React/Vite frontend, providing a complete framework for building, testing, and scaling AI applications.

Key features include:

- **Inference Logging:** Automatically tracks and logs AI model inference calls.
- **Project Management:** Create and manage projects with AI-generated content.
- **Real-Time Updates:** WebSocket-based dashboard for live project updates.
- **Extensibility:** A clean, modular structure that can be easily extended for additional workflows.


## Quickstart
1. git clone
2. `cd src && pip install -r requirements.txt`
3. `cp env.template .env` && Fill in your OPENAI_API_KEY value (unless its in ENV already)
4. `python -m uvicorn app:app --host 0.0.0.0 --port 8000`
5. open new terminal tab
6. `cd frontend/src && npm install`
7. `npm run dev`


## Reasonings

### `app.py`
- we want a simple web server that supports http and websockets

### `llm.py`
- we want our providers, models and inference configuration to be flexible
- we always want structured responses
- we want our inference requests and responses logged in our db
- we want each inference call to have a supported short name, e.g. "intent recognition"
- we want to optionally tie our chained inference calls together, so that for any given database row that was a result of an inference chain we can find each inference request / response log, and any other data that was created in the chain instance. The pattern for this is:
  - exclude `chain_id` from the first call to `ask_llm`, it will generate a value for it and return it
  - use this return value in the subsequent calls to `ask_llm` that are part of this "chain"
  - these inference calls will now be easy to group together via sql queries

### `database.py`
- we want to be able to insert / updated / retrieve data via the SQLAlchemy ORM or raw SQL depending on our preferences
- when developing locally, we want a sqlite db that is set up automatically, will be re-created if deleted (as a simple schema migration trick) but also provides complete SQL support / behavior

> "but only for models that have been imported and share the same Base. In SQLAlchemy, Base.metadata.create_all(bind=engine) inspects the metadata registered with that Base. This means you must import (or otherwise reference) the model modules (e.g., from other apps/{app name}/models.py) before calling create_all. Otherwise, those models won’t be registered and their tables won’t be created."

### `models.py`
- these are our database models (via SQLAlchemy)
- you want to append `Table` to these, or there will be confusion with `schemas.py`

### `schemas.py`
- these are our LLM models that we will be asking the LLM to return its responses in, a.k.a. structured responses or json mode
- they have some overlap with `models.py`, and its tempting to use inheritance but in practice its not worth the code reduction

### `logger.py`
- we just want a simple, flexible logger and to be able to log from anywhere quickly

## `frontend/src`
- this is a React app with all of the baggage (npm , yarn, vite, and on and on)
- vite provides a fast development server that instantly reflects changes in the browser without full reloads
- we use websocket connections to the backend to keep the client up to date
- React MUI is worth all of that baggage, and this setup provides a very nice local development experience
- deploying this frontend is pretty simple : it compiles into a flat, performant package that can be pushed to an S3 bucket / Cloudfront distribution with simple Git hooks