import os
from fastapi import FastAPI, Request

from question_answerer import QuestionAnswerer

from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

qa = QuestionAnswerer()
api = FastAPI()
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
app_handler = SlackRequestHandler(app)

@app.event("app_mention")
def handle_app_mentions(body, say, logger):
    logger.info(body)
    say("What's up?")

@app.event("message")
def handle_message():
    pass


@api.get("/")
def hello():
    return "Welcome, I'm dbt's question answering bot."

@api.get("/answer")
def get_answer(question: str = "What is dbt?"):
    return {"answer": qa.answer_question(question)}

@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)