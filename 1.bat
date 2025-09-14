@echo off
setlocal

set "PYTHON_DIR=%USERPROFILE%\Python312"
set "ZIP=%TEMP%\python-embed.zip"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"
set "PIP_FILE=%TEMP%\get-pip.py"
set "URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"

echo Downloading Python from %URL% to %ZIP%
powershell.exe -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%URL%' -OutFile '%ZIP%' -UseBasicParsing"

if not exist "%ZIP%" (
  echo Error: Python zip not downloaded.
  exit /b 1
)

echo Extracting %ZIP% to %PYTHON_DIR%
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
powershell.exe -NoProfile -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"

echo Checking for python.exe in %PYTHON_DIR%
if not exist "%PYTHON_DIR%\python.exe" (
  echo Error: python.exe not found. Contents:
  dir "%PYTHON_DIR%"
  exit /b 2
)

echo Enabling site-packages in python312._pth
powershell.exe -NoProfile -Command "(Get-Content '%PYTHON_DIR%\python312._pth') -replace '^#import site$', 'import site' | Set-Content '%PYTHON_DIR%\python312._pth'"

echo Downloading get-pip.py to %PIP_FILE%
powershell.exe -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%PIP_URL%' -OutFile '%PIP_FILE%' -UseBasicParsing"

if not exist "%PIP_FILE%" (
  echo Error: get-pip.py not downloaded.
  exit /b 3
)

echo Installing pip...
cd /d "%PYTHON_DIR%"
"%PYTHON_DIR%\python.exe" "%PIP_FILE%"

if errorlevel 1 (
  echo Error: pip installation failed.
  exit /b 4
)

echo Adding %PYTHON_DIR% to PATH (permanent)
setx PATH "%PYTHON_DIR%;%%PATH%%" >nul 2>&1
if errorlevel 1 (
  echo Warning: setx failed (PATH too long?). Setting for current session.
  set PATH=%PYTHON_DIR%;%PATH%
)

echo Installing basic modules (requests, psutil)...
"%PYTHON_DIR%\python.exe" -m pip install --upgrade pip requests psutil >nul 2>&1

echo Cleaning up...
del "%ZIP%" >nul 2>&1
del "%PIP_FILE%" >nul 2>&1

echo Installation completed in %PYTHON_DIR%. Open new terminal for PATH changes.
endlocal
exit /b 0