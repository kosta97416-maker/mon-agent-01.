from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
import os

app = FastAPI()

# Client Groq (la clé GROQ_API_KEY vient des variables d'environnement Render)
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Modèle Groq (rapide et puissant)
MODEL = "llama-3.3-70b-versatile"

class Message(BaseModel):
    message: str

@app.post("/chat")
async def chat(msg: Message):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": msg.message}
            ],
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Erreur : {str(e)}"}

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("templates/index.html").read()
