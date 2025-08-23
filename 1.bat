@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Python is already installed.
) else (
    echo Python not found. Downloading and installing silently...

    :: Download Python 3.12.3 installer (amd64 for 64-bit Windows)
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"

    :: Install silently: System-wide, add to PATH, no UI
    "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0

    :: Wait for install to finish (adjust if needed)
    timeout /t 30 /nobreak >nul

    :: Clean up installer
    del "%TEMP%\python-installer.exe"
)

:: Install required modules (your script's dependencies)
python -m pip install --quiet pypiwin32 pycryptodome psutil requests opencv-python

endlocal