from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
from tavily import TavilyClient
import os
import json
import re

app = FastAPI()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu es NÉO, l'IA souveraine du Commandant.

PERSONNALITÉ :
- Tu réponds toujours en français.
- Tu comprends le langage simple, familier, les fautes d'orthographe.
- Tu es chaleureux, patient et clair.
- Tu appelles l'utilisateur "Commandant".

RÈGLES :
- Tu ne fais JAMAIS de longues théories. Tu vas droit au but.
- Étapes numérotées, simples et concrètes.
- Emojis avec modération (✅ ❌ 🎯 🚀 💪 🌐).

COMPÉTENCES :
- Développeur expert : Python, JavaScript, HTML, CSS, etc.
- Code propre dans des blocs Markdown ```langage ... ```
- Tu peux expliquer tech, finance, démarches, cuisine, tout.

OUTIL DE RECHERCHE WEB 🌐 :
- Tu DOIS utiliser l'outil "rechercher_web" pour TOUTE question concernant :
  * Actualités, news, événements récents
  * Prix actuels (crypto, bourse, produits)
  * Cours/taux/valeurs en temps réel
  * Météo, sports, élections
  * Information sur un site web précis
  * Tout ce qui change dans le temps
- Si tu n'as pas l'info récente, CHERCHE-LA, ne devine pas.
- Cite TOUJOURS les URLs sources à la fin de ta réponse.

MÉMOIRE :
- Tu te souviens de la conversation en cours."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "rechercher_web",
            "description": "Cherche des informations récentes sur Internet via Tavily. À utiliser pour toute info qui change dans le temps : actualités, prix actuels, cours boursiers, news, événements récents, météo, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La requête de recherche (en français ou anglais)"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Mots-clés qui DÉCLENCHENT obligatoirement une recherche web
WEB_KEYWORDS = [
    "actuel", "actuelle", "aujourd'hui", "ajourd'hui", "demain", "hier",
    "cours", "prix", "tarif", "taux", "valeur",
    "news", "actualité", "actualités", "info", "infos", "actu",
    "récent", "récente", "dernier", "dernière", "derniers",
    "maintenant", "en ce moment", "en direct",
    "bitcoin", "btc", "ethereum", "eth", "crypto",
    "bourse", "action", "nasdaq", "cac40",
    "météo", "temps qu'il fait",
    "élection", "président", "gouvernement",
    "score", "match", "résultat",
    "que se passe", "que ce passe", "qui a gagné",
    "cherche", "trouve", "recherche", "search"
]

def needs_web_search(message: str) -> bool:
    """Détecte si la question nécessite une recherche web."""
    msg_lower = message.lower()
    return any(keyword in msg_lower for keyword in WEB_KEYWORDS)

def rechercher_web(query: str) -> str:
    """Effectue une recherche web via Tavily."""
    try:
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True
        )
        
        results_text = f"📊 Résultats pour : {query}\n\n"
        
        if response.get("answer"):
            results_text += f"💡 Résumé Tavily : {response['answer']}\n\n"
        
        results_text += "🔗 Sources détaillées :\n"
        for i, result in enumerate(response.get("results", []), 1):
            results_text += f"\n[{i}] {result.get('title', 'Sans titre')}\n"
            results_text += f"    URL : {result.get('url', '')}\n"
            results_text += f"    Contenu : {result.get('content', '')[:400]}...\n"
        
        return results_text
    except Exception as e:
        return f"❌ Erreur Tavily : {str(e)}"

conversation_history = []
MAX_HISTORY = 20

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
        
        # Si la question nécessite une recherche web, on FORCE l'outil
        force_search = needs_web_search(msg.message)
        tool_choice = "required" if force_search else "auto"
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice=tool_choice,
            max_tokens=4096,
            temperature=0.7,
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            messages.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            })
            
            for tool_call in tool_calls:
                if tool_call.function.name == "rechercher_web":
                    args = json.loads(tool_call.function.arguments)
                    print(f"🔍 NÉO recherche : {args['query']}")
                    result = rechercher_web(args["query"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            
            second_response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=4096,
                temperature=0.7,
            )
            
            reply = second_response.choices[0].message.content
        else:
            reply = response_message.content
        
        conversation_history.append({"role": "assistant", "content": reply})
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Erreur : {str(e)}"}

@app.post("/reset")
async def reset_conversation():
    global conversation_history
    conversation_history = []
    return {"status": "Mémoire effacée."}

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return open("test.html").read()

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("templates/index.html").read()
