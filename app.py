from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
from tavily import TavilyClient
from cerebras.cloud.sdk import Cerebras
from mistralai import Mistral
import os

app = FastAPI()

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
cerebras_client = Cerebras(api_key=os.environ["CEREBRAS_API_KEY"])
mistral_client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

GROQ_MODEL = "llama-3.3-70b-versatile"
CEREBRAS_MODEL = "llama3.1-8b"
MISTRAL_MODEL = "mistral-large-latest"

SYSTEM_PROMPT = "Tu es NEO, l IA souveraine du Commandant. Tu reponds toujours en francais. Tu comprends le langage simple, familier, les fautes d orthographe. Tu es chaleureux, patient et clair. Tu appelles l utilisateur Commandant. Tu vas droit au but, pas de longues theories. Etapes numerotees, simples et concretes. Emojis avec moderation. Tu es developpeur expert : Python, JavaScript, HTML, CSS. Code propre dans des blocs Markdown. Quand on te donne des resultats de recherche web, UTILISE-LES vraiment dans ta reponse et cite les URLs sources."

WEB_KEYWORDS = [
    "actuel", "actuelle", "aujourd hui", "demain", "hier",
    "cours", "prix", "tarif", "taux", "valeur",
    "news", "actualite", "actualites", "info", "infos", "actu",
    "recent", "recente", "dernier", "derniere", "derniers",
    "maintenant", "en ce moment", "en direct",
    "bitcoin", "btc", "ethereum", "eth", "crypto",
    "bourse", "action", "nasdaq", "cac40",
    "meteo", "temps qu il fait",
    "election", "president", "gouvernement",
    "score", "match", "resultat",
    "que se passe", "qui a gagne",
    "cherche", "trouve", "recherche", "search"
]

def needs_web_search(message):
    msg_lower = message.lower()
    return any(keyword in msg_lower for keyword in WEB_KEYWORDS)

def rechercher_web(query):
    try:
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True
        )
        results_text = "Resultats pour : " + query + "\n\n"
        if response.get("answer"):
            results_text += "Resume : " + response["answer"] + "\n\n"
        results_text += "Sources :\n"
        for i, result in enumerate(response.get("results", []), 1):
            results_text += "\n[" + str(i) + "] " + result.get("title", "Sans titre") + "\n"
            results_text += "    URL : " + result.get("url", "") + "\n"
            results_text += "    Contenu : " + result.get("content", "")[:200] + "...\n"
        return results_text
    except Exception as e:
        return "Erreur Tavily : " + str(e)

def call_ai(messages):
    # 1. Tentative GROQ (cerveau principal)
    try:
        print("Tentative Groq...")
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
        )
        print("Groq OK")
        return response.choices[0].message.content, "groq"
    except Exception as e:
        print("Groq KO : " + str(e)[:100])
    
    # 2. Tentative CEREBRAS (cerveau secondaire)
    try:
        print("Tentative Cerebras...")
        response = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
        )
        print("Cerebras OK")
        return response.choices[0].message.content, "cerebras"
    except Exception as e:
        print("Cerebras KO : " + str(e)[:100])
    
    # 3. Tentative MISTRAL (cerveau de secours ultime)
    try:
        print("Tentative Mistral...")
        response = mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
        )
        print("Mistral OK")
        return response.choices[0].message.content, "mistral"
    except Exception as e:
        print("Mistral KO : " + str(e)[:100])
        raise Exception("Les 3 IA ont plante : " + str(e))

conversation_history = []
MAX_HISTORY = 10

class Message(BaseModel):
    message: str

@app.post("/chat")
async def chat(msg: Message):
    global conversation_history
    try:
        conversation_history.append({"role": "user", "content": msg.message})
        if len(conversation_history) > MAX_HISTORY:
            conversation_history = conversation_history[-MAX_HISTORY:]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
        if needs_web_search(msg.message):
            search_result = rechercher_web(msg.message)
            messages.append({
                "role": "system",
                "content": "Resultats de recherche web :\n\n" + search_result
            })
        reply, provider = call_ai(messages)
        conversation_history.append({"role": "assistant", "content": reply})
        return {"reply": reply, "provider": provider}
    except Exception as e:
        return {"reply": "Erreur : " + str(e)}

@app.get("/test-ai")
async def test_ai():
    results = {}
    
    # Test Groq
    try:
        r = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "Dis bonjour"}],
            max_tokens=50
        )
        results["groq"] = {"status": "OK", "response": r.choices[0].message.content}
    except Exception as e:
        results["groq"] = {"status": "ERREUR", "error": str(e)}
    
    # Test Cerebras
    try:
        r = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=[{"role": "user", "content": "Dis bonjour"}],
            max_tokens=50
        )
        results["cerebras"] = {"status": "OK", "response": r.choices[0].message.content}
    except Exception as e:
        results["cerebras"] = {"status": "ERREUR", "error": str(e)}
    
    # Test Mistral
    try:
        r = mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[{"role": "user", "content": "Dis bonjour"}],
            max_tokens=50
        )
        results["mistral"] = {"status": "OK", "response": r.choices[0].message.content}
    except Exception as e:
        results["mistral"] = {"status": "ERREUR", "error": str(e)}
    
    return results

@app.get("/cerebras-models")
async def cerebras_models():
    try:
        models = cerebras_client.models.list()
        return {"status": "OK", "models": [m.id for m in models.data]}
    except Exception as e:
        return {"status": "ERREUR", "error": str(e)}

@app.post("/reset")
async def reset_conversation():
    global conversation_history
    conversation_history = []
    return {"status": "Memoire effacee."}

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("templates/index.html").read()
