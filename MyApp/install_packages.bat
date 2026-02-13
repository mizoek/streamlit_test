@echo off
rem Embedded Python のパス
set PYTHON_DIR=%~dp0bin\Python

echo Installing pip...
"%PYTHON_DIR%\python.exe" "%~dp0get-pip.py"

echo Removing get-pip.py...
del "%~dp0get-pip.py"

echo Adding Scripts to PATH temporarily
set PATH=%PYTHON_DIR%\Scripts;%PATH%

echo Done.
pause
