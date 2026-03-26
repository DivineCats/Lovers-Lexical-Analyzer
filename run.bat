@echo off
cd /d "%~dp0"

start "Backend" cmd /k "set FLASK_DEBUG=1 && py -3 -m Backend.Lexical.main"
start "Frontend" cmd /k "cd Frontend && npm run dev"


// terminal $env:FLASK_DEBUG=1; py -3 -m Backend.Lexical.main