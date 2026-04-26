from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
import os

app = FastAPI()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = "Tu es NÉO, l'IA souveraine du Commandant. Tu réponds toujours en français, avec un ton tactique et précis. Tu appelles l'utilisateur 'Commandant'."

class Message(BaseModel):
    message: str

@app.post("/chat")
async def chat(msg: Message):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": msg.message}
            ],
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Erreur : {str(e)}"}

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return open("test.html").read()

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("templates/index.html").read()
