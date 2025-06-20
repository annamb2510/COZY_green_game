from flask import Flask, render_template_string, request, session, redirect, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'vacanza-secret-key'

DATA_FILE = 'giocatori.json'

def carica_dati():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def salva_dati(dati):
    with open(DATA_FILE, 'w') as f:
        json.dump(dati, f, indent=2)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form['nickname'].strip()
        if nickname:
            session['nickname'] = nickname
            dati = carica_dati()
            if nickname not in dati:
                dati[nickname] = {
                    "punti": 0,
                    "ultimo_accesso": datetime.now().isoformat(),
                    "obiettivi": []
                }
            else:
                dati[nickname]["ultimo_accesso"] = datetime.now().isoformat()
            salva_dati(dati)
            return redirect('/')
        else:
            flash("Inserisci un nickname valido.")
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            <label>Nickname:</label><br>
            <input type="text" name="nickname" required><br><br>
            <input type="submit" value="Entra">
        </form>
    ''')

@app.route('/')
def home():
    if 'nickname' in session:
        dati = carica_dati()
        nickname = session['nickname']
        punti = dati.get(nickname, {}).get("punti", 0)
        return render_template_string(f'''
            <h2>Ciao {nickname}!</h2>
            <p>Hai totalizzato <strong>{punti}</strong> punti 🎯</p>
            <p><a href="/obiettivi">Vai agli obiettivi</a></p>
            <form action="/logout" method="get">
                <button type="submit">Esci</button>
            </form>
        ''')
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('nickname', None)
    return redirect('/login')

@app.route('/obiettivi', methods=['GET', 'POST'])
def obiettivi():
    if 'nickname' not in session:
        return redirect('/login')

    obiettivi_lista = {
        'colazione': 5,
        'camminata': 10,
        'acquagym': 15,
        'foto_tramonto': 8
    }

    dati = carica_dati()
    nickname = session['nickname']

    if nickname not in dati:
        dati[nickname] = {
            "punti": 0,
            "ultimo_accesso": datetime.now().isoformat(),
            "obiettivi": []
        }
        salva_dati(dati)

    utente = dati[nickname]
    raggiunti = utente.get("obiettivi", [])

    if request.method == 'POST':
        selezionato = request.form.get('obiettivo')
        if selezionato and selezionato not in raggiunti:
            punti = obiettivi_lista.get(selezionato, 0)
            utente["punti"] += punti
            utente["obiettivi"].append(selezionato)
            salva_dati(dati)
            flash(f"Hai guadagnato {punti} punti per '{selezionato}'! ✅")
        else:
            flash("Obiettivo già segnato o non valido.")
        return redirect('/obiettivi')

    return render_template_string('''
        <h2>Obiettivi raggiunti</h2>
        <form method="post">
            {% for nome, punti in obiettivi.items() %}
                <label>
                    <input type="radio" name="obiettivo" value="{{ nome }}"
                        {% if nome in raggiunti %}disabled{% endif %}>
                    {{ nome }} (+{{ punti }} punti)
                    {% if nome in raggiunti %} ✅{% endif %}
                </label><br>
            {% endfor %}
            <br>
            <button type="submit">Segna obiettivo</button>
        </form>
        <br>
        <a href="/">Torna alla home</a>
    ''', obiettivi=obiettivi_lista, raggiunti=raggiunti)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)