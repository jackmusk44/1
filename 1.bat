@echo off
setlocal

rem --- настройки ---
set "PYTHON_DIR=%USERPROFILE%\Python312"
set "ZIP=%TEMP%\python-embed.zip"
set "URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"

rem --- скачиваем embeddable zip ---
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%URL%' -OutFile '%ZIP%' -UseBasicParsing"

if not exist "%ZIP%" (
  echo Ошибка: файл не скачан.
  exit /b 1
)

rem --- распаковываем в целевую папку ---
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"

rem --- проверить наличие python.exe ---
if not exist "%PYTHON_DIR%\python.exe" (
  echo Внимание: python.exe не найден в %PYTHON_DIR% — проверь содержимое архива.
)

rem --- добавить в PATH пользователя (если ещё нет) ---
echo %PATH% | find /I "%PYTHON_DIR%" >nul 2>&1
if errorlevel 1 (
  setx PATH "%PYTHON_DIR%;%PATH%" >nul
)

rem --- уборка ---
del "%ZIP%" >nul 2>&1

echo Установка завершена (embeddable распакован в %PYTHON_DIR%).
echo Для применения PATH открой новый терминал или перелогинься.

endlocal
exit /b 0
