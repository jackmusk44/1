@echo off
setlocal

set "PYTHON_DIR=%USERPROFILE%\Python312"
set "INSTALLER=%TEMP%\python-installer.exe"

if not exist "%PYTHON_DIR%\python.exe" (
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%INSTALLER%'"

    if exist "%INSTALLER%" (
        "%INSTALLER%" /quiet InstallAllUsers=0 TargetDir="%PYTHON_DIR%" PrependPath=1 Include_pip=1 Include_test=0
        del "%INSTALLER%" >nul 2>&1
    ) else (
        echo Failed to download installer.
    )
)

endlocal