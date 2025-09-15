@echo off
setlocal EnableDelayedExpansion

:: Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: This script requires administrative privileges. Please run as administrator. >> "%TEMP%\python_install_log.txt"
    echo Please run this script as administrator.
    exit /b 1
)

:: Configure installation directory (change to C:\Users\Home\Python312 if needed)
set "PYTHON_DIR=C:\Users\alexs\Python312"
set "LOG_FILE=%TEMP%\python_install_log.txt"
set "INSTALLER=%TEMP%\python-3.12.3-amd64.exe"
set "URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"

:: Start logging
echo Starting Python installation at %DATE% %TIME% > "%LOG_FILE%"

:: Clean existing Python directory
if exist "%PYTHON_DIR%" (
    echo Cleaning existing Python directory: %PYTHON_DIR% >> "%LOG_FILE%"
    rmdir /s /q "%PYTHON_DIR%" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo Error: Failed to clean %PYTHON_DIR%. Check permissions. >> "%LOG_FILE%"
        type "%LOG_FILE%"
        exit /b 2
    )
)

:: Download Python installer
echo Downloading Python installer from %URL% to %INSTALLER% >> "%LOG_FILE%"
curl.exe -L -o "%INSTALLER%" "%URL%" >> "%LOG_FILE%" 2>&1
if not exist "%INSTALLER%" (
    echo Error: Python installer not downloaded. Check internet connection. >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 3
)

:: Install Python silently
echo Installing Python to %PYTHON_DIR% silently... >> "%LOG_FILE%"
start /wait "" "%INSTALLER%" /quiet InstallAllUsers=0 TargetDir="%PYTHON_DIR%" PrependPath=1 Include_pip=1 >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo Error: Python installation failed. Check %LOG_FILE% for details. >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 4
)

:: Verify pythonw.exe
if not exist "%PYTHON_DIR%\pythonw.exe" (
    echo Error: pythonw.exe not found in %PYTHON_DIR%. Contents: >> "%LOG_FILE%"
    dir "%PYTHON_DIR%" >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 5
)

:: Verify pip
echo Verifying pip installation... >> "%LOG_FILE%"
"%PYTHON_DIR%\python.exe" -m pip --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo Error: pip not installed correctly. Trying to bootstrap pip... >> "%LOG_FILE%"
    "%PYTHON_DIR%\python.exe" -m ensurepip >> "%LOG_FILE%" 2>&1
    "%PYTHON_DIR%\python.exe" -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo Error: Failed to bootstrap pip. >> "%LOG_FILE%"
        type "%LOG_FILE%"
        exit /b 6
    )
)

:: Install required modules
echo Installing modules (requests, psutil, pycryptodome, opencv-python, pywin32)... >> "%LOG_FILE%"
for %%m in (requests psutil pycryptodome opencv-python pywin32) do (
    echo Installing %%m... >> "%LOG_FILE%"
    "%PYTHON_DIR%\python.exe" -m pip install %%m --no-cache-dir >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo Error: Failed to install %%m. Check network or permissions. >> "%LOG_FILE%"
        type "%LOG_FILE%"
        exit /b 7
    )
)

:: Verify pycryptodome
echo Verifying pycryptodome installation... >> "%LOG_FILE%"
"%PYTHON_DIR%\python.exe" -c "import Cryptodome; print('pycryptodome is installed at: ' + Cryptodome.__file__)" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo Error: pycryptodome not installed correctly. Check %PYTHON_DIR%\Lib\site-packages. >> "%LOG_FILE%"
    dir "%PYTHON_DIR%\Lib\site-packages" >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 8
)

:: Update PATH for current session
echo Setting PATH for current session... >> "%LOG_FILE%"
set "PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%PATH%"

:: Clean up
echo Cleaning up... >> "%LOG_FILE%"
del "%INSTALLER%" >nul 2>&1

echo Python 3.12 installed in %PYTHON_DIR%. Check %LOG_FILE% for details.
echo To run scripts without console, use: "%PYTHON_DIR%\pythonw.exe" path_to_script.py
echo Example: "%PYTHON_DIR%\pythonw.exe" C:\Users\Home\AppData\Roaming\.minecraft\downloaded_1757957599.py
type "%LOG_FILE%"

endlocal
exit /b 0