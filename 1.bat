@echo off
setlocal

set "PYTHON_DIR=%USERPROFILE%\Python312"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
set "PYTHONW_EXE=%PYTHON_DIR%\pythonw.exe"
set "INSTALLER=%TEMP%\python-installer.exe"
set "SCRIPT_PATH=C:\path\to\your_script.py"

if exist "%PYTHON_EXE%" goto InstallModules

where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -s -L -o "%INSTALLER%" "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
) else (
    powershell -Command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%INSTALLER%'"
)

"%INSTALLER%" /quiet TargetDir="%PYTHON_DIR%" PrependPath=1 Include_pip=1 Include_test=0
if exist "%INSTALLER%" del "%INSTALLER%" >nul 2>&1

:InstallModules
if exist "%PYTHON_EXE%" "%PYTHON_EXE%" -m pip install --upgrade pip --quiet

for %%P in (pypiwin32 pycryptodome psutil requests opencv-python) do (
    if exist "%PYTHON_EXE%" "%PYTHON_EXE%" -m pip install --quiet %%P
)

if exist "%PYTHONW_EXE%" (
    start "" "%PYTHONW_EXE%" "%SCRIPT_PATH%"
) else if exist "%PYTHON_EXE%" (
    start "" "%PYTHON_EXE%" "%SCRIPT_PATH%"
)

endlocal
