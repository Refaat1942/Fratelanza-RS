@echo off
setlocal
cd /d "%~dp0\.."

if not exist .venv (
    py -3 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
if errorlevel 1 goto failed
pip install -e ".[exe]"
if errorlevel 1 goto failed
pyinstaller --clean --noconfirm build\windows\fratelanza_admin.spec
if errorlevel 1 goto failed

echo.
echo Admin EXE created at:
echo dist\FratelanzaAdminConsole\FratelanzaAdminConsole.exe
echo.
echo Edit dist\FratelanzaAdminConsole\.env with your VPS admin URL and admin key.
exit /b 0

:failed
echo.
echo Build failed. Please send the error lines above.
exit /b 1
