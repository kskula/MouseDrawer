@echo off
REM PyInstaller build for screen_drawer_window.py

cd /d "%~dp0"

REM Clean previous build
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Build with PyInstaller (hidden console)
python -m PyInstaller --noconfirm ^
    --name=ScreenDrawerWindow ^
    --windowed=False ^
    --console=True ^
    --onefile ^
    --add-data "tests;tests" ^
    screen_drawer_window.py

echo Build complete! Check dist\ScreenDrawerWindow.exe
pause
