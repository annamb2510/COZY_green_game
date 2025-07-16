import os
import json
from pathlib import Path
from flask import Flask, session

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'vacanza-secret-key')

# 1) Carica traduzioni UI da translations/strings_xx.json
SUPPORTED_LANGS = ['it', 'en', 'fr']
UI_TRANSLATIONS = {}
translations_dir = Path(__file__).parent / 'translations'

print("DEBUG: ✅ Flask app inizializzata correttamente", file=sys.stderr)

for file in translations_dir.glob('strings_*.json'):
    lang = file.stem.split('_')[1]  # 'strings_fr' → 'fr'
    try:
        UI_TRANSLATIONS[lang] = json.loads(file.read_text(encoding='utf-8'))
    except Exception as e:
        app.logger.error(f"Errore caricando {file.name}: {e}")
        UI_TRANSLATIONS[lang] = {}

# 2) Registra helper globale T(text)
app.jinja_env.globals['T'] = lambda text: \
    UI_TRANSLATIONS.get(session.get('lang', 'it'), {}).get(text, text)

# 3) Inietta solo la lingua corrente (lang) nei template
@app.context_processor
def inject_lang():
    return {'lang': session.get('lang', 'it')}

@app.route("/_debug/routes")
def debug_routes():
    return "<br>".join(str(r) for r in app.url_map.iter_rules())

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

