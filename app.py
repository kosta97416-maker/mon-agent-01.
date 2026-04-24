from flask import Flask, render_template
import os

# Le template_folder='templates' est l'instruction magique
app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    # C'est cette ligne qui va chercher ton beau design
    return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
