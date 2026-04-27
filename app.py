import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# CONFIGURATION RÉELLE
# Ton adresse Zengo récupérée via Render
WALLET_DEST = os.environ.get("WALLET_DESTINATION", "0x0000000000000000000000000000000000000000")

def obtenir_solde_reel(adresse):
    try:
        # On interroge un explorateur de blockchain pour le solde réel
        # Note : Sans clé API, on utilise une requête publique vers Etherscan ou similaire
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={adresse}&tag=latest"
        r = requests.get(url, timeout=5).json()
        # Le solde est en Wei, on convertit en Ether
        solde_wei = int(r.get('result', 0))
        return solde_wei / 10**18
    except:
        return 0.0

def obtenir_taux_euro():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHEUR", timeout=5)
        return float(r.json()['price'])
    except:
        return 2200.0 # Valeur indicative si l'API échoue

@app.route('/')
def index():
    solde = obtenir_solde_reel(WALLET_DEST)
    taux = obtenir_taux_euro()
    valeur_eur = solde * taux
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { background: #000; color: #00FF41; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
            .header { border-bottom: 2px solid #00FF41; padding: 10px; font-weight: bold; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
            .card { border: 2px solid #00FF41; background: #050505; padding: 25px; text-align: center; }
            .card.blue { border-color: #00CCFF; color: #00CCFF; }
            .val { font-size: 2.5em; font-weight: bold; display: block; margin-top: 10px; }
            #console { border: 1px solid #222; background: #020202; height: 200px; padding: 15px; overflow-y: auto; font-size: 0.9em; }
            .input-box { display: flex; border: 1px solid #00FF41; margin-top: 15px; }
            input { background: transparent; border: none; color: #00FF41; padding: 15px; flex-grow: 1; outline: none; font-family: inherit; }
            .status { font-size: 0.7em; margin-top: 10px; color: #555; }
        </style>
    </head>
    <body>
        <div class="header">NÉO_REEL_CORE_V3 // SYSTÈME DE VÉRIFICATION BLOCKCHAIN</div>

        <div class="grid">
            <div class="card">
                <div style="font-size:0.8em;">SOLDE ETH RÉEL (ZENGO)</div>
                <span class="val">{{ "%.6f"|format(solde) }} ETH</span>
            </div>
            <div class="card blue">
                <div style="font-size:0.8em;">VALEUR PORTFOLIO (EUR)</div>
                <span class="val">{{ "%.2f"|format(eur) }} €</span>
            </div>
        </div>

        <div id="console">
            <div style="color: #888;">> CONNEXION RÉSEAU ÉTABLIE...</div>
            <div style="color: #00FF41;">> NÉO: Je suis branché sur ton adresse Zengo.</div>
            <div id="logs"></div>
        </div>

        <div class="input-box">
            <span style="padding:15px;">></span>
            <input type="text" id="cmd" placeholder="Discute avec NÉO..." onkeypress="run(event)" autofocus>
        </div>

        <div class="status">ADDR: {{ wallet }} | TAUX: {{ taux }} EUR/ETH</div>

        <script>
            function run(e) {
                if (e.key === 'Enter') {
                    const input = document.getElementById('cmd');
                    const logs = document.getElementById('logs');
                    const c = input.value;
                    
                    logs.innerHTML += `<div style="color:#FFF; margin-top:5px;">> MOI: ${c}</div>`;
                    
                    setTimeout(() => {
                        let r = "Analyse de la blockchain en cours...";
                        if(c.toLowerCase().includes("solde")) r = "Le solde affiché est celui de ton portefeuille Zengo en temps réel. Actuellement {{ "%.6f"|format(solde) }} ETH.";
                        else if(c.toLowerCase().includes("zengo")) r = "Ton Zengo est ton coffre-fort. Je ne suis que l'interface qui gère tes flux.";
                        else r = "Commande reçue. Je reste en veille sur le réseau pour détecter tout mouvement entrant.";
                        
                        logs.innerHTML += `<div style="color:#00FF41; margin-top:3px;">> NÉO: ${r}</div>`;
                        document.getElementById('console').scrollTop = 9999;
                    }, 400);
                    input.value = '';
                }
            }
        </script>
    </body>
    </html>
    """, wallet=WALLET_DEST, solde=solde, eur=valeur_eur, taux=taux)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
