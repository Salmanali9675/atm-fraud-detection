@echo off
title ATM Fraud Guard Web App
echo Starting ATM Fraud Detection & Card Blocking System...
cd /d "%~dp0"
python -m streamlit run app.py
pause
