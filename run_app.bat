@echo off
cd /d %~dp0

:: 8501番ポートが使用中かを確認
netstat -ano | findstr :8501 | findstr LISTENING > nul

if %errorlevel% equ 0 (
  echo --------------------------------------------------
  echo レシート帳簿アプリは既に起動しているようです。
  echo ブラウザのタブを確認してください。
  echo --------------------------------------------------
  pause
  exit
)

:: 起動処理
echo アプリの起動中…
streamlit run app_ver3.py --server.port 8501

pause
