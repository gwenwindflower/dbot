from fastapi import FastAPI

from question_answerer import QuestionAnswerer

qa = QuestionAnswerer()
app = FastAPI()

@app.get("/")
def hello():
    return "Welcome, I'm dbt's question answering bot."

@app.get("/answer")
def get_answer(question: str = "What is dbt?"):
    return {"answer": qa.answer_question(question)}