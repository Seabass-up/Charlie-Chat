@echo off
REM Charlie Application Launcher
REM This batch file runs the Charlie application

echo Starting Charlie...

REM Switch to the directory of this script to ensure relative paths work
pushd "%~dp0"

REM Optional mode argument: "web" to launch the web UI
set "MODE=%1"

REM Ensure virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate

REM Run the application
if /I "%MODE%"=="web" goto WEB
if /I "%MODE%"=="serve" goto SERVE
REM Ensure dependencies are installed for CLI run (full requirements)
pip install -r requirements.txt
python charlie.py
goto END

:WEB
set "CHARLIE_URL=http://localhost:8008/"
echo Launching Charlie Web UI on %CHARLIE_URL% ...
REM Ensure minimal web server dependencies are installed
python -c "import fastapi, uvicorn, pydantic" >nul 2>&1
if errorlevel 1 (
    if exist requirements-web.txt (
        pip install -r requirements-web.txt
    ) else (
        pip install fastapi uvicorn pydantic
    )
)
if not defined CHARLIE_NO_BROWSER (
    start "" %CHARLIE_URL%
)
python -m uvicorn web_server:app --host 127.0.0.1 --port 8008
goto END

:SERVE
echo Launching Charlie Web Server (no browser) on http://localhost:8008/ ...
python -c "import fastapi, uvicorn, pydantic" >nul 2>&1
if errorlevel 1 (
    if exist requirements-web.txt (
        pip install -r requirements-web.txt
    ) else (
        pip install fastapi uvicorn pydantic
    )
)
python -m uvicorn web_server:app --host 127.0.0.1 --port 8008
goto END

REM Deactivate virtual environment
:END
call venv\Scripts\deactivate
popd

echo Charlie has completed execution.
pause
