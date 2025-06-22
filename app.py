from flask import Flask, render_template, request, session, redirect, flash, url_for
import json, os, sys
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'vacanza-secret-key'

DATA_FILE = 'giocatori.json'
CONFIG_FILE = 'config.json'
OBIETTIVI_FILE = 'obiettivi.json'
PUNTEGGIO_PREMIANTE = 120

def carica_dati(file_path, default=None):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def salva_dati(dati, file_path):
    with open(file_path, 'w') as f:
        json.dump(dati, f, indent=2)

def log_debug(msg):
    timestamp = datetime.now().isoformat(timespec='seconds')
    print(f"🟢 [COZY-DEBUG] [{timestamp}] {msg}", file=sys.stderr, flush=True)
    flash(f"[DEBUG] [{timestamp}] {msg}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form['nickname'].strip().upper()
        if not nickname:
            flash("Please enter a valid nickname")
            return redirect('/login')

        dati = carica_dati(DATA_FILE)
        config = carica_dati(CONFIG_FILE, {"riutilizzo_nickname_dopo_giorni": 30})
        giorni_limite = config.get("riutilizzo_nickname_dopo_giorni", 30)

        if nickname in dati:
            ultimo_accesso_str = dati[nickname].get("ultimo_accesso")
            try:
                ultimo_accesso = datetime.fromisoformat(ultimo_accesso_str)
            except:
                ultimo_accesso = datetime.now()
            giorni_trascorsi = (datetime.now() - ultimo_accesso).days

            if giorni_trascorsi > giorni_limite:
                nuovo_nome = f"old_{nickname}_{datetime.now().date()}"
                dati[nuovo_nome] = dati[nickname]
                del dati[nickname]
                flash(f"Il vecchio utente '{nickname}' è stato archiviato come '{nuovo_nome}'.")
            else:
                session['nickname'] = nickname
                dati[nickname]["ultimo_accesso"] = datetime.now().isoformat()
                salva_dati(dati, DATA_FILE)
                flash("Welcome!")
                return redirect('/')

        session['nickname'] = nickname
        dati[nickname] = {
            "punti": 0,
            "ultimo_accesso": datetime.now().isoformat(),
            "obiettivi": []
        }
        salva_dati(dati, DATA_FILE)
        return redirect('/')

    return render_template("login.html")

@app.route('/')
def home():
    if 'nickname' not in session:
        return redirect(url_for('login'))

    nickname = session['nickname']
    dati = carica_dati(DATA_FILE)
    giocatore = dati.get(nickname, {"punti": 0})
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

@app.route('/logout')
def logout():
    session.pop('nickname', None)
    return redirect('/login')

@app.route('/obiettivi', methods=['GET', 'POST'])
def obiettivi():
    if 'nickname' not in session:
        return redirect('/login')

    obiettivi_lista = carica_dati(OBIETTIVI_FILE)
    dati = carica_dati(DATA_FILE)
    nickname = session['nickname']

    if nickname not in dati:
        dati[nickname] = {
            "punti": 0,
            "ultimo_accesso": datetime.now().isoformat(),
            "obiettivi": []
        }

    utente = dati[nickname]
    utente.setdefault("obiettivi", [])
    raggiunti = utente["obiettivi"]
    selezionato = None

    if request.method == 'POST':
        selezionato = request.form.get('obiettivo')

        log_debug(f"Obiettivo selezionato: {selezionato}")
        log_debug(f"Obiettivi già raggiunti: {raggiunti}")

        if selezionato and selezionato not in raggiunti:
            punti = obiettivi_lista.get(selezionato, 0)
            log_debug(f"Punti assegnati: {punti}")
            log_debug(f"Punti prima: {utente['punti']}")
            utente["punti"] += punti
            utente["obiettivi"].append(selezionato)
            salva_dati(dati, DATA_FILE)
            log_debug(f"Punti dopo: {utente['punti']}")
            log_debug(f"Obiettivi aggiornati: {utente['obiettivi']}")
            flash(f"You gained {punti} scores for '{selezionato}'! ✅")
        else:
            flash("Target already marked or invalid.")

    return render_template(
        "obiettivi.html",
        obiettivi=obiettivi_lista,
        raggiunti=utente["obiettivi"],
        selezionato=selezionato
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
