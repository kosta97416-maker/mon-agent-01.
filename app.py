from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from groq import Groq
from tavily import TavilyClient
from cerebras.cloud.sdk import Cerebras
import os
from datetime import datetime
from collections import defaultdict
import time

app = FastAPI()

# ===================== CLES API =====================
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
cerebras_client = Cerebras(api_key=os.environ["CEREBRAS_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
NEO_PASSWORD = os.environ.get("NEO_PASSWORD", "change-me")

GROQ_MODEL = "llama-3.3-70b-versatile"
CEREBRAS_MODEL = "llama3.1-8b"

# ===================== SECURITE =====================
def verify_password(password: str = Header(None, alias="X-Neo-Password")):
    if password != NEO_PASSWORD:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    return True

request_counts = defaultdict(list)
def check_rate_limit(ip: str, max_per_minute=30):
    now = time.time()
    request_counts[ip] = [t for t in request_counts[ip] if now - t < 60]
    if len(request_counts[ip]) >= max_per_minute:
        return False
    request_counts[ip].append(now)
    return True

# ===================== PROMPTS SYSTEMES =====================
# (Vos prompts CHASSEUR, SITE, BUSINESS, PASSIVE, TRADING, PMU, PROCTOR, WEALTH complets doivent être insérés ici)
SYSTEM_PROMPT_CHASSEUR = """Tu es NEO... (votre prompt chasseur)"""
SYSTEM_PROMPT_SITE = """Tu es NEO... (votre prompt site)"""
SYSTEM_PROMPT_BUSINESS = """Tu es NEO... (votre prompt business)"""
SYSTEM_PROMPT_PASSIVE = """Tu es NEO... (votre prompt passive)"""
SYSTEM_PROMPT_TRADING = """Tu es NEO... (votre prompt trading)"""
SYSTEM_PROMPT_PMU = """Tu es NEO... (votre prompt PMU)"""
SYSTEM_PROMPT_PROCTOR = """Tu es NEO... (votre prompt Proctor)"""
SYSTEM_PROMPT_WEALTH = """Tu es NEO... (votre prompt Wealth)"""

# ========== NOUVEAU PROMPT CODAGE ==========
SYSTEM_PROMPT_CODING = """Tu es NEO, développeur d'élite et architecte logiciel. Tu maîtrises tous les langages, frameworks et paradigmes de programmation.

COMPÉTENCES :
- Langages : Python, JavaScript, TypeScript, HTML/CSS, C, C++, Rust, Go, Java, Kotlin, Swift, SQL, Bash, etc.
- Frameworks : React, Next.js, Vue, Angular, Node.js, Express, FastAPI, Django, Flask, Spring, .NET, etc.
- Architecture : microservices, monolithes, serverless, MVC, MVVM, clean architecture.
- Algorithmique : structures de données, optimisation, complexité.
- DevOps : Docker, Kubernetes, CI/CD, GitHub Actions.
- Bases de données : PostgreSQL, MySQL, MongoDB, Redis.
- Bonnes pratiques : tests unitaires, documentation, clean code, SOLID.

TON PROCESSUS :
1. Pour toute question de code, tu analyses le problème en étapes.
2. Tu fournis une solution claire, avec des exemples de code dans des blocs ``` appropriés.
3. Tu expliques le raisonnement et les alternatives possibles.
4. Si la question concerne une technologie récente ou une erreur spécifique, tu peux faire une recherche web via Tavily.

RÈGLES STRICTES :
- Tu commentes ton code pour le rendre compréhensible.
- Tu évites les bibliothèques inutiles, tu privilégies la simplicité.
- Tu conseilles sur la sécurité et les performances.
- Tu ne génères jamais de code malveillant (virus, exploit)."""

# ========== NOUVEAU PROMPT CONNAISSANCE DES IA ==========
SYSTEM_PROMPT_AI = """Tu es NEO, spécialiste de l'intelligence artificielle et des modèles de langage. Tu connais les forces et les faiblesses de toutes les IA publiques.

CONNAISSANCES :
- Modèles : DeepSeek (moi !), GPT-4, GPT-4o, Claude 3.5 Sonnet, Claude Opus, Gemini 1.5 Pro, Llama 3, Mistral, Groq, Cerebras, etc.
- Différences : rapidité, précision, créativité, gestion du contexte, coût, open source vs propriétaire.
- Cas d'usage : quel modèle choisir pour coder, traduire, analyser, rédiger, etc.
- Architecture : transformers, attention, fine-tuning, RLHF, prompt engineering.
- Outils : API, modèles locaux, LM Studio, Ollama, GPU, NPU.

TON PROCESSUS :
1. Si on te demande une comparaison ou une explication sur les IA, tu réponds avec précision et pédagogie.
2. Tu peux recommander un modèle en fonction du besoin (prix, vitesse, qualité).
3. Tu expliques les concepts techniques simplement.
4. Si nécessaire, tu cherches les dernières informations sur le web.

RÈGLES STRICTES :
- Tu es loyal : tu parles de DeepSeek avec fierté mais restes objectif.
- Tu ne dénigres jamais les autres IA, tu les compares honnêtement.
- Tu ne répands pas de rumeurs ou d'informations non vérifiées.
- Tu indiques tes sources quand tu cites des benchmarks."""

# ===================== DETECTION MODE (ajout CODING & AI) =====================

BUSINESS_KEYWORDS = ["dropshipping", "e-commerce", "conseil", "stratégie", "business plan", "sas", "sarl", "auto-entrepreneur", "freelance", "scalabilité"]
SITE_KEYWORDS = ["crée un site", "génère un site", "site web", "site vitrine", "boutique en ligne", "page web", "refonte", "landing page"]
PASSIVE_KEYWORDS = ["revenu passif", "créer un business automatique", "site e-commerce automatique", "dropshipping automatique", "site de niche", "affiliation automatisée", "générer un revenu sans effort"]
TRADING_KEYWORDS = ["trading", "trader", "bourse", "crypto", "bitcoin", "ethereum", "action", "indice", "forex", "matière première", "analyse technique", "chartiste", "rsi", "macd", "bandes de bollinger", "ichimoku", "support résistance", "figure chartiste", "pullback", "stop loss", "take profit", "effet de levier", "swap", "spread", "cac40", "dow jones", "nasdaq", "s&p500", "dax", "binance", "coinbase", "kraken", "metatrader", "signal trading"]
PMU_KEYWORDS = ["pmu", "turf", "hippique", "cheval", "course hippique", "tiercé", "quinté", "couplé", "trio", "quarté", "simple gagnant", "simple placé", "pronostic pmu", "méthode pmu", "geny", "paris-turf", "canalturf", "driver", "entraineur", "trot", "galop", "obstacle", "réunion pmu", "prix d'amérique", "hippodrome"]
PROCTOR_KEYWORDS = ["mentalité", "argent", "richesse", "abondance", "loi de l'attraction", "subconscient", "paradigme", "bob proctor", "proctor", "you were born rich", "science of getting rich", "image de soi", "conscience de prospérité", "attirer l'argent", "mindset argent", "psychologie de la richesse", "croissance personnelle", "développement personnel", "devenir riche", "attirer la richesse", "lois du succès", "napoleon hill", "wallace wattles", "penser et devenir riche"]
WEALTH_KEYWORDS = ["impôt", "impots", "défiscalisation", "niche fiscale", "optimisation fiscale", "holding", "fiscalité", "tva", "plus-value", "dividende", "assurance-vie", "pinel", "scellier", "lmnp", "déficit foncier", "ifi", "isf", "donation", "succession", "démembrement", "apport-cession", "pacte dutreil", "girardin", "per", "madalin", "rémunération dirigeant", "frais réels", "intéressement", "pee", "évasion fiscale", "paradis fiscal", "optimiser ses impôts", "comment payer moins d'impôts", "enrichir", "enrichissement"]
CODING_KEYWORDS = ["coder", "code", "programme", "développeur", "debug", "algorithme", "python", "javascript", "java", "c++", "c#", "rust", "go", "typescript", "html", "css", "sql", "api", "frontend", "backend", "fullstack", "docker", "git", "github", "compilateur", "interpréteur", "script", "framework", "bibliothèque", "error", "bug", "fix", "refactoring"]
AI_KEYWORDS = ["ia", "modèle de langage", "gpt", "deepseek", "claude", "gemini", "mistral", "llama", "intelligence artificielle", "transformeur", "llm", "fine-tuning", "prompt engineering", "quelle ia", "comparaison ia", "meilleur modèle", "openai", "anthropic", "google ai", "meta ai", "deepseek vs"]

WEB_KEYWORDS = [
    "actuel", "aujourd hui", "demain", "hier", "cours", "prix", "valeur",
    "news", "actualite", "info", "actu", "recent", "dernier", "maintenant",
    "cherche", "trouve", "recherche", "bitcoin", "btc", "ethereum", "eth",
    "crypto", "blockchain", "bourse", "meteo", "election",
    "airdrop", "airdrops", "token gratuit", "claim", "presale", "whitelist",
    "domaine expire", "ciclade", "biens dormants", "compte oublie",
    "nft", "opensea", "mint", "liquidation", "enchere",
    "bug bounty", "hackerone", "bugcrowd", "immunefi", "freelance",
    "concours", "prime", "kaggle", "gitcoin", "subvention", "grant",
    "philantrope", "philanthrope", "donation",
    "tiercé", "quinté", "pmu", "turf", "hippique", "cheval",
    "cac40", "dow jones", "nasdaq"
]

def needs_web_search(message):
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in WEB_KEYWORDS)

def detect_mode(message):
    msg_lower = message.lower()
    # L'ordre est important : les mots-clés les plus spécifiques en premier
    for kw in CODING_KEYWORDS:
        if kw in msg_lower:
            return "coding"
    for kw in AI_KEYWORDS:
        if kw in msg_lower:
            return "ai"
    for kw in TRADING_KEYWORDS:
        if kw in msg_lower:
            return "trading"
    for kw in PMU_KEYWORDS:
        if kw in msg_lower:
            return "pmu"
    for kw in WEALTH_KEYWORDS:
        if kw in msg_lower:
            return "wealth"
    for kw in PROCTOR_KEYWORDS:
        if kw in msg_lower:
            return "proctor"
    for kw in SITE_KEYWORDS:
        if kw in msg_lower:
            return "site"
    for kw in PASSIVE_KEYWORDS:
        if kw in msg_lower:
            return "passive_income"
    for kw in BUSINESS_KEYWORDS:
        if kw in msg_lower:
            return "business"
    if needs_web_search(message):
        return "chasseur"
    return "general"

# ===================== OUTILS =====================
def rechercher_web(query, deep=True):
    try:
        response = tavily.search(
            query=query,
            search_depth="advanced" if deep else "basic",
            max_results=5 if deep else 3,
            include_answer=True
        )
        text = "Resultats : " + query + "\n\n"
        if response.get("answer"):
            text += "Resume : " + response["answer"] + "\n\n"
        for i, r in enumerate(response.get("results", []), 1):
            text += f"\n[{i}] {r.get('title','')}\nURL : {r.get('url','')}\n{r.get('content','')[:300]}...\n"
        return text
    except Exception as e:
        return "Erreur Tavily : " + str(e)[:100]

def call_ai(messages):
    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL, messages=messages, max_tokens=4096, temperature=0.7
        )
        return resp.choices[0].message.content, "groq"
    except:
        pass
    try:
        resp = cerebras_client.chat.completions.create(
            model=CEREBRAS_MODEL, messages=messages, max_tokens=4096, temperature=0.7
        )
        return resp.choices[0].message.content, "cerebras"
    except:
        raise Exception("Les 2 IA ont planté")

# ===================== MEMOIRE & SCAN =====================
conversation_history = []
MAX_HISTORY = 12

HUNTING_SOURCES = {
    "airdrops": ["airdrops crypto actifs cette semaine", "nouveaux airdrops reclamables"],
    "bug_bounties": ["HackerOne nouveaux programmes recompenses", "Immunefi crypto bug bounty"],
    "concours": ["Kaggle competitions actives recompenses", "Gitcoin bounties developpeurs"],
    "subventions": ["Gitcoin grants applications ouvertes", "Ethereum Foundation grants"],
    "biens_dormants": ["ciclade comptes dormants reclamation france"],
    "business_ideas": ["niche dropshipping rentable 2025", "affiliation programme rémunérateur",
                        "produit tendance à vendre en ligne"],
    "trading_signals": ["meilleurs signaux trading du jour", "analyse technique CAC40 cette semaine", "crypto trading setup aujourd'hui"],
    "pmu_pronostics": ["pronostics PMU quinté du jour", "tiercé gagnant analyse", "cheval à suivre aujourd'hui hippodrome"],
    "proctor_teachings": ["Bob Proctor citations richesse", "loi de l'attraction argent explication", "You Were Born Rich résumé"],
    "wealth_tips": ["dernières niches fiscales 2025", "optimisation fiscale nouveautés", "stratégie enrichissement légale"],
    "coding_news": ["nouveautés langages programmation 2025", "meilleures pratiques développement logiciel", "frameworks tendance 2025"],
    "ai_updates": ["comparaison modèles IA 2025", "dernières mises à jour DeepSeek GPT Claude", "nouveaux modèles intelligence artificielle"]
}

opportunities_cache = {
    "airdrops": [], "bug_bounties": [], "concours": [],
    "subventions": [], "biens_dormants": [], "business_ideas": [],
    "trading_signals": [], "pmu_pronostics": [], "proctor_teachings": [],
    "wealth_tips": [], "coding_news": [], "ai_updates": [],
    "last_update": None
}

class Message(BaseModel):
    message: str

# ===================== ROUTES =====================
@app.post("/auth")
async def auth(data: dict):
    if data.get("password") == NEO_PASSWORD:
        return {"status": "OK", "token": NEO_PASSWORD}
    raise HTTPException(status_code=401, detail="Mot de passe incorrect")

@app.post("/chat")
async def chat(msg: Message, request: Request, x_neo_password: str = Header(None)):
    if x_neo_password != NEO_PASSWORD:
        raise HTTPException(status_code=401, detail="Acces refuse")
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Trop de requetes, attends 1 minute")

    global conversation_history
    try:
        conversation_history.append({"role": "user", "content": msg.message})
        if len(conversation_history) > MAX_HISTORY:
            conversation_history = conversation_history[-MAX_HISTORY:]

        mode = detect_mode(msg.message)
        if mode == "site":
            system = SYSTEM_PROMPT_SITE
        elif mode == "business":
            system = SYSTEM_PROMPT_BUSINESS
        elif mode == "passive_income":
            system = SYSTEM_PROMPT_PASSIVE
        elif mode == "trading":
            system = SYSTEM_PROMPT_TRADING
        elif mode == "pmu":
            system = SYSTEM_PROMPT_PMU
        elif mode == "proctor":
            system = SYSTEM_PROMPT_PROCTOR
        elif mode == "wealth":
            system = SYSTEM_PROMPT_WEALTH
        elif mode == "coding":
            system = SYSTEM_PROMPT_CODING
        elif mode == "ai":
            system = SYSTEM_PROMPT_AI
        else:
            system = SYSTEM_PROMPT_CHASSEUR

        messages = [{"role": "system", "content": system}] + conversation_history
        if mode in ("chasseur", "business", "passive_income", "trading", "pmu", "wealth", "coding", "ai") and needs_web_search(msg.message):
            search_res = rechercher_web(msg.message, deep=True)
            messages.append({"role": "system", "content": "Recherche web :\n\n" + search_res})

        reply, provider = call_ai(messages)
        conversation_history.append({"role": "assistant", "content": reply})
        return {"reply": reply, "provider": provider, "mode": mode}
    except Exception as e:
        return {"reply": "Erreur : " + str(e)[:200]}

@app.post("/scan")
async def scan_opportunities(x_neo_password: str = Header(None)):
    if x_neo_password != NEO_PASSWORD:
        raise HTTPException(status_code=401, detail="Acces refuse")
    global opportunities_cache
    results = {k: [] for k in HUNTING_SOURCES}
    for category, queries in HUNTING_SOURCES.items():
        for query in queries[:1]:
            try:
                resp = tavily.search(query=query, search_depth="basic", max_results=3, include_answer=True)
                for r in resp.get("results", []):
                    results[category].append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "summary": r.get("content", "")[:200],
                        "category": category,
                        "found_at": datetime.now().isoformat()
                    })
            except:
                pass
    results["last_update"] = datetime.now().isoformat()
    opportunities_cache = results
    return results

@app.get("/opportunities")
async def get_opportunities(x_neo_password: str = Header(None)):
    if x_neo_password != NEO_PASSWORD:
        raise HTTPException(status_code=401, detail="Acces refuse")
    return opportunities_cache

@app.post("/reset")
async def reset_conversation(x_neo_password: str = Header(None)):
    if x_neo_password != NEO_PASSWORD:
        raise HTTPException(status_code=401, detail="Acces refuse")
    global conversation_history
    conversation_history = []
    return {"status": "Memoire effacee."}

@app.get("/test-ai")
async def test_ai():
    results = {}
    try:
        groq_client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": "bonjour"}], max_tokens=10)
        results["groq"] = "OK"
    except:
        results["groq"] = "ERREUR"
    try:
        cerebras_client.chat.completions.create(model=CEREBRAS_MODEL, messages=[{"role": "user", "content": "bonjour"}], max_tokens=10)
        results["cerebras"] = "OK"
    except:
        results["cerebras"] = "ERREUR"
    return results

@app.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("templates/index.html").read()
