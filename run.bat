@echo off
cd /d "%~dp0"
title Music Downloader (Dev)
echo.
echo  Music Downloader — PulseTube cam UI (pywebview)
echo  Kaynak kod dogrudan calisir.
echo.
python main.py
if errorlevel 1 (
  echo.
  echo  Hata: baslatilamadi.
  echo  Once:  pip install -r requirements.txt
  echo.
  pause
)
