@echo off
setlocal
cd /d "%~dp0\.."

if not exist .venv (
    py -3 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[exe]"
pyinstaller --clean --noconfirm build\windows\fratelanza_admin.spec

echo.
echo Admin EXE created at:
echo dist\FratelanzaAdminConsole\FratelanzaAdminConsole.exe
echo.
echo Edit dist\FratelanzaAdminConsole\.env with your VPS admin URL and admin key.
