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
pyinstaller --clean --noconfirm build\windows\fratelanza_customer.spec
if errorlevel 1 goto failed

echo.
echo Customer EXE created at:
echo dist\FratelanzaBusinessSuite\FratelanzaBusinessSuite.exe
echo.
echo Edit dist\FratelanzaBusinessSuite\.env for each customer before delivery.
exit /b 0

:failed
echo.
echo Build failed. Please send the error lines above.
exit /b 1
