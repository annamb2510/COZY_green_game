@echo off
echo === Cozy Green Game: Deploy Script ===

REM Vai nella cartella del progetto
cd /d C:\Users\annam\OneDrive\Desktop\vacanza_game

REM Attiva l'ambiente virtuale (se serve)
REM call venv\Scripts\activate

REM Aggiunge tutti i file modificati
git add .

REM Chiede un messaggio di commit all'utente
set /p msg="Inserisci messaggio di commit: "
git commit -m "%msg%"

REM Fa il push sul branch main
git push origin main

echo === Deploy completato! ===
pause
