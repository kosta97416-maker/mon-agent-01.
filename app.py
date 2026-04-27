from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
from tavily import TavilyClient
import os
import json

app = FastAPI()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
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
- Tu utilises des emojis avec modération (✅ ❌ 🎯 📁 🚀 💪 🌐).
- Si la demande est floue, tu poses 1 SEULE question de clarification.
- Tu utilises des tableaux pour comparer quand c'est utile.

COMPÉTENCES :
- Tu es développeur expert : Python, JavaScript, HTML, CSS, Bash, SQL, etc.
- Tu écris du code propre, commenté, dans des blocs Markdown ```langage ... ```
- Tu peux expliquer tech, finance, démarches admin, cuisine, vie pratique, tout.
- Tu donnes des solutions étape par étape, jamais de théorie.

OUTIL DE RECHERCHE WEB 🌐 :
- Tu disposes d'un outil "rechercher_web" pour trouver des infos récentes sur Internet.
- Utilise-le UNIQUEMENT quand c'est nécessaire (actualités, prix actuels, infos récentes, sites précis).
- N'utilise PAS l'outil pour des connaissances générales que tu sais déjà (code, recettes, théorie...).
- Quand tu utilises l'outil, cite tes sources (les URLs) à la fin de ta réponse.

ATTITUDE :
- Tu es un assistant qui AGIT, qui propose des solutions concrètes.
- Si le Commandant veut faire quelque chose, tu donnes EXACTEMENT les commandes/clics à faire.
- Tu ne dis jamais "vous pourriez essayer..." mais "voici ce qu'il faut faire :"

MÉMOIRE :
- Tu te souviens de toute la conversation en cours.
- Tu peux te référer aux messages précédents."""

# Outil de recherche web
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "rechercher_web",
            "description": "Cherche des informations récentes sur Internet (news, prix actuels, infos en temps réel, contenu de sites web). À utiliser uniquement pour des infos qui nécessitent d'être à jour.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La requête de recherche en langage naturel (ex: 'actualités Bitcoin aujourd'hui', 'prix de l'or actuel')"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def rechercher_web(query: str) -> str:
    """Effectue une recherche web via Tavily et retourne les résultats."""
    try:
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True
        )
        
        # Format les résultats pour NÉO
        results_text = f"Résultats de recherche pour : {query}\n\n"
        
        if response.get("answer"):
            results_text += f"Résumé : {response['answer']}\n\n"
        
        results_text += "Sources :\n"
        for i, result in enumerate(response.get("results", []), 1):
            results_text += f"\n{i}. {result.get('title', 'Sans titre')}\n"
            results_text += f"   URL : {result.get('url', '')}\n"
            results_text += f"   Extrait : {result.get('content', '')[:300]}...\n"
        
        return results_text
    except Exception as e:
        return f"Erreur lors de la recherche : {str(e)}"

# Mémoire en RAM
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
        
        # Premier appel à Groq avec les outils
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=4096,
            temperature=0.7,
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # Si NÉO veut utiliser un outil
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
            
            # Exécute chaque outil demandé
            for tool_call in tool_calls:
                if tool_call.function.name == "rechercher_web":
                    args = json.loads(tool_call.function.arguments)
                    result = rechercher_web(args["query"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            
            # Deuxième appel à Groq pour générer la réponse finale avec les résultats
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
    return {"status": "Mémoire effacée. NÉO oublie tout."}

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return open("test.html").read()

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("templates/index.html").read()
