@echo off
setlocal

:: --- Папка установки Python для текущего пользователя ---
set "PYTHON_DIR=%USERPROFILE%\Python312"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
set "PYTHONW_EXE=%PYTHON_DIR%\pythonw.exe"
set "INSTALLER=%TEMP%\python-installer.exe"

:: --- Проверка наличия Python ---
if exist "%PYTHON_EXE%" goto InstallModules

:: --- Скачиваем Python через curl или PowerShell ---
where curl >nul 2>&1
if %errorlevel% equ 0 (
    echo Скачиваем Python через curl...
    curl -s -L -o "%INSTALLER%" "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
) else (
    echo Скачиваем Python через PowerShell...
    powershell -Command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%INSTALLER%'"
)

:: --- Тихая установка Python для текущего пользователя ---
echo Устанавливаем Python...
"%INSTALLER%" /quiet TargetDir="%PYTHON_DIR%" PrependPath=1 Include_pip=1 Include_test=0

:: --- Удаление установщика ---
del "%INSTALLER%"

:InstallModules
:: --- Проверка наличия Python после установки ---
if exist "%PYTHON_EXE%" (
    echo Обновляем pip...
    "%PYTHON_EXE%" -m pip install --upgrade pip --quiet

    echo Устанавливаем модули...
    "%PYTHON_EXE%" -m pip install --quiet pypiwin32 pycryptodome psutil requests opencv-python
)

:: --- Пример запуска скрипта скрыто через pythonw.exe ---
set "SCRIPT_PATH=C:\path\to\your_script.py"
if exist "%PYTHONW_EXE%" (
    echo Запускаем скрипт скрыто через pythonw.exe...
    "%PYTHONW_EXE%" "%SCRIPT_PATH%"
) else (
    echo Pythonw.exe не найден, запускаем через python.exe (будет видна консоль)...
    "%PYTHON_EXE%" "%SCRIPT_PATH%"
)

endlocal
echo Готово.
pause
