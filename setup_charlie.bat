@echo off
echo ===================================================
echo     Charlie-Chat Complete Setup Script
echo ===================================================

echo [INFO] Starting Charlie-Chat setup...

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set JUNE_ENV=%SCRIPT_DIR%june-env

echo [INFO] Script directory: %SCRIPT_DIR%
echo [INFO] June environment will be created at: %JUNE_ENV%

REM Check if Node.js is installed (required for MCP)
echo [INFO] Checking Node.js installation...
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed.
    echo Please install Node.js from https://nodejs.org/
    echo Then run this script again.
    pause
    exit /b 1
) else (
    echo [INFO] Node.js is installed.
)

REM Check if npm is available
npm --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not available.
    echo Please install npm or check Node.js installation.
    pause
    exit /b 1
) else (
    echo [INFO] npm is available.
)

REM Install MCP packages globally
echo [INFO] Installing MCP (Model Context Protocol) packages...
npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-memory @modelcontextprotocol/server-puppeteer @playwright/mcp @modelcontextprotocol/server-postgres @modelcontextprotocol/server-sequential-thinking mcp-remote

if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some MCP packages may have failed to install.
    echo This is normal if you don't have admin privileges.
    echo You can install them manually later with: npm install -g [package-name]
) else (
    echo [INFO] MCP packages installed successfully.
)

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.8+ from https://python.org/
    pause
    exit /b 1
) else (
    echo [INFO] Python is installed.
)

REM Check if the June environment already exists
if exist "%JUNE_ENV%" (
    echo [INFO] June environment found at %JUNE_ENV%
    echo [INFO] Updating existing environment...
    call "%JUNE_ENV%\Scripts\activate.bat"
) else (
    echo [INFO] Creating June virtual environment at %JUNE_ENV%...
    python -m venv "%JUNE_ENV%"

    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        echo Please make sure Python venv is available and try again.
        pause
        exit /b 1
    )

    echo [INFO] Activating June environment...
    call "%JUNE_ENV%\Scripts\activate.bat"
)

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install core requirements
echo [INFO] Installing core Python dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install core dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

REM Check if June is installed
echo [INFO] Checking June installation...
pip show june-va >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] June voice assistant is already installed.
) else (
    echo [INFO] Installing June voice assistant...
    pip install june-va

    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install June voice assistant.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    ) else (
        echo [SUCCESS] June voice assistant installed successfully!
    )
)

REM Test June installation
echo [INFO] Testing June installation...
python -c "import june_va; print('June imported successfully')" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] June module test passed.
) else (
    echo [WARNING] June module test failed.
    echo This may indicate an issue with the installation.
)

REM Check if Ollama is installed
echo [INFO] Checking Ollama installation...
where ollama >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Ollama is already installed.

    REM Check if the required model is available
    echo [INFO] Checking for gpt-oss:120b model...
    ollama list | findstr gpt-oss:120b >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [INFO] gpt-oss:120b model is available.
    ) else (
        echo [INFO] Downloading gpt-oss:120b model...
        echo [WARNING] This may take several minutes...
        ollama pull gpt-oss:120b
        if %ERRORLEVEL% NEQ 0 (
            echo [WARNING] Failed to download gpt-oss:120b model automatically.
            echo Please run 'ollama pull gpt-oss:120b' manually.
        ) else (
            echo [INFO] gpt-oss:120b model downloaded successfully.
        )
    )
) else (
    echo [WARNING] Ollama is not installed.
    echo Please install Ollama from https://ollama.ai/download
    echo After installing Ollama, run: ollama pull gpt-oss:120b
)

echo.
echo ===================================================
echo     Setup Complete
echo ===================================================
echo.
echo Charlie-Chat setup completed successfully!
echo.
echo To use Charlie-Chat:
echo 1. Make sure Ollama is running: ollama serve
echo 2. Run Charlie with voice: python charlie.py --voice
echo 3. Or test voice: python test_voice.py
echo 4. Or use web interface: python web_server.py
echo.
echo Configuration can be modified in config.yaml
echo MCP servers are enabled in mcp_config.json
echo.
echo ===================================================

pause
