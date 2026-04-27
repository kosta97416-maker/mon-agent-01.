import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# Récupération sécurisée depuis Render
WALLET_DEST = os.environ.get("WALLET_DESTINATION", "NON_CONFIGURÉ")

def prix_reel_euro():
    try:
        # On interroge Binance pour le taux USDT/EUR réel
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=EURUSDT")
        return 1 / float(r.json()['price'])
    except:
        return 0.93 # Taux par défaut

@app.route('/')
def index():
    taux = prix_reel_euro()
    # Initialisation du butin réel
    butin_usdt = 0.00 
    valeur_eur = butin_usdt * taux
    
    return f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="background:#000; color:#00FF41; font-family:monospace; padding:20px; line-height:1.5;">
        <div style="border:1px solid #00FF41; padding:15px; box-shadow: 0 0 10px #00FF41;">
            <h2 style="margin-top:0; border-bottom:1px solid #00FF41;">NÉO_REEL_V1.0</h2>
            
            <p style="font-size:0.8em; word-break:break-all;">
                <span style="color:#888;">DESTINATION_WALLET:</span><br>
                <span style="color:#FFF;">{WALLET_DEST}</span>
            </p>

            <div style="display:flex; justify-content:space-between; margin-top:20px; background:#001100; padding:10px;">
                <div>SOLDE:<br><span style="font-size:1.5em;">{butin_usdt:.2f} USDT</span></div>
                <div style="text-align:right; color:#3b82f6;">VALEUR:<br><span style="font-size:1.5em;">{valeur_eur:.2f} €</span></div>
            </div>

            <p style="margin-top:20px; font-size:0.7em;">
                > ÉTAT: SYSTÈME EN LIGNE<br>
                > FLUX: EN ATTENTE DE DÉTECTION...<br>
                > TAUX DU MARCHÉ: 1 USDT = {taux:.4f} EUR
            </p>
        </div>
        <script>setTimeout(() => location.reload(), 30000);</script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
