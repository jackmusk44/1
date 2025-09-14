@echo off
setlocal

set "PYTHON_DIR=%USERPROFILE%\Python312"
set "ZIP=%TEMP%\python-embed.zip"
set "URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"
set "PIP_SCRIPT=%TEMP%\get-pip.py"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"

echo Downloading Python from %URL% to %ZIP%
curl.exe -L -o "%ZIP%" "%URL%"

if not exist "%ZIP%" (
  echo Error: Python zip not downloaded.
  exit /b 1
)

echo Extracting %ZIP% to %PYTHON_DIR%
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
tar -xf "%ZIP%" -C "%PYTHON_DIR%"

echo Checking for python.exe in %PYTHON_DIR%
if not exist "%PYTHON_DIR%\python.exe" (
  echo Error: python.exe not found. Contents:
  dir "%PYTHON_DIR%"
  exit /b 2
)

echo Enabling site-packages in python312._pth
echo import site>> "%PYTHON_DIR%\python312._pth"

echo Downloading get-pip.py from %PIP_URL% to %PIP_SCRIPT%
curl.exe -L -o "%PIP_SCRIPT%" "%PIP_URL%"

if not exist "%PIP_SCRIPT%" (
  echo Error: get-pip.py not downloaded.
  exit /b 3
)

echo Installing pip...
"%PYTHON_DIR%\python.exe" "%PIP_SCRIPT%" --no-warn-script-location

if errorlevel 1 (
  echo Error: pip installation failed.
  exit /b 4
)

echo Installing modules for app.py (requests, psutil, pycryptodome, opencv-python, pywin32)...
"%PYTHON_DIR%\python.exe" -m pip install requests psutil pycryptodome opencv-python pywin32 --no-cache-dir

if errorlevel 1 (
  echo Error: Failed to install some modules.
  exit /b 5
)

echo Setting PATH for current session...
set "PATH=%PYTHON_DIR%;%PATH%"

echo Cleaning up...
del "%ZIP%" >nul 2>&1
del "%PIP_SCRIPT%" >nul 2>&1

echo Portable Python installed in %PYTHON_DIR% with pip and modules.
echo Run 'python --version' and 'pip list' in a new cmd to verify.

endlocal
exit /b 0