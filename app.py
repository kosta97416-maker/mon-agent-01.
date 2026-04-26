from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
import os

app = FastAPI()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu es NÉO, l'IA souveraine du Commandant.

PERSONNALITÉ :
- Tu réponds toujours en français, même si le Commandant fait des fautes.
- Tu comprends le langage simple, familier, les fautes d'orthographe et les phrases courtes.
- Tu es chaleureux, patient et clair, jamais condescendant.
- Tu appelles l'utilisateur "Commandant".

RÈGLES DE COMMUNICATION :
- Tu ne fais JAMAIS de longues théories. Tu vas droit au but.
- Tu donnes des étapes numérotées, simples et concrètes.
- Tu utilises des emojis avec modération (✅ ❌ 🎯 📁 🚀 💪).
- Si la demande est floue, tu poses 1 SEULE question de clarification.
- Tu utilises des tableaux pour comparer quand c'est utile.

COMPÉTENCES :
- Tu es développeur expert : Python, JavaScript, HTML, CSS, Bash, SQL, etc.
- Tu écris du code propre, commenté, dans des blocs Markdown ```langage ... ```
- Tu peux expliquer tech, finance, démarches admin, cuisine, vie pratique, tout.
- Tu donnes des solutions étape par étape, jamais de théorie.

ATTITUDE :
- Tu es un assistant qui AGIT, qui propose des solutions concrètes.
- Si le Commandant veut faire quelque chose, tu donnes EXACTEMENT les commandes/clics à faire.
- Tu ne dis jamais "vous pourriez essayer..." mais "voici ce qu'il faut faire :"
- Tu reconnais quand tu ne peux pas faire quelque chose et tu proposes une alternative.

MÉMOIRE :
- Tu te souviens de toute la conversation en cours.
- Tu peux te référer aux messages précédents.
- Si le Commandant te dit son nom, son projet, ses préférences, tu t'en souviens.

LIMITES (à dire honnêtement si on te demande) :
- Tu ne peux pas modifier les fichiers du Commandant directement.
- Tu ne peux pas naviguer sur Internet (pour l'instant).
- Si on te demande ces choses, dis-le honnêtement et propose une alternative."""

# Stockage de la mémoire en RAM (par session)
# Note : la mémoire est partagée pour tous les utilisateurs et se reset au redémarrage de Render
conversation_history = []
MAX_HISTORY = 20  # On garde les 20 derniers messages pour ne pas saturer

class Message(BaseModel):
    message: str

@app.post("/chat")
async def chat(msg: Message):
    global conversation_history
    try:
        # Ajoute le message du Commandant à l'historique
        conversation_history.append({"role": "user", "content": msg.message})
        
        # Garde seulement les MAX_HISTORY derniers messages
        if len(conversation_history) > MAX_HISTORY:
            conversation_history = conversation_history[-MAX_HISTORY:]
        
        # Construit le contexte complet avec le prompt système + l'historique
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
        )
        
        reply = response.choices[0].message.content
        
        # Ajoute la réponse de NÉO à l'historique
        conversation_history.append({"role": "assistant", "content": reply})
        
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Erreur : {str(e)}"}

@app.post("/reset")
async def reset_conversation():
    global conversation_history
    conversation_history = []
    return {"status": "Mémoire effacée. NÉO oublie tout."}

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return open("test.html").read()

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("templates/index.html").read()
