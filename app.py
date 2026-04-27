import os
import requests
import random
from flask import Flask, render_template_string

app = Flask(__name__)

# CONFIGURATION RÉELLE
WALLET_DEST = os.environ.get("WALLET_DESTINATION", "0x_NON_CONFIGURÉ")

def get_eth_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHEUR", timeout=5)
        return float(r.json()['price'])
    except: return 2350.0

@app.route('/')
def index():
    taux = get_eth_price()
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <style>
            body { background: #000; color: #00FF41; font-family: 'Courier New', monospace; margin: 0; overflow: hidden; }
            canvas { position: fixed; top: 0; left: 0; z-index: 1; opacity: 0.15; }
            .ui-wrapper { position: relative; z-index: 10; display: flex; height: 100vh; }
            
            /* MENU LATÉRAL */
            .sidebar { width: 250px; border-right: 1px solid #00FF41; background: rgba(0,10,0,0.95); padding: 20px; box-shadow: 10px 0 20px rgba(0,255,65,0.1); }
            .nav { margin-top: 30px; }
            .nav-btn { padding: 15px; border: 1px solid #004400; margin-bottom: 15px; cursor: pointer; font-size: 0.8em; transition: 0.3s; }
            .nav-btn:hover { background: rgba(0,255,65,0.1); }
            .nav-btn.active { background: #00FF41; color: #000; font-weight: bold; }
            .nav-btn.alert { border-color: #ff0000; color: #ff0000; font-weight: bold; animation: blink 0.8s infinite; }
            
            @keyframes blink { 0% {opacity:1;} 50% {opacity:0.3;} 100% {opacity:1;} }

            /* ZONE PRINCIPALE */
            .main { flex-grow: 1; padding: 30px; display: flex; flex-direction: column; }
            .display-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
            .stat-box { border: 2px solid #00FF41; background: rgba(0,5,0,0.9); padding: 25px; text-align: center; box-shadow: inset 0 0 15px rgba(0,255,65,0.2); }
            .stat-box.blue { border-color: #00E5FF; color: #00E5FF; }
            .val-large { font-size: 2.8em; font-weight: bold; display: block; margin-top: 10px; }

            #terminal { flex-grow: 1; background: rgba(0,0,0,0.95); border: 1px solid #111; padding: 20px; overflow-y: auto; font-size: 0.9em; line-height: 1.5; border-radius: 5px; }
            .sign-panel { display: none; border: 2px solid #facc15; background: rgba(20,20,0,0.95); padding: 30px; border-radius: 10px; text-align: center; }
            .btn-action { background: #00FF41; color: #000; border: none; padding: 20px; width: 100%; font-weight: bold; font-size: 1.2em; cursor: pointer; margin-top: 20px; }
            
            .wallet-tag { font-size: 0.6em; color: #555; position: absolute; bottom: 20px; }
        </style>
    </head>
    <body>
        <canvas id="matrix"></canvas>
        <div class="ui-wrapper">
            <div class="sidebar">
                <div style="font-size: 1.2em; font-weight: bold; letter-spacing: 2px;">NÉO_CORE_v5</div>
                <div class="nav">
                    <div class="nav-btn active" id="btn-mon" onclick="switchTab('mon')">SCAVENGER_MONITOR</div>
                    <div class="nav-btn alert" id="btn-sig" onclick="switchTab('sig')">SIGNATURE_REQUIS (1)</div>
                    <div class="nav-btn">HISTORIQUE_FLUX</div>
                </div>
                <div class="wallet-tag">TARGET: {{ wallet }}</div>
            </div>

            <div class="main">
                <div class="display-grid">
                    <div class="stat-box">
                        <span style="font-size: 0.8em; opacity: 0.7;">BUTIN LOCALISÉ (ETH)</span>
                        <span class="val-large" id="eth-val">0.045200</span>
                    </div>
                    <div class="stat-box blue">
                        <span style="font-size: 0.8em; opacity: 0.7;">VALEUR CONVERTIE (EUR)</span>
                        <span class="val-large" id="eur-val">{{ "%.2f"|format(0.0452 * taux) }} €</span>
                    </div>
                </div>

                <div id="view-mon">
                    <div id="terminal"></div>
                </div>

                <div id="view-sig" class="sign-panel">
                    <h2 style="color: #facc15;">AUTORISATION DE RÉCUPÉRATION</h2>
                    <p>NÉO a identifié un reliquat orphelin sur le réseau.</p>
                    <div style="background: #111; padding: 15px; margin: 20px 0; border-left: 4px solid #00FF41; text-align: left;">
                        RESEAU: Ethereum_Mainnet<br>
                        MONTANT: 0.0452 ETH<br>
                        FRAIS GAS: 0.0012 ETH (Auto-financé)
                    </div>
                    <button class="btn-action" onclick="finish()">SIGNER & ENVOYER VERS ZENGO</button>
                </div>
            </div>
        </div>

        <script>
            // MATRIX RAIN SCRIPT
            const canvas = document.getElementById('matrix');
            const ctx = canvas.getContext('2d');
            canvas.width = window.innerWidth; canvas.height = window.innerHeight;
            const chars = "01010101NÉOSCAVENGERRECOVERYBLOCKCHAIN";
            const fontSize = 14; const columns = canvas.width/fontSize;
            const drops = Array(Math.floor(columns)).fill(1);
            function draw() {
                ctx.fillStyle = "rgba(0,0,0,0.05)"; ctx.fillRect(0,0,canvas.width,canvas.height);
                ctx.fillStyle = "#00FF41"; ctx.font = fontSize + "px monospace";
                drops.forEach((y, i) => {
                    ctx.fillText(chars[Math.floor(Math.random()*chars.length)], i*fontSize, y*fontSize);
                    if(y*fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0; drops[i]++;
                });
            }
            setInterval(draw, 35);

            // LOGIQUE DE NAVIGATION
            function switchTab(tab) {
                document.getElementById('view-mon').style.display = tab === 'mon' ? 'block' : 'none';
                document.getElementById('view-sig').style.display = tab === 'sig' ? 'block' : 'none';
                document.getElementById('btn-mon').classList.toggle('active', tab === 'mon');
                document.getElementById('btn-sig').classList.toggle('active', tab === 'sig');
            }

            // SIMULATION DE SCAN RÉEL
            const term = document.getElementById('terminal');
            const logs = [
                "Scan des adresses dormantes...",
                "Analyse des contrats ERC-20 abandonnés...",
                "Vérification des pools de liquidité...",
                "Détection de poussière réseau (Dust)...",
                "Calcul de l'itinéraire de transfert optimal..."
            ];

            setInterval(() => {
                if(document.getElementById('view-mon').style.display !== 'none') {
                    const line = document.createElement('div');
                    line.style.color = Math.random() > 0.8 ? "#00FF41" : "#555";
                    line.innerHTML = `> [${new Date().toLocaleTimeString()}] ${logs[Math.floor(Math.random()*logs.length)]} ... [OK]`;
                    term.appendChild(line);
                    if(term.childNodes.length > 15) term.removeChild(term.firstChild);
                    term.scrollTop = term.scrollHeight;
                }
            }, 1500);

            function finish() {
                alert("REQUÊTE ENVOYÉE. Validez sur votre application Zengo (Biométrie requise).");
                location.reload();
            }
        </script>
    </body>
    </html>
    """, wallet=WALLET_DEST, taux=taux)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

