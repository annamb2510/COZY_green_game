import os
import sys
import json
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, session,
    redirect, flash, url_for
)
from dotenv import load_dotenv
from supabase import create_client, Client

# 📦 Carica variabili da .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.debug = False
app.secret_key = 'vacanza-secret-key'

# costanti e default
PUNTEGGIO_PREMIANTE = 120
SUPPORTED_LANGS = ['it', 'en', 'fr']

#
# 1) CARICAMENTO TRADUZIONI UI (strings_xx.json)
#

def load_ui_translations():
    base = os.path.join(app.root_path, 'translations')
    out = {}
    for lang in SUPPORTED_LANGS:
        fn = os.path.join(base, f"strings_{lang}.json")
        try:
            with open(fn, encoding='utf-8') as f:
                out[lang] = json.load(f)
        except FileNotFoundError:
            out[lang] = {}
    return out

UI_TRANSLATIONS = load_ui_translations()
import sys
print("🔤 UI_TRANSLATIONS:", UI_TRANSLATIONS, file=sys.stderr)

@app.template_filter('t')
def translate_ui(text):
    lang = session.get('lang', 'it')
    translations = UI_TRANSLATIONS.get(lang, {})
    out = translations.get(text, text)

    # stampiamo per ogni chiamata:
    print(
        f"[t-filter] lang={lang} "
        f"text={text!r} → out={out!r}",
        file=sys.stderr
    )

    return out

@app.context_processor
def inject_lang_and_ui():
    return {
      'lang': session.get('lang','it'),
      # se vuoi accedere a UI_TRANSLATIONS direttamente in template
      'UI_TRANSLATIONS': UI_TRANSLATIONS
    }

#
# 2) ROUTE PER IL CAMBIO LINGUA
#
@app.route('/lang/<locale>')
def set_language(locale):
    if locale in SUPPORTED_LANGS:
        session['lang'] = locale
    # torna alla pagina chiamante (o home)
    return redirect(request.referrer or url_for('home'))


#
# 3) CARICAMENTO OBIETTIVI PER LINGUA
#
def load_goals(lang):
    fn = os.path.join(app.root_path, 'data', f'obiettivi_{lang}.json')
    if os.path.exists(fn):
        with open(fn, encoding='utf-8') as f:
            return json.load(f)
    return []


#
# --- il resto rimane invariato, eccetto l'uso di load_goals() ---
#

# funzioni cloud
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
        "ultimo_accesso": datetime.now().isoformat(),
        "obiettivi": []
    }

def salva_utente(nickname, punti, obiettivi):
    ultimo_accesso = datetime.now().isoformat()
    existing = supabase.table("giocatori")\
                       .select("nickname")\
                       .eq("nickname", nickname)\
                       .execute()
    if existing.data:
        supabase.table("giocatori")\
                .update({
                    "punti": punti,
                    "obiettivi": obiettivi,
                    "ultimo_accesso": ultimo_accesso
                }).eq("nickname", nickname).execute()
    else:
        supabase.table("giocatori")\
                .insert({
                    "nickname": nickname,
                    "punti": punti,
                    "obiettivi": obiettivi,
                    "ultimo_accesso": ultimo_accesso
                }).execute()

def carica_dati(file_path, default=None):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default if default is not None else {}

def log_debug(msg):
    timestamp = datetime.now().isoformat(timespec='seconds')
    print(f"[DEBUG] [{timestamp}] {msg}", file=sys.stderr, flush=True)
    if app.debug:
        flash(f"[DEBUG] [{timestamp}] {msg}")


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form['nickname'].strip().upper()
        if nickname.lower() == "admin":
            session['nickname'] = "ADMIN"
            return redirect('/')
        if not nickname:
            flash("Please enter a valid nickname")
            return redirect('/login')

        giocatore = carica_utente(nickname)
        config = carica_dati('data/config.json', {"riutilizzo_nickname_dopo_giorni": 30})
        giorni_limite = config.get("riutilizzo_nickname_dopo_giorni", 30)

        try:
            ultimo = datetime.fromisoformat(giocatore["ultimo_accesso"])
        except:
            ultimo = datetime.now()
        if (datetime.now() - ultimo).days > giorni_limite:
            nuovo = f"old_{nickname}_{datetime.now().date()}"
            salva_utente(nuovo, giocatore["punti"], giocatore["obiettivi"])
            flash(f"Il vecchio utente '{nickname}' è stato archiviato come '{nuovo}'.")
        else:
            session['nickname'] = nickname
            salva_utente(nickname, giocatore["punti"], giocatore["obiettivi"])
            flash("Welcome!")
            return redirect('/')

        session['nickname'] = nickname
        salva_utente(nickname, 0, [])
        return redirect('/')

    return render_template("login.html")


# Home
@app.route('/')
def home():
    if 'nickname' not in session:
        return redirect(url_for('login'))

    nickname = session['nickname']
    if nickname == "ADMIN":
        # ... admin logic (unchanged) ...
        return render_template("home.html", ...)
    else:
        giocatore = carica_utente(nickname)
        obiettivi = load_goals(session.get('lang', 'it'))
        punti = sum(o["punti"] for o in obiettivi if str(o["id"]) in giocatore["obiettivi"])
        mancanti = max(0, PUNTEGGIO_PREMIANTE - punti)
        percentuale = min(100, round(punti * 100 / PUNTEGGIO_PREMIANTE))
        return render_template("home.html",
            nickname=nickname,
            punti=punti,
            punti_mancanti=mancanti,
            percentuale=percentuale,
            punteggio_premio=PUNTEGGIO_PREMIANTE
        )


# Logout
@app.route('/logout')
def logout():
    session.pop('nickname', None)
    return redirect('/login')


# Delete user (admin only)
@app.route('/admin/delete_user/<nickname>', methods=['POST'])
def delete_user(nickname):
    if session.get("nickname") != "ADMIN":
        flash("Accesso non autorizzato")
        return redirect(url_for("home"))
    try:
        supabase.table("giocatori").delete().eq("nickname", nickname.upper()).execute()
        flash(f"Utente '{nickname}' eliminato con successo.")
    except Exception as e:
        flash(f"Errore durante l'eliminazione: {e}")
    return redirect(url_for("admin"))


# Obiettivi
@app.route('/Robiettivi', methods=['GET', 'POST'])
def Robiettivi():
    nickname = session.get('nickname')
    if not nickname:
        return redirect(url_for('login'))

    lang = session.get('lang', 'it')
    obiettivi_lista = load_goals(lang)

    giocatore = carica_utente(nickname)
    raggiunti = giocatore.get("obiettivi", [])

    if request.method == 'POST':
        sel = request.form.get('obiettivo')
        if sel and sel not in raggiunti:
            ob = next(o for o in obiettivi_lista if str(o['id']) == sel)
            giocatore['punti'] += ob['punti']
            raggiunti.append(sel)
            salva_utente(nickname, giocatore['punti'], raggiunti)
            flash(f"You gained {ob['punti']} scores for '{ob['testo']}'! ✅")
        return redirect(url_for('Robiettivi'))

    punti = sum(o['punti'] for o in obiettivi_lista if str(o['id']) in raggiunti)
    mancano = max(PUNTEGGIO_PREMIANTE - punti, 0)

    return render_template('obiettivi.html',
                           obiettivi=obiettivi_lista,
                           raggiunti=raggiunti,
                           punti=punti,
                           mancano=mancano,
                           punteggio_premio=PUNTEGGIO_PREMIANTE)


# Admin overview
@app.route('/admin')
def admin():
    if session.get('nickname') != 'ADMIN':
        return redirect('/login')
    # ... unchanged ...
    return render_template("admin.html", elenco=elenco)


# Avvio
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
