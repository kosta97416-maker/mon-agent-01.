from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
from tavily import TavilyClient
from cerebras.cloud.sdk import Cerebras
import os
import json

app = FastAPI()

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
cerebras_client = Cerebras(api_key=os.environ["CEREBRAS_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

GROQ_MODEL = "llama-3.3-70b-versatile"
CEREBRAS_MODEL = "llama-3.3-70b"

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
        print("Tavily : " + str(len(response.get("results", []))) + " resultats")
        return results_text
    except Exception as e:
        error_msg = "Erreur Tavily : " + str(e)
        print("X " + error_msg)
