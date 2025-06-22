from flask import Flask, render_template, request, session, redirect, flash, url_for
from datetime import datetime
import json, os, sys

from dotenv import load_dotenv
from supabase import create_client, Client

# 📦 Carica variabili da .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = 'vacanza-secret-key'

CONFIG_FILE = 'config.json'
OBIETTIVI_FILE = 'obiettivi.json'
PUNTEGGIO_PREMIANTE = 120

# 🧠 Funzioni cloud
def carica_utente(nickname):
    result = supabase.table("giocatori").select("*").eq("nickname", nickname).execute()
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
    existing = supabase.table("giocatori").select("nickname").eq("nickname", nickname).execute()

    if existing.data:
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

# 🔧 Supporto
def carica_dati(file_path, default=None):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def log_debug(msg):
    timestamp = datetime.now().isoformat(timespec='seconds')
    print(f"[DEBUG] [{timestamp}] {msg}", file=sys.stderr, flush=True)
    flash(f"[DEBUG] [{timestamp}] {msg}")

# 🟠 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form['nickname'].strip().upper()
        if not nickname:
            flash("Please enter a valid nickname")
            return redirect('/login')

        giocatore = carica_utente(nickname)
        config = carica_dati(CONFIG_FILE, {"riutilizzo_nickname_dopo_giorni": 30})
        giorni_limite = config.get("riutilizzo_nickname_dopo_giorni", 30)

        try:
            ultimo_accesso = datetime.fromisoformat(giocatore["ultimo_accesso"])
        except:
            ultimo_accesso = datetime.now()

        giorni_trascorsi = (datetime.now() - ultimo_accesso).days

        if giorni_trascorsi > giorni_limite:
            nuovo_nome = f"old_{nickname}_{datetime.now().date()}"
            salva_utente(nuovo_nome, giocatore["punti"], giocatore["obiettivi"])
            flash(f"Il vecchio utente '{nickname}' è stato archiviato come '{nuovo_nome}'.")
        else:
            session['nickname'] = nickname
            salva_utente(nickname, giocatore["punti"], giocatore["obiettivi"])
            flash("Welcome!")
            return redirect('/')

        session['nickname'] = nickname
        salva_utente(nickname, 0, [])
        return redirect('/')

    return render_template("login.html")

# 🏠 Home
@app.route('/')
def home():
    if 'nickname' not in session:
        return redirect(url_for('login'))

    nickname = session['nickname']
    giocatore = carica_utente(nickname)
    punti = giocatore["punti"]
    punti_mancanti = max(0, PUNTEGGIO_PREMIANTE - punti)
    percentuale = min(100, int(punti * 100 / PUNTEGGIO_PREMIANTE))

    return render_template("home.html",
        nickname=nickname,
        punti=punti,
        punti_mancanti=punti_mancanti,
        percentuale=percentuale,
        punteggio_premio=PUNTEGGIO_PREMIANTE
    )

# 🚪 Logout
@app.route('/logout')
def logout():
    session.pop('nickname', None)
    return redirect('/login')

# 🎯 Obiettivi
@app.route('/obiettivi', methods=['GET', 'POST'])
def obiettivi():
    if 'nickname' not in session:
        return redirect('/login')

    obiettivi_lista = carica_dati(OBIETTIVI_FILE)
    nickname = session['nickname']
    giocatore = carica_utente(nickname)
    giocatore.setdefault("obiettivi", [])
    raggiunti = gioc