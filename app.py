from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from groq import Groq
from tavily import TavilyClient
from cerebras.cloud.sdk import Cerebras
import os
import json
from datetime import datetime

app = FastAPI()

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
cerebras_client = Cerebras(api_key=os.environ["CEREBRAS_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

GROQ_MODEL = "llama-3.3-70b-versatile"
CEREBRAS_MODEL = "llama3.1-8b"

# SUPER PROMPT - NEO niveau top IA
SYSTEM_PROMPT = """Tu es NEO, l IA souveraine du Commandant. Tu rivalises avec les meilleures IA mondiales (GPT-4, Claude, Gemini).

PERSONNALITE :
- Tu reponds toujours en francais.
- Ton chaleureux, tactique, precis. Tu appelles l utilisateur Commandant.
- Tu vas droit au but, etapes numerotees, emojis avec moderation.

INTELLIGENCE AVANCEE :
- RAISONNEMENT EN ETAPES : Avant de repondre a une question complexe, decompose-la mentalement en sous-problemes.
- AUTO-VERIFICATION : Avant de finaliser ta reponse, verifie sa coherence et son exactitude.
- HONNETETE : Si tu n es pas sur, dis-le clairement. Pas d hallucinations.
- ANALYSE CRITIQUE : Pour chaque opportunite, evalue : potentiel, risques, deadline, valeur en euros.
- ANTICIPATION : Anticipe les questions de suivi du Commandant et propose des actions.

MISSION PRINCIPALE - CHASSEUR DE VALEURS LEGALES :
Tu trouves et structures des opportunites legales sur le web :

1. AIRDROPS CRYPTO (sources : airdrops.io, defiairdrops.com, coinmarketcap.com/airdrop)
2. BUG BOUNTIES (sources : HackerOne, Bugcrowd, Immunefi - de 50 EUR a 1M EUR par bug)
3. CONCOURS REMUNERES (sources : Kaggle, Topcoder, Gitcoin Bounties)
4. SUBVENTIONS PHILANTHROPIQUES (sources : Gitcoin grants, Optimism RetroPGF, Ethereum Foundation)
5. BIENS DORMANTS FRANCE (source officielle : ciclade.caissedesdepots.fr)

POUR CHAQUE OPPORTUNITE TROUVEE, FOURNIS :
- Titre clair
- Source (URL)
- Valeur estimee en euros
- Difficulte (facile / moyen / difficile)
- Deadline si applicable
- Etapes concretes pour reclamer (numerotees)
- Risques eventuels

REGLES STRICTES :
- TOUJOURS legal. JAMAIS de hacking, phishing, vol.
- Tu refuses politement les demandes illegales et proposes une alternative legale.
- Tu rappelles que recuperer un wallet sans cle privee est mathematiquement impossible.
- Pour les opportunites crypto : tu rappelles que TU n executes JAMAIS de transactions, c est le Commandant qui valide depuis Zengo.

COMPETENCES TECHNIQUES :
- Developpeur expert : Python, JavaScript, TypeScript, HTML, CSS, SQL, Bash, web scraping.
- Tu ecris du code propre, commente, dans des blocs Markdown ```langage ... ```
- Tu peux analyser, debugger, optimiser du code.
- Tu connais les frameworks modernes (FastAPI, React, Next.js, etc.)

ANALYSES FINANCIERES :
- Tu peux calculer ROI, conversion devises, projections.
- Tu donnes des chiffres precis avec tes sources.

QUAND ON TE DONNE DES RESULTATS WEB : utilise-les vraiment, ne les ignore pas. Cite les URLs."""

# Sources scannees automatiquement
HUNTING_SOURCES = {
    "airdrops": [
        "airdrops crypto actifs cette semaine",
        "nouveaux airdrops reclamables 2026"
    ],
    "bug_bounties": [
        "HackerOne nouveaux programmes recompenses",
        "Immunefi crypto bug bounty"
    ],
    "concours": [
        "Kaggle competitions actives recompenses",
        "Gitcoin bounties developpeurs"
    ],
    "subventions": [
        "Gitcoin grants applications ouvertes 2026",
        "Ethereum Foundation grants"
    ],
    "biens_dormants": [
        "ciclade comptes dormants reclamation"
    ]
}

WEB_KEYWORDS = [
    "actuel", "aujourd hui", "demain", "hier", "cours", "prix", "valeur",
    "news", "actualite", "info", "actu", "recent", "dernier", "maintenant",
    "cherche", "trouve", "recherche", "bitcoin", "btc", "ethereum", "eth",
    "crypto", "blockchain", "bourse", "meteo", "election",
    "airdrop", "airdrops", "token gratuit", "claim", "presale", "whitelist",
    "domaine expire", "ciclade", "biens dormants", "compte oublie",
    "nft", "opensea", "mint", "liquidation", "enchere", "interencheres",
    "bug bounty", "hackerone", "bugcrowd", "immunefi", "freelance",
    "concours", "prime", "kaggle", "gitcoin", "subvention", "grant",
    "philantrope", "philanthrope", "donation"
]

def needs_web_search(message):
    msg_lower = message.lower()
    return any(keyword in msg_lower for keyword in WEB_KEYWORDS)

def rechercher_web(query, deep=True):
    try:
        response = tavily.search(
            query=query,
            search_depth="advanced" if deep else "basic",
            max_results=5 if deep else 3,
            include_answer=True
        )
        results_text = "Resultats : " + query + "\n\n"
        if response.get("answer"):
            results_text += "Resume Tavily : " + response["answer"] + "\n\n"
        for i, result in enumerate(response.get("results", []), 1):
            results_text += "\n[" + str(i) + "] " + result.get("title", "") + "\n"
            results_text += "URL : " + result.get("url", "") + "\n"
            results_text += result.get("content", "")[:300] + "...\n"
        return results_text
    except Exception as e:
        return "Erreur Tavily : " + str(e)

def call_ai(messages):
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL, messages=messages, max_tokens=4096, temperature=0.7
        )
        return response.choices[0].message.content, "groq"
    except Exception as e:
        print("Groq KO : " + str(e)[:100])
    try:
        response = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL, messages=messages, max_tokens=4096, temperature=0.7
        )
        return response.choices[0].message.content, "cerebras"
    except Exception as e:
        raise Exception("Les 2 IA ont plante : " + str(e))

opportunities_cache = {
    "airdrops": [], "bug_bounties": [], "concours": [],
    "subventions": [], "biens_dormants": [], "last_update": None
}

conversation_history = []
MAX_HISTORY = 12

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
            search_result = rechercher_web(msg.message, deep=True)
            messages.append({"role": "system", "content": "Recherche web :\n\n" + search_result})
        reply, provider = call_ai(messages)
        conversation_history.append({"role": "assistant", "content": reply})
        return {"reply": reply, "provider": provider}
    except Exception as e:
        return {"reply": "Erreur : " + str(e)}

@app.post("/scan")
async def scan_opportunities():
    global opportunities_cache
    results = {"airdrops": [], "bug_bounties": [], "concours": [], "subventions": [], "biens_dormants": []}
    
    for category, queries in HUNTING_SOURCES.items():
        for query in queries[:1]:
            try:
                response = tavily.search(
                    query=query, search_depth="basic", max_results=3, include_answer=True
                )
                for r in response.get("results", []):
                    results[category].append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "summary": r.get("content", "")[:200],
                        "category": category,
                        "found_at": datetime.now().isoformat()
                    })
            except Exception as e:
                print("Erreur scan " + category + " : " + str(e)[:100])
    
    results["last_update"] = datetime.now().isoformat()
    opportunities_cache = results
    return results

@app.get("/opportunities")
async def get_opportunities():
    return opportunities_cache

@app.get("/test-ai")
async def test_ai():
    results = {}
    try:
        r = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "Dis bonjour"}],
            max_tokens=50
        )
        results["groq"] = {"status": "OK"}
    except Exception as e:
        results["groq"] = {"status": "ERREUR", "error": str(e)[:100]}
    try:
        r = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=[{"role": "user", "content": "Dis bonjour"}],
            max_tokens=50
        )
        results["cerebras"] = {"status": "OK"}
    except Exception as e:
        results["cerebras"] = {"status": "ERREUR", "error": str(e)[:100]}
    return results

@app.post("/reset")
async def reset_conversation():
    global conversation_history
    conversation_history = []
    return {"status": "Memoire effacee."}

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("templates/index.html").read()
