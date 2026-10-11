@echo off
setlocal EnableDelayedExpansion
title OSRS - Open Source Robotics System Launcher

:: Ensure we are in the repository root directory
cd /d "%~dp0"

:: Auto-detect Python virtual environment created by setup.bat
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    set "ENV_STATUS=[Environment: .venv]"
) else (
    set "PYTHON_CMD=python"
    set "ENV_STATUS=[Environment: System Python]"
)

:menu
cls
echo ===============================================================================
echo                      OPEN SOURCE ROBOTICS SYSTEM (OSRS)
echo                          Unified Launcher Menu
echo                          !ENV_STATUS!
echo ===============================================================================
echo.
echo   [ WEB PLATFORM AND DASHBOARD ]
echo     1. Launch OSRS Server (FastAPI Backend + Web Dashboard at localhost:8000)
echo     2. Launch Frontend Dev Server (Vite Hot-Reload at localhost:5173)
echo.
echo   [ SIMULATIONS (MuJoCo Physics) ]
echo     3. Stage 1: Dual OpenManipulator-X Cooperative Plate Balancing
echo     4. Stage 1: OMX PID Controller Benchmark
echo     5. Stage 1: OMX Multi-Camera Calibration and Triangulation (solvePnP)
echo     6. Stage 1: Standalone Single-Arm OpenManipulator-X Model Viewer
echo     7. Stage 2: Asymmetric Two-Arm (Franka FR3 + HEAL) Ball Manipulation
echo     8. Stage 3: Humanoid Bimanual Plate Balancing (OP3 Torso)
echo     9. Stage 3: Humanoid Steering Wheel Simulation
echo.
echo   [ BUILD AND UTILITIES ]
echo    10. Rebuild Frontend Production Bundle (npm run build)
echo    11. Install or Update Python and Node Dependencies
echo    12. Run Full Environment Setup (setup.bat)
echo.
echo     0. Exit
echo ===============================================================================
set /p choice="Enter your choice (0-12): "

:: Remove any trailing or leading whitespace
if defined choice set "choice=%choice: =%"

if "%choice%"=="1" goto launch_main
if "%choice%"=="2" goto launch_frontend_dev
if "%choice%"=="3" goto launch_omx_cooperative
if "%choice%"=="4" goto launch_omx_pid
if "%choice%"=="5" goto launch_omx_cameras
if "%choice%"=="6" goto launch_omx_single
if "%choice%"=="7" goto launch_two_arm
if "%choice%"=="8" goto launch_humanoid_plate
if "%choice%"=="9" goto launch_humanoid_steering
if "%choice%"=="10" goto build_frontend
if "%choice%"=="11" goto install_deps
if "%choice%"=="12" goto run_setup
if "%choice%"=="0" goto exit_launcher

echo.
echo [!] Invalid selection "%choice%". Please enter a valid number.
ping -n 3 127.0.0.1 >nul
goto menu

:launch_main
cls
echo ===============================================================================
echo [>] Starting OSRS FastAPI Production Server...
echo [>] Dashboard will be available at: http://localhost:8000
echo ===============================================================================
echo.
"!PYTHON_CMD!" main.py
echo.
pause
goto menu

:launch_frontend_dev
cls
echo ===============================================================================
echo [>] Starting Vite Frontend Development Server...
echo [>] Dev Dashboard will be available at: http://localhost:5173
echo ===============================================================================
echo.
cd frontend
call npm run dev
cd ..
echo.
pause
goto menu

:launch_omx_cooperative
cls
echo ===============================================================================
echo [>] Launching Stage 1: Dual OpenManipulator-X Cooperative Plate Balancing...
echo ===============================================================================
echo.
cd omx_ball_manipulation
"!PYTHON_CMD!" simulate_cooperative.py
cd ..
echo.
pause
goto menu

:launch_omx_pid
cls
echo ===============================================================================
echo [>] Launching Stage 1: OMX PID Benchmark...
echo ===============================================================================
echo.
cd omx_ball_manipulation
"!PYTHON_CMD!" PID.py
cd ..
echo.
pause
goto menu

:launch_omx_cameras
cls
echo ===============================================================================
echo [>] Launching Stage 1: OMX Multi-Camera Calibration and Triangulation...
echo ===============================================================================
echo.
cd omx_ball_manipulation
"!PYTHON_CMD!" verify_cameras.py
cd ..
echo.
pause
goto menu

:launch_omx_single
cls
echo ===============================================================================
echo [>] Launching Stage 1: Standalone OpenManipulator-X Viewer...
echo ===============================================================================
echo.
cd omx_ball_manipulation
"!PYTHON_CMD!" -m mujoco.viewer --mjcf=single_arm/scene.xml
cd ..
echo.
pause
goto menu

:launch_two_arm
cls
echo ===============================================================================
echo [>] Launching Stage 2: Asymmetric Two-Arm (Franka FR3 + HEAL) Manipulation...
echo ===============================================================================
echo.
cd two_arm_ball_manipulation
"!PYTHON_CMD!" ball_balance_controller.py
cd ..
echo.
pause
goto menu

:launch_humanoid_plate
cls
echo ===============================================================================
echo [>] Launching Stage 3: Humanoid Bimanual Plate Balancing...
echo ===============================================================================
echo.
cd simulation_ref
"!PYTHON_CMD!" balance_plate.py
cd ..
echo.
pause
goto menu

:launch_humanoid_steering
cls
echo ===============================================================================
echo [>] Launching Stage 3: Humanoid Steering Wheel Simulation...
echo ===============================================================================
echo.
cd simulation_ref
"!PYTHON_CMD!" steering_simulation.py
cd ..
echo.
pause
goto menu

:build_frontend
cls
echo ===============================================================================
echo [>] Building Frontend Production Bundle...
echo ===============================================================================
echo.
cd frontend
call npm run build
cd ..
echo.
echo [+] Build process completed successfully.
pause
goto menu

:install_deps
cls
echo ===============================================================================
echo [>] Installing / Updating Python requirements...
echo ===============================================================================
"!PYTHON_CMD!" -m pip install -r requirements.txt
echo.
echo ===============================================================================
echo [>] Installing / Updating Frontend npm packages...
echo ===============================================================================
cd frontend
call npm install
cd ..
echo.
echo [+] All dependencies installed successfully.
pause
goto menu

:run_setup
cls
call "%~dp0setup.bat"
goto menu

:exit_launcher
echo.
echo Goodbye!
exit /b 0
