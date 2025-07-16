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
from flask import render_template, request, redirect, url_for, flash

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip().upper()
        if not nickname:
            flash(T("Please enter a valid nickname"))
            return redirect('/login')
        session['nickname'] = nickname
        flash("Welcome!")
        return redirect('/')
    return render_template("login.html")

# home
@app.route('/')
def home():
    nickname = session.get('nickname')
    if not nickname:
        return redirect('/login')
    return render_template("home.html", nickname=nickname)

# cambio lingua
@app.route('/lang/<locale>', methods=['POST'])
def set_language(locale):
    if locale in SUPPORTED_LANGS:
        session['lang'] = locale
        session.modified = True
    next_page = request.form.get('next') or url_for('login')
    return f"""
    <!DOCTYPE html>
    <html lang="{locale}">
    <head>
      <meta charset="utf-8" />
      <title>Switching language…</title>
      <script>
        setTimeout(function() {{
          window.location.href = '{next_page}';
        }}, 100);
      </script>
    </head>
    <body>
      <p style="text-align: center; padding-top: 2rem;">
        🌍 Switching to language: <strong>{locale.upper()}</strong><br>
        Just a moment…
      </p>
    </body>
    </html>
    """

# logout
@app.route('/logout')
def logout():
    session.pop('nickname', None)
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

