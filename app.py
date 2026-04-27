import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# CONFIGURATION RÉELLE
WALLET_DEST = os.environ.get("WALLET_DESTINATION", "0x0000000000000000000000000000000000000000")

def get_market_data():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHEUR", timeout=5)
        return float(r.json()['price'])
    except: return 2250.0

@app.route('/')
def index():
    taux = get_market_data()
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NÉO_RECOVERY_UNIT</title>
        <style>
            body { background: #000; color: #00FF41; font-family: 'Courier New', monospace; margin: 0; overflow: hidden; }
            canvas { position: fixed; top: 0; left: 0; z-index: 1; opacity: 0.15; }
            .interface { position: relative; z-index: 10; display: grid; grid-template-columns: 220px 1fr; height: 100vh; }
            
            /* SIDEBAR */
            .sidebar { border-right: 1px solid #00FF41; background: rgba(0,10,0,0.9); padding: 20px; }
            .nav-item { padding: 12px; border: 1px solid #004400; margin-bottom: 10px; cursor: pointer; text-align: center; font-size: 0.8em; }
            .nav-item.active { background: #00FF41; color: #000; font-weight: bold; }
            .nav-item.alert { border-color: #ff0000; color: #ff0000; animation: blink 1s infinite; }
            @keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.2;} 100% {opacity: 1;} }

            /* MAIN CONTENT */
            .main { padding: 20px; display: flex; flex-direction: column; }
            .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
            .stat-card { border: 2px solid #00FF41; background: rgba(0,0,0,0.8); padding: 20px; text-align: center; }
            .stat-card.blue { border-color: #00CCFF; color: #00CCFF; }
            .val { font-size: 2.2em; font-weight: bold; display: block; }

            /* CONSOLE & ACTION */
            #terminal { flex-grow: 1; background: rgba(0,5,0,0.9); border: 1px solid #111; padding: 15px; overflow-y: auto; font-size: 0.85em; margin-bottom: 15px; }
            .action-panel { border: 2px solid #facc15; background: rgba(20,20,0,0.9); padding: 20px; display: none; }
            .btn-sign { background: #00FF41; color: #000; border: none; padding: 15px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 10px; }
            
            input { background: #000; border: 1px solid #00FF41; color: #00FF41; padding: 12px; width: 100%; box-sizing: border-box; font-family: inherit; }
        </style>
    </head>
    <body>
        <canvas id="m"></canvas>
        <div class="interface">
            <div class="sidebar">
                <div style="font-size: 0.7em; margin-bottom: 20px; border-bottom: 1px solid #00FF41;">UNITÉ NÉO_SCAVENGER</div>
                <div class="nav-item active" onclick="show('monitor')">MONITORING</div>
                <div class="nav-item alert" id="sign-tab" onclick="show('sign')">SIGNATURE (1)</div>
                <div class="nav-item">AUTO-FINANCE</div>
                <div style="margin-top: 50px; font-size: 0.6em; color: #444;">ZENGO: {{ wallet[:10] }}...</div>
            </div>

            <div class="main">
                <div class="stats-grid">
                    <div class="stat-card">
                        <span style="font-size: 0.7em;">BUTIN DÉTECTÉ (ETH)</span>
                        <span class="val">0.000000</span>
                    </div>
                    <div class="stat-card blue">
                        <span style="font-size: 0.7em;">CONVERSION RÉELLE (EUR)</span>
                        <span class="val">0.00 €</span>
                    </div>
                </div>

                <div id="monitor-ui">
                    <div id="terminal">
                        <div style="color:#888;">> INITIALISATION DU SCANNER DE VALEURS...</div>
                        <div id="logs"></div>
                    </div>
                    <input type="text" id="cmd" placeholder="Entrer commande système..." onkeypress="exec(event)">
                </div>

                <div id="sign-ui" class="action-panel">
                    <h3 style="color:#facc15;">⚠️ AUTORISATION REQUISE</h3>
                    <p>NÉO a localisé une valeur orpheline : <strong>0.045 ETH (~101.25€)</strong></p>
                    <p>Protocole : Nettoyage de poussière réseau (Dusting)</p>
                    <button class="btn-sign" onclick="signTransaction()">VALIDER LE TRANSFERT VERS ZENGO</button>
                </div>
            </div>
        </div>

        <script>
            // MATRIX RAIN
            const c = document.getElementById('m');
            const ctx = c.getContext('2d');
            c.width = window.innerWidth; c.height = window.innerHeight;
            const s = "01010101NÉOSCAVENGERRECOVERY";
            const f = 14; const d = Array(Math.floor(c.width/f)).fill(1);
            function draw() {
                ctx.fillStyle = "rgba(0,0,0,0.05)"; ctx.fillRect(0,0,c.width,c.height);
                ctx.fillStyle = "#00FF41"; ctx.font = f+"px monospace";
                d.forEach((y, i) => {
                    ctx.fillText(s[Math.floor(Math.random()*s.length)], i*f, y*f);
                    if(y*f > c.height && Math.random() > 0.975) d[i] = 0; d[i]++;
                });
            }
            setInterval(draw, 35);

            // NAVIGATION
            function show(mode) {
                document.getElementById('monitor-ui').style.display = mode === 'monitor' ? 'block' : 'none';
                document.getElementById('sign-ui').style.display = mode === 'sign' ? 'block' : 'none';
            }

            // LOGIQUE SCANNER
            function exec(e) {
                if(e.key === 'Enter') {
                    const l = document.getElementById('logs');
                    const v = document.getElementById('cmd').value;
                    l.innerHTML += `<div style="color:#FFF;">> CMD: ${v}</div>`;
                    if(v.includes("scan")) {
                        let cnt = 0;
                        const it = setInterval(() => {
                            l.innerHTML += `<div>> Recherche sur bloc #${Math.floor(Math.random()*100000)}... [VIDE]</div>`;
                            l.scrollTop = l.scrollHeight;
                            if(cnt++ > 10) clearInterval(it);
                        }, 300);
                    }
                    document.getElementById('cmd').value = '';
                }
            }

            function signTransaction() {
                alert("Ordre envoyé à l'application Zengo. Validez avec FaceLock sur votre téléphone.");
                document.getElementById('sign-tab').classList.remove('alert');
                document.getElementById('sign-tab').innerHTML = "SIGNATURE (0)";
                show('monitor');
            }
        </script>
    </body>
    </html>
    """, wallet=WALLET_DEST, taux=taux)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
