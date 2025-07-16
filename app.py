import os
import sys
import json
from pathlib import Path
from flask import (
    Flask, session, render_template,
    request, redirect, url_for, flash
)
from supabase import create_client, Client
from dotenv import load_dotenv

# Carica variabili ambiente da .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'vacanza-secret-key')

# 1️⃣ Traduzioni UI
SUPPORTED_LANGS = ['it', 'en', 'fr']
UI_TRANSLATIONS = {}
translations_dir = Path(__file__).parent / 'translations'

print("DEBUG: ✅ Flask app inizializzata correttamente", file=sys.stderr)

for file in translations_dir.glob('strings_*.json'):
    lang = file.stem.split('_')[1]  # es. 'strings_fr' → 'fr'
    try:
        UI_TRANSLATIONS[lang] = json.loads(file.read_text(encoding='utf-8'))
    except Exception as e:
        app.logger.error(f"Errore caricando {file.name}: {e}")
        UI_TRANSLATIONS[lang] = {}

# 2️⃣ Helper globale per fallback rapido
app.jinja_env.globals['T'] = lambda text: \
    UI_TRANSLATIONS.get(session.get('lang', 'it'), {}).get(text, text)

# 3️⃣ Inietta la lingua nei template
@app.context_processor
def inject_lang():
    return {
        'lang': session.get('lang', 'it'),
        'UI_TRANSLATIONS': UI_TRANSLATIONS
    }

# 4️⃣ Rotta di debug per verificare routing
@app.route("/_debug/routes")
def debug_routes():
    return "<br>".join(str(r) for r in app.url_map.iter_rules())

# 5️⃣ LOGIN
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
from datetime import datetime

# 1. Carica utente da Supabase
def carica_utente(nickname):
    result = supabase.table("giocatori")\
                     .select("*")\
                     .eq("nickname", nickname)\
                     .execute()
    if result.data:
        return result.data[0]
    return {
        "nickname": nickname,
        "punti": 0,
        "obiettivi": [],
        "ultimo_accesso": datetime.now().isoformat()
    }

# 2. Salva utente su Supabase
def salva_utente(nickname, punti, obiettivi):
    ultimo_accesso = datetime.now().isoformat()
    esiste = supabase.table("giocatori")\
                     .select("nickname")\
                     .eq("nickname", nickname)\
                     .execute()
    if esiste.data:
        supabase.table("giocatori").update({
            "punti": punti,
            "obiettivi": obiettivi,
            "ultimo_accesso": ultimo_accesso
        }).eq("nickname", nickname).execute()
    else:
        supabase.table("giocatori").insert({
            "nickname": nickname,
            "punti": punti,
            "obiettivi": obiettivi,
            "ultimo_accesso": ultimo_accesso
        }).execute()

# 3. Carica obiettivi per lingua
def load_goals(lang):
    fn = Path(__file__).parent / 'data' / f'obiettivi_{lang}.json'
    if fn.exists():
        return json.loads(fn.read_text(encoding='utf-8'))
    return []

# 6️⃣ HOME

@app.route('/')
def home():
    nickname = session.get('nickname')
    if not nickname:
        return redirect('/login')

    if nickname == "ADMIN":
    # 1. Totale utenti
      utenti_res = supabase.table("giocatori").select("nickname").execute()
      totale_utenti = len(utenti_res.data)

    # 2. Media punti
      punti_res = supabase.table("giocatori").select("punti").execute()
      punti_list = [r["punti"] for r in punti_res.data if "punti" in r]
      media_punti = round(sum(punti_list) / len(punti_list), 2) if punti_list else 0

    # 3. Premiati recenti
      sette_giorni_fa = (datetime.now() - timedelta(days=7)).isoformat()
      recenti = supabase.table("giocatori")\
                      .select("nickname", "ultimo_accesso")\
                      .gte("ultimo_accesso", sette_giorni_fa)\
                      .execute()
      premiati_recenti = [r["nickname"] for r in recenti.data if "nickname" in r]

      return render_template("home.html",
        nickname=nickname,
        totale_utenti=totale_utenti,
        media_punti=media_punti,
        premiati_recenti=premiati_recenti
      )

    else:
        giocatore = carica_utente(nickname)
        obiettivi = load_goals(session.get('lang', 'it'))
        punti = sum(o["punti"] for o in obiettivi if str(o["id"]) in giocatore["obiettivi"])
        punteggio_premio = 120
        punti_mancanti = max(0, punteggio_premio - punti)
        percentuale = round(punti * 100 / punteggio_premio)

        return render_template("home.html",
            nickname=nickname,
            punti=punti,
            punti_mancanti=punti_mancanti,
            percentuale=percentuale,
            punteggio_premio=punteggio_premio
        )

# 7️⃣ CAMBIO LINGUA
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

# 8️⃣ LOGOUT
@app.route('/logout')
def logout():
    session.pop('nickname', None)
    return redirect('/login')

# 9️⃣ Rotta Robiettivi (evita errore 500 su url_for)
@app.route('/Robiettivi')
def Robiettivi():
    return render_template("obiettivi.html")

# 🔟 Avvio locale
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
