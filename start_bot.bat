@echo off
title JJ Playz Store Bot
cd /d "%~dp0"
echo ========================================
echo   JJ Playz Store Bot - Starting...
echo ========================================
echo.

:loop
echo [%date% %time%] Bot starting...
python bot.py
echo.
echo [%date% %time%] Bot stopped. Restarting in 5 seconds...
timeout /t 5 /nokey
goto loop
