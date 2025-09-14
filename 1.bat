@echo off
setlocal

set "PYTHON_DIR=%USERPROFILE%\Python312"
set "ZIP=%TEMP%\python-embed.zip"
set "URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"

echo Downloading from %URL% to %ZIP%
powershell.exe -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%URL%' -OutFile '%ZIP%' -UseBasicParsing"

if not exist "%ZIP%" (
  echo Error: File not downloaded.
  exit /b 1
)

echo Extracting %ZIP% to %PYTHON_DIR%
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
powershell.exe -NoProfile -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"

echo Checking for python.exe in %PYTHON_DIR%
if not exist "%PYTHON_DIR%\python.exe" (
  echo Error: python.exe not found in %PYTHON_DIR%. Contents:
  dir "%PYTHON_DIR%"
  exit /b 2
)

set "found=0"
for %%a in ("%PATH:;=" "%") do (
  if /I "%%~a" == "%PYTHON_DIR%" set "found=1"
)
if "%found%" == "0" (
  echo Adding %PYTHON_DIR% to PATH
  setx PATH "%PYTHON_DIR%;%PATH%" >nul
)

echo Cleaning up %ZIP%
del "%ZIP%" >nul 2>&1

echo Installation completed in %PYTHON_DIR%. Open new terminal for PATH changes.
endlocal
exit /b 0