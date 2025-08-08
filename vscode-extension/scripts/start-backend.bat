@echo off
REM Palette Backend Server Startup Script (Windows)

echo 🎨 Starting Palette Backend Server...

REM Get the directory of this script
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%\..\..

echo 📁 Project directory: %PROJECT_DIR%

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Check if we're in the right place
if not exist "src\palette" (
    echo ❌ Error: Not in Palette project directory
    echo    Expected to find src\palette directory
    pause
    exit /b 1
)

REM Check for virtual environment
if exist "venv" (
    echo 🐍 Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found, using system Python
)

REM Set PYTHONPATH
set PYTHONPATH=%PROJECT_DIR%\src

REM Start the server
echo 🚀 Starting server on http://localhost:8765...
echo 📝 Press Ctrl+C to stop the server
echo --------------------------------------------------

python -m uvicorn palette.server.main:app --host 127.0.0.1 --port 8765 --reload

pause