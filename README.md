# 🌿 Cozy Green Game

[![Deploy on Render](https://img.shields.io/badge/Live%20on-Render-46b946?logo=render&logoColor=white)](https://cozy-green-game.onrender.com)

**Cozy Green Game** è un'app Flask pensata per incentivare comportamenti sostenibili durante il soggiorno in una struttura ricettiva.  
I giocatori guadagnano punti completando obiettivi ecologici, come spegnere le luci, differenziare i rifiuti o usare bottiglie riutilizzabili.

---

## 🚀 Funzionalità principali

- Login con nickname (anche modalità Admin)
- Sistema di punteggio basato su obiettivi ambientali
- Salvataggio dati su Supabase
- Interfaccia responsive con Bootstrap
- Visualizzazione dei progressi e premi raggiunti
- Compatibile con dispositivi mobili

---

## 🛠️ Installazione

1. Clona il repository:
   ```bash
   git clone https://github.com/annamb2510/COZY_green_game.git
   cd COZY_green_game
   
2. Crea ambiente virtuale

python -m venv venv
venv\Scripts\activate   # Su Windows

3. Installa le dipendenza
pip install -r requirements.txt


4.crea file delle dipendenze 
SUPABASE_URL=...
SUPABASE_KEY=...

5. Avvia l'app
python app.py

📁 Struttura del progetto
├── app.py
├── data/
│   ├── config.json
│   └── obiettivi.json
├── static/
│   ├── style.css
│   └── img/
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── obiettivi.html
│   └── admin.html
├── .gitignore
├── requirements.txt
└── .env  (non caricare su GitHub!)



📸 Demo online
🌐 cozy-green-game.onrender.com

