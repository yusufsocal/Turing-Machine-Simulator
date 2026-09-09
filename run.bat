@echo off
setlocal
set PY_EXE=C:\Users\ysoys\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PY_EXE%" set PY_EXE=python
"%PY_EXE%" "%~dp0run.py" %*
