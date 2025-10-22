@echo off
echo ===================================================
echo     Charlie Voice Assistant Setup
echo ===================================================

set JUNE_ENV=C:\Users\seaba\june-env

REM Check if the June environment already exists
if exist "%JUNE_ENV%" (
    echo [INFO] June environment found at %JUNE_ENV%
) else (
    echo [INFO] Creating June virtual environment at %JUNE_ENV%...
    python -m venv "%JUNE_ENV%"
    
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        echo Please make sure Python is installed and try again.
        pause
        exit /b 1
    )
)

REM Activate the environment and install June
echo [INFO] Activating June environment...
call "%JUNE_ENV%\Scripts\activate.bat"

REM Check if June is installed
"%JUNE_ENV%\Scripts\pip" show june-va >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] June voice assistant is already installed.
) else (
    echo [INFO] Installing June voice assistant...
    "%JUNE_ENV%\Scripts\pip" install june-va
    
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install June voice assistant.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    ) else (
        echo [SUCCESS] June voice assistant installed successfully!
    )
)

REM Check if Ollama is installed
where ollama >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Ollama is already installed.
    
    REM Check if the required model is available
    echo [INFO] Checking for gemma3:12b model...
    ollama list | findstr gemma3:12b >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [INFO] gemma3:12b model is available.
    ) else (
        echo [INFO] Downloading gemma3:12b model...
        start /b ollama pull gemma3:12b
        echo [INFO] Model download started in background. This may take a while.
    )
) else (
    echo [WARNING] Ollama is not installed.
    echo Please install Ollama from https://ollama.ai/download
    echo After installing Ollama, run: ollama pull gemma3:12b
)

echo.
echo ===================================================
echo     Setup Complete
echo ===================================================
echo.
echo To use the Charlie voice assistant:
echo 1. Make sure Ollama is running with: ollama serve
echo 2. Run Charlie with the --voice flag: python charlie.py --voice
echo 3. Or test the voice assistant directly: python test_voice.py --text
echo.
echo ===================================================

pause
