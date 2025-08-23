@echo off
setlocal enabledelayedexpansion

set "PY_INSTALLER=%TEMP%\python-installer.exe"

:: Попытка скачать через полный путь к curl
"C:\Windows\System32\curl.exe" -L -o "%PY_INSTALLER%" "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
if %errorlevel% neq 0 (
    echo curl failed or not found, falling back to PowerShell...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%PY_INSTALLER%'"
)

:: Установка Python
"%PY_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0

:: Подождать немного
timeout /t 30 /nobreak >nul

:: Очистка
del "%PY_INSTALLER%"

endlocal
