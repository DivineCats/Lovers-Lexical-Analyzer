@echo off
cd /d "%~dp0"
start "Backend" cmd /k python -m Backend.Lexical.main
start "Frontend" cmd /k "cd Frontend && npm run dev"
