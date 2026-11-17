@echo off
setlocal
set "project_python=%~dp0.venv\Scripts\python.exe"
if not exist "%project_python%" set "project_python=python"
"%project_python%" "%~dp0src\main.py" %*
