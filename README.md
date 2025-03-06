## Quickstart
1. git clone
2. `cd src && pip install -r requirements.txt`
3. `python -m uvicorn app:app --host 0.0.0.0 --port 8800`
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
- we want to easily transform our database selections

### `models.py`
- these are our database models (via SQLAlchemy)

### `schema.py`
- these are our LLM models that we will be asking the LLM to return its responses in, a.k.a. structured responses or json mode
- they have some overlap with `models.py`, and its tempting to use inheritance but in practice its not worth the code reduction

### `logger.py`
- we just want a simple, flexible logger and to be able to log from anywhere quickly

## `frontend/src`
- this is a React app with all of the baggage (npm , yarn, vite, and on and on)
- we use websocket connections to the backend to keep the client up to date
- React MUI is worth all of that baggage, and this setup provides a very nice local development experience
- deploying this frontend is pretty simple : it compiles into a flat, performant package that can be pushed to an S3 bucket / Cloudfront distribution with simple Git hooks