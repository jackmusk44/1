@echo off
setlocal enabledelayedexpansion

:: Проверяем, установлен ли Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Python уже установлен.
) else (
    echo Python не найден. Скачиваем и устанавливаем...

    :: Скачиваем Python 3.12.3 (64-bit)
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '$env:TEMP\python-installer.exe'"

    :: Создаем PowerShell скрипт для установки через Планировщик задач
    set psScript=%TEMP%\python_install_task.ps1
    (
        echo $installerPath = "$env:TEMP\python-installer.exe"
        echo $taskName = "PythonInstallElevated"
        echo if (-not (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) {
        echo     $action = New-ScheduledTaskAction -Execute $installerPath -Argument "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0"
        echo     $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
        echo     $task = New-ScheduledTask -Action $action -Principal $principal
        echo     Register-ScheduledTask -TaskName $taskName -InputObject $task
        echo }
        echo Start-ScheduledTask -TaskName $taskName
        echo Start-Sleep -Seconds 30
        echo Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    ) > "%psScript%"

    :: Запуск скрипта
    powershell -ExecutionPolicy Bypass -File "%psScript%"

    :: Удаляем временные файлы
    del "%psScript%"
    del "%TEMP%\python-installer.exe"
)

:: Устанавливаем зависимости
python -m pip install --quiet pypiwin32 pycryptodome psutil requests opencv-python

endlocal
