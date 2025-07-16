import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from flask import (
    Flask, session, render_template,
    request, redirect, url_for, flash
)
from dotenv import load_dotenv
from supabase import create_client, Client

# 🔧 Init Supabase
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🧠 Init Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'vacanza-secret-key')

# 🌍 Carica traduzioni UI
SUPPORTED_LANGS = ['it', 'en', 'fr']
UI_TRANSLATIONS = {}
translations_dir = Path(__file__).parent / 'translations'

print("DEBUG: ✅ Flask app inizializzata correttamente", file=sys.stderr)

for file in translations_dir.glob('strings_*.json'):
    lang = file.stem.split('_')[1]
    try:
        UI_TRANSLATIONS[lang] = json.loads(file.read_text(encoding='utf-8'))
    except Exception as e:
        app.logger.error(f"Errore caricando {file.name}: {e}")
        UI_TRANSLATIONS[lang] = {}

# 🔣 Helper traduzioni
app.jinja_env.globals['T'] = lambda text: \
    UI_TRANSLATIONS.get(session.get('lang', 'it'), {}).get(text, text)

# 💬 Inietta lingua e traduzioni nei template
@app.context_processor
def inject_lang():
    return {
        'lang': session.get('lang', 'it'),
        'UI_TRANSLATIONS': UI_TRANSLATIONS
    }

# 🛠 Rotta debug per tutte le route
@app.route("/_debug/routes")
def debug_routes():
    return "<br>".join(str(r) for r in app.url_map.iter_rules())

# 📁 Carica obiettivi localizzati
def load_goals(lang):
    fn = Path(__file__).parent / 'data' / f'obiettivi_{lang}.json'
    if fn.exists():
        return json.loads(fn.read_text(encoding='utf-8'))
    return []

# 🧑‍💻 Carica utente da Supabase
def carica_utente(nickname):
    result = supabase.table("giocatori").select("*").eq("nickname", nickname).execute()
    if result.data:
        return result.data[0]
    return {"nickname": nickname, "punti": 0, "obiettivi": [], "ultimo_accesso": datetime.now().isoformat()}

# 💾 Salva utente su Supabase
def salva_utente(nickname, punti, obiettivi):
    ultimo_accesso = datetime.now().isoformat()
    exists = supabase.table("giocatori").select("nickname").eq("nickname", nickname).execute()
    if exists.data:
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

# 🔐 Login
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

# 🏠 Home e dashboard
@app.route('/')
def home():
    nickname = session.get('nickname')
    if not nickname:
        return redirect('/login')

    if nickname == "ADMIN":
        utenti_res = supabase.table("giocatori").select("nickname").execute()
        totale_utenti = len(utenti_res.data)

        punti_res = supabase.table("giocatori").select("punti").execute()
        punti_list = [r["punti"] for r in punti_res.data if "punti" in r]
        media_punti = round(sum(punti_list) / len(punti_list), 2) if punti_list else 0

        sette_giorni_fa = (datetime.now() - timedelta(days=7)).isoformat()
        recenti = supabase.table("giocatori").select("nickname", "ultimo_accesso")\
                          .gte("ultimo_accesso", sette_giorni_fa).execute()
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

# 🌐 Cambio lingua
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

# 🔓 Logout
@app.route('/logout')
def logout():
    session.pop('nickname', None)
    return redirect('/login')

# 🎯 Obiettivi
@app.route('/Robiettivi', methods=['GET', 'POST'])
def Robiettivi():
    nickname = session.get('nickname')
    if not nickname:
        return redirect('/login')
    giocatore = carica_utente(nickname)
    obiettivi = load_goals(session.get('lang', 'it'))

    raggiunti = set(giocatore.get("obiettivi", []))
    if request.method == 'POST':
        oid = request.form.get("obiettivo")
        if oid and oid not in raggiunti:
            raggiunti.add(oid)
            punti = sum(o["punti"] for o in obiettivi if str(o["id"]) in raggiunti)
            salva_utente(nickname, punti, list(raggiunti))
            flash(T("Goal marked as completed"))

    punti = sum(o["punti"] for o in obiettivi if str(o["id"]) in raggiunti)
    punteggio_premio = 120
    mancano = max(0, punteggio_premio - punti)

    return render_template("obiettivi.html",
        obiettivi=obiettivi,
        punti=punti,
        punteggio_premio=punteggio_premio,
        mancano=mancano,
        raggiunti=raggiunti
    )

# 🚀 Avvio app locale
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
