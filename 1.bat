@echo off
setlocal

set "PYTHON_DIR=%USERPROFILE%\Python312"
set "ZIP=%TEMP%\python-embed.zip"
set "URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"
set "PIP_ZIP=%TEMP%\pip-wheel.zip"
set "PIP_URL=https://files.pythonhosted.org/packages/36/74/8767ed75cd62c6b2cee38d38f8783b7534d3c5e3b4ff2f22532ff63a53a7/pip-24.2-py3-none-any.whl"
set "SETUPTOOLS_URL=https://files.pythonhosted.org/packages/27/b8/6d6e0b4e6b2aaac5b3c4f3c6bc1c5b4f7b9a420dd6eb7b25b74f8b3a1c06/setuptools-74.1.2-py3-none-any.whl"
set "WHEEL_URL=https://files.pythonhosted.org/packages/1b/d1/2b56fd7c5745f5f3e0754b0060a88603e7a672c5f7f4f4f6f8d2957a38f4/wheel-0.44.0-py3-none-any.whl"
set "PYWIN32_URL=https://files.pythonhosted.org/packages/a4/2a/8a614851b0e83655bc4a8e6af5a19f3fd72e7474b4b8a31e645ad98cc340/pywin32-306-cp312-cp312-win_amd64.whl"

echo Downloading Python from %URL% to %ZIP%
curl.exe -L -o "%ZIP%" "%URL%"

if not exist "%ZIP%" (
  echo Error: Python zip not downloaded.
  exit /b 1
)

echo Extracting %ZIP% to %PYTHON_DIR%
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
tar -xf "%ZIP%" -C "%PYTHON_DIR%"

echo Checking for python.exe in %PYTHON_DIR%
if not exist "%PYTHON_DIR%\python.exe" (
  echo Error: python.exe not found. Contents:
  dir "%PYTHON_DIR%"
  exit /b 2
)

echo Enabling site-packages in python312._pth
echo import site>> "%PYTHON_DIR%\python312._pth"

echo Downloading pip, setuptools, and wheel...
curl.exe -L -o "%PIP_ZIP%" "%PIP_URL%"
curl.exe -L -o "%TEMP%\setuptools.whl" "%SETUPTOOLS_URL%"
curl.exe -L -o "%TEMP%\wheel.whl" "%WHEEL_URL%"
curl.exe -L -o "%TEMP%\pywin32.whl" "%PYWIN32_URL%"

echo Extracting pip to %PYTHON_DIR%\Lib\site-packages
if not exist "%PYTHON_DIR%\Lib\site-packages" mkdir "%PYTHON_DIR%\Lib\site-packages"
cd /d "%PYTHON_DIR%\Lib\site-packages"
tar -xf "%PIP_ZIP%"

echo Copying setuptools and wheel to site-packages
copy "%TEMP%\setuptools.whl" "%PYTHON_DIR%\Lib\site-packages" >nul
copy "%TEMP%\wheel.whl" "%PYTHON_DIR%\Lib\site-packages" >nul
copy "%TEMP%\pywin32.whl" "%PYTHON_DIR%\Lib\site-packages" >nul

echo Installing pip, setuptools, wheel, and pywin32...
"%PYTHON_DIR%\python.exe" -m pip install "%PYTHON_DIR%\Lib\site-packages\pip-24.2-py3-none-any.whl" --no-index --find-links "%PYTHON_DIR%\Lib\site-packages"
"%PYTHON_DIR%\python.exe" -m pip install "%PYTHON_DIR%\Lib\site-packages\setuptools-74.1.2-py3-none-any.whl" --no-index --find-links "%PYTHON_DIR%\Lib\site-packages"
"%PYTHON_DIR%\python.exe" -m pip install "%PYTHON_DIR%\Lib\site-packages\wheel-0.44.0-py3-none-any.whl" --no-index --find-links "%PYTHON_DIR%\Lib\site-packages"
"%PYTHON_DIR%\python.exe" -m pip install "%PYTHON_DIR%\Lib\site-packages\pywin32-306-cp312-cp312-win_amd64.whl" --no-index --find-links "%PYTHON_DIR%\Lib\site-packages"

echo Installing basic modules (requests, psutil, pycryptodome, opencv-python)...
"%PYTHON_DIR%\python.exe" -m pip install requests psutil pycryptodome opencv-python --no-cache-dir

echo Adding %PYTHON_DIR% to PATH (permanent)
setx PATH "%PYTHON_DIR%;%%PATH%%" >nul 2>&1
if errorlevel 1 (
  echo Warning: setx failed (PATH too long?). Setting for current session.
  set PATH=%PYTHON_DIR%;%PATH%
)

echo Cleaning up...
del "%ZIP%" >nul 2>&1
del "%TEMP%\pip-wheel.zip" >nul 2>&1
del "%TEMP%\setuptools.whl" >nul 2>&1
del "%TEMP%\wheel.whl" >nul 2>&1
del "%TEMP%\pywin32.whl" >nul 2>&1

echo Portable Python installed in %PYTHON_DIR% with pip and modules.
echo Run 'python --version' and 'pip list' in a new terminal to verify.

endlocal
exit /b 0