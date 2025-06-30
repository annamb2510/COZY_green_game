@echo off
echo === Cozy Green Game: Deploy Robusto ===

cd /d C:\Users\annam\OneDrive\Desktop\vacanza_game

echo.
git status

REM Controlla se ci sono modifiche
for /f %%i in ('git status --porcelain') do (
    set found=1
    goto :modifiche
)

echo Nessuna modifica da inviare. Tutto aggiornato.
pause
exit

:modifiche
echo.
echo Modifiche rilevate. Procedo con il commit...

git add .

set /p msg="Messaggio di commit: "
git commit -m "%msg%"
git push origin main

echo.
echo === Push completato con successo! ===
pause
