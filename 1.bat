@echo off
setlocal

:: Папка установки Python для текущего пользователя
set "PYTHON_DIR=%USERPROFILE%\Python312"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
set "INSTALLER=%TEMP%\python-installer.exe"

:: Проверка Python
if exist "%PYTHON_EXE%" goto InstallModules

:: Скачиваем Python через curl или PowerShell
where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -s -L -o "%INSTALLER%" "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
) else (
    powershell -Command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%INSTALLER%'"
)

:: Тихая установка для текущего пользователя без UAC
"%INSTALLER%" /quiet TargetDir="%PYTHON_DIR%" PrependPath=1 Include_pip=1 Include_test=0

:: Чистка
del "%INSTALLER%"

:InstallModules
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -m pip install --upgrade pip --quiet
    "%PYTHON_EXE%" -m pip install --quiet pypiwin32 pycryptodome psutil requests opencv-python
)

endlocal
