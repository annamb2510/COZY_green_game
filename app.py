from flask import Flask, render_template, render_template_string, request, session, redirect, flash, url_for
import json, os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'vacanza-secret-key'

DATA_FILE        = 'giocatori.json'
CONFIG_FILE      = 'config.json'
OBIETTIVI_FILE   = 'obiettivi.json'
PUNTEGGIO_PREMIO = 120

def carica_giocatori():
    with open('giocatori.json', 'r') as f:
        return json.load(f)

def carica_dati():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def salva_dati(dati):
    with open(DATA_FILE, 'w') as f:
        json.dump(dati, f, indent=2)

def carica_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"riutilizzo_nickname_dopo_giorni": 30}

def carica_obiettivi():
    if os.path.exists(OBIETTIVI_FILE):
        with open(OBIETTIVI_FILE, 'r') as f:
            return json.load(f)
    return {}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form['nickname'].strip().title()
        if not nickname:
            flash("Please enter a valid nickname")
            return redirect('/login')

        dati          = carica_dati()
        config        = carica_config()
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
                salva_dati(dati)
                flash("Welcome!")
                return redirect('/')

        session['nickname'] = nickname
        dati[nickname] = {
            "punti": 0,
            "ultimo_accesso": datetime.now().isoformat(),
            "obiettivi": []
        }
        salva_dati(dati)
        return redirect('/')

    return render_template("login.html")

@app.route('/')
def home():
    if 'nickname' not in session:
        return redirect(url_for('login'))

    nickname = session['nickname']
    giocatori = carica_giocatori()
    giocatore = giocatori.get(nickname, {"punti": 0})
    punti = giocatore["punti"]
    punti_mancanti = max(0, PUNTEGGIO_PREMIO - punti)
    percentuale = min(100, int(punti * 100 / PUNTEGGIO_PREMIO))

    return render_template("home.html", nickname=nickname, punti=giocatore["punti"], punti_mancanti=punti_mancanti, percentuale=percentuale, punteggio_premio=PUNTEGGIO_PREMIO)


@app.route('/logout')
def logout():
    session.pop('nickname', None)
    return redirect('/login')

@app.route('/obiettivi', methods=['GET', 'POST'])
def obiettivi():
    if 'nickname' not in session:
        return redirect('/login')

    obiettivi_lista = carica_obiettivi()
    dati = carica_dati()
    nickname = session['nickname']

    if nickname not in dati:
        dati[nickname] = {
            "punti": 0,
            "ultimo_accesso": datetime.now().isoformat(),
            "obiettivi": []
        }
    # ✨ questa riga mancava:
    utente = dati[nickname]

    utente.setdefault("obiettivi", [])
    raggiunti = utente["obiettivi"]
    selezionato = None

    if request.method == 'POST':
        selezionato = request.form.get('obiettivo')

        if selezionato and selezionato not in raggiunti:
            punti = obiettivi_lista.get(selezionato, 0)
            utente["punti"] += punti
            utente["obiettivi"].append(selezionato)
            salva_dati(dati)
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

    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
   