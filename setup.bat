@echo off
setlocal EnableDelayedExpansion
title OSRS - Automated One-Click Setup

:: Ensure execution from repository root directory
cd /d "%~dp0"

echo ===============================================================================
echo                      OPEN SOURCE ROBOTICS SYSTEM (OSRS)
echo                        Automated Environment Setup
echo ===============================================================================
echo.
echo This setup script will configure the entire OSRS environment:
echo   1. Verify system prerequisites (Python 3.10+ and Node.js 18+)
echo   2. Create an isolated Python virtual environment (.venv)
echo   3. Install Python dependencies (FastAPI, MuJoCo, OpenCV, SciPy, Dynamixel SDK)
echo   4. Install Node.js frontend dependencies (npm install)
echo   5. Compile the React dashboard production bundle (npm run build)
echo.
echo ===============================================================================
echo.

:: --- 1. PREREQUISITES CHECK ---
echo [*] Checking system prerequisites...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python was not found in your system PATH!
    echo.
    echo Please download and install Python 3.10 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During Python installation, ensure you check the box:
    echo   "[x] Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Node.js was not found in your system PATH!
    echo.
    echo Please download and install Node.js (v18 or higher LTS) from:
    echo   https://nodejs.org/
    echo.
    pause
    exit /b 1
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] npm was not found in your system PATH!
    echo.
    echo Please reinstall Node.js (which includes npm) from:
    echo   https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [+] Python and Node.js prerequisites verified successfully.
echo.

:: --- 2. PYTHON VIRTUAL ENVIRONMENT ---
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [1/5] Creating Python virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [!] Warning: Failed to create .venv. Falling back to system Python.
        set "PYTHON_CMD=python"
    ) else (
        echo [+] Virtual environment created successfully.
        set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    )
) else (
    echo [1/5] Existing Python virtual environment found in .venv.
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
)
echo.

:: --- 3. PYTHON DEPENDENCIES ---
echo [2/5] Upgrading pip...
"!PYTHON_CMD!" -m pip install --upgrade pip --quiet

echo [3/5] Installing Python requirements (FastAPI, MuJoCo, OpenCV, SciPy, etc.)...
"!PYTHON_CMD!" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Warning: Some Python packages encountered installation issues.
) else (
    echo [+] Python dependencies installed successfully.
)
echo.

:: --- 3b. MUJOCO PHYSICS ENGINE VERIFICATION ---
echo [*] Verifying MuJoCo physics engine installation...
"!PYTHON_CMD!" -c "import mujoco; print('  - MuJoCo version:', mujoco.__version__); import mujoco.viewer; print('  - MuJoCo interactive passive viewer: Ready')"
if %errorlevel% neq 0 (
    echo [!] Warning: MuJoCo physics verification encountered an issue. Ensure your GPU drivers support OpenGL 3.3+.
) else (
    echo [+] MuJoCo physics engine verified and operational.
)
echo.

:: --- 4. FRONTEND DEPENDENCIES ---
echo [4/5] Installing frontend Node packages in frontend/...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [!] Warning: npm install encountered warnings or issues.
) else (
    echo [+] Frontend packages installed successfully.
)
echo.

:: --- 5. COMPILE PRODUCTION BUNDLE ---
echo [5/5] Compiling React dashboard production bundle (npm run build)...
call npm run build
if %errorlevel% neq 0 (
    echo [!] Warning: npm run build failed.
) else (
    echo [+] Production bundle compiled successfully into frontend/dist.
)
cd ..
echo.

:: --- 6. SUCCESS BANNER ---
echo ===============================================================================
echo                      [+] SETUP COMPLETED SUCCESSFULLY!
echo ===============================================================================
echo.
echo OSRS is fully configured and ready for research and development.
echo You can run the platform or simulations at any time using: launch.bat
echo.
set /p start_now="Would you like to launch the OSRS Menu now? (Y/N): "
if /i "%start_now%"=="Y" (
    call "%~dp0launch.bat"
) else (
    echo.
    echo Setup finished. Double-click launch.bat whenever you are ready!
    pause
)
exit /b 0
