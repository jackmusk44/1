@echo off
setlocal

set "PYTHON_DIR=%USERPROFILE%\Python312"
set "INSTALLER=%TEMP%\python-installer.exe"

if not exist "%PYTHON_DIR%\python.exe" (
    where curl >nul 2>&1
    if %errorlevel% equ 0 (
        curl -s -L -o "%INSTALLER%" "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
    ) else (
        powershell -Command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%INSTALLER%'"
    )

    "%INSTALLER%" /quiet InstallAllUsers=0 TargetDir="%PYTHON_DIR%" PrependPath=1 Include_pip=1 Include_test=0

    if exist "%INSTALLER%" del "%INSTALLER%" >nul 2>&1
)

endlocal
