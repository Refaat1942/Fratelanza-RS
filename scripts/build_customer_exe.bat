@echo off
setlocal
cd /d "%~dp0\.."

if not exist .venv (
    py -3 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[exe]"
pyinstaller --clean --noconfirm build\windows\fratelanza_customer.spec

echo.
echo Customer EXE created at:
echo dist\FratelanzaBusinessSuite\FratelanzaBusinessSuite.exe
echo.
echo Edit dist\FratelanzaBusinessSuite\.env for each customer before delivery.
