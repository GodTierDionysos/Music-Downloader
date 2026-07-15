@echo off
cd /d "%~dp0"
title Music Downloader — EXE Derleme
echo.
echo  Bu islem birkac dakika surebilir.
echo  Gelistirme icin run.bat kullanin; exe sadece dagitim icin gerekir.
echo.
python build.py
echo.
pause
