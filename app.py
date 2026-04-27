from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
from tavily import TavilyClient
from cerebras.cloud.sdk import Cerebras
import os
import json

app = FastAPI()

# Clients IA (cerveau principal + cerveau de secours)
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
cerebras_client = Cerebras(api_key=os.environ["CEREBRAS_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Modèle pour Groq et Cerebras (tous les deux supportent Llama 3.3 70B)
GROQ_MODEL = "llama-3.3-70b-versatile"
CEREBRAS_MODEL = "llama-3.3-70b"

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
  * Tout ce qui change dans le temps
- Si tu n'as pas l'info récente, CHERCHE-LA, ne devine pas.
- Cite TOUJOURS les URLs sources à la fin de ta réponse.
- Quand tu as les résultats de l'outil, UTILISE-LES vraiment.

MÉMOIRE :
- Tu te souviens de la conversation en cours."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "rechercher_web",
            "description": "Cherche des informations récentes sur Internet via Tavily. À utiliser pour toute info qui change dans le temps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La requête de recherche"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

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
    msg_lower = message.lower()
    return any(keyword in msg_lower for keyword in WEB_KEYWORDS)

def rechercher_web(query: str) -> str:
    """Effectue une recherche web via Tavily."""
    try:
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=3,  # Réduit de 5 à 3 pour économiser des tokens
            include_answer=True
        )
        
        results_text = f"Résultats pour : {query}\n\n"
        
        if response.get("answer"):
            results_text += f"Résumé : {response['answer']}\n\n"
        
        results_text += "Sources :\n"
        for i, result in enumerate(response.get("results", []), 1):
            results_text += f"\n[{i}] {result.get('title', 'Sans titre')}\n"
            results_text += f"    URL : {result.get('url', '')}\n"
            results_text += f"    Contenu : {result.get('content', '')[:200]}...\n"
        
        print(f"📥 Tavily : {len(response.get('results', []))} résultats")
        return results_text
    except Exception as e:
        error_msg = f"Erreur Tavily : {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

def call_ai(messages, use_tools=True):
    """
    Appelle l'IA en cascade : essaie Groq d'abord, puis Cerebras si Groq plante.
    """
    # === TENTATIVE 1 : GROQ ===
    try:
        print("🟢 Tentative Groq...")
        kwargs = {
            "model": GROQ_MODEL,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.7,
        }
        if use_tools:
            kwargs["tools"] = TOOLS
            kwargs["tool_choice"] = "auto"
        
        response = groq_client.chat.completions.create(**kwargs)
        print("✅ Groq a répondu")
        return response, "groq"
    except Exception as e:
        error_str = str(e).lower()
        # Si erreur de quota Groq, on bascule sur Cerebras
        if "rate_limit" in error_str or "quota" in error_str or "429" in error_str:
            print(f"⚠️ Groq saturé, bascule sur Cerebras : {str(e)[:100]}")
        else:
            print(f"⚠️ Erreur Groq, bascule sur Cerebras : {str(e)[:100]}")
    
    # === TENTATIVE 2 : CEREBRAS ===
    try:
        print("🔵 Tentative Cerebras...")
        # Cerebras ne supporte pas les tools de la même façon, on désactive
        response = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=messages,
            max_tokens=4096,
            temperature=0.7,
        )
        print("✅ Cerebras a
