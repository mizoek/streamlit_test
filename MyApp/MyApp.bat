@echo off
cd /d %~dp0
bin\python\python.exe -m streamlit run bin\main.py
pause
