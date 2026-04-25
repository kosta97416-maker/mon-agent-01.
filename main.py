from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

class Message(BaseModel):
    message: str

@app.post("/chat")
async def chat(msg: Message):
    response = model.generate_content(msg.message)
    return {"reply": response.text}

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("index.html").read()
