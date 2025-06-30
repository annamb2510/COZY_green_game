@echo off
echo === Cozy Green Game: Deploy Avanzato ===

REM Vai nella cartella del progetto
cd /d C:\Users\annam\OneDrive\Desktop\vacanza_game

REM Chiedi all'utente il branch da usare
set /p branch="Inserisci il nome del branch (es. main o cozy-pre-pubblicazione): "
git checkout %branch%

REM Aggiungi solo i file modificati
git add -u

REM Chiedi il messaggio di commit
set /p msg="Messaggio di commit: "
git commit -m "%msg%"

REM Push sul branch scelto
git push origin %branch%

echo === Push completato sul branch %branch%! ===
pause
