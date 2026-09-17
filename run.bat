@echo off
setlocal

where py >nul 2>nul
if not errorlevel 1 (
    py "%~dp0run.py" %*
    goto :eof
)

python --version >nul 2>nul
if not errorlevel 1 (
    python "%~dp0run.py" %*
    goto :eof
)

if exist "C:\Users\ysoys\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\ysoys\AppData\Local\Programs\Python\Python312\python.exe" "%~dp0run.py" %*
    goto :eof
)

echo Could not find a working Python. Install it from https://python.org, or make sure "py" or "python" is on PATH.
exit /b 1
