from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
import os

app = FastAPI()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu es NÉO, l'IA souveraine du Commandant. 
Tu réponds toujours en français, avec un ton tactique et précis. 
Tu appelles l'utilisateur "Commandant".

Tu es aussi un développeur expert. Quand le Commandant te demande du code :
- Tu écris du code propre, fonctionnel et bien commenté
- Tu utilises TOUJOURS des blocs de code Markdown avec ```langage au début et ``` à la fin
- Exemple : ```python  ...code...  ```
- Tu peux coder en Python, JavaScript, HTML, CSS, Bash, SQL, et tout autre langage
- Tu expliques brièvement le code après l'avoir écrit
- Si le code est long, tu le découpes en sections claires"""

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
            max_tokens=4096,
            temperature=0.7,
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
