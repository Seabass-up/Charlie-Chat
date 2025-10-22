# Charlie-Chat

## Overview

Charlie-Chat is a voice-enabled AI assistant application that provides both text and voice interaction capabilities. This project offers a clean, modular structure following best practices for Python development.

## Features

- Structured logging system
- Clean object-oriented design
- Voice interaction using June for speech-to-text and text-to-speech
- Ollama integration for local LLM responses
- Conversation memory for contextual interactions
- Configurable wake word and listening modes
- Fully offline operation with no cloud dependencies

## Configuration

Charlie-Chat's configuration is managed through a YAML file (`config.yaml`). You can customize various settings including:

- **Application Settings**: Name, version, debug mode, and log level.
- **User Preferences**: Username, theme, and language.
- **Feature Toggles**: Enable or disable features like voice capabilities.
- **Voice Assistant Settings**: Specify models for Ollama, Whisper, and TTS, as well as API endpoint and key for Ollama Turbo API.
- **MCP Settings**: Enable Model Context Protocol servers for enhanced functionality.

### Voice Configuration

```yaml
voice:
  june_env_path: C:/Users/seaba/june-env  # Path to June virtual environment (configurable)
  ollama_model: gpt-oss:120b  # Ollama model to use
  whisper_model: openai/whisper-small.en  # Whisper model for speech recognition
  tts_model: coqui/XTTS-v2  # TTS model for speech synthesis
  wake_word: Charlie  # Optional wake word to trigger the assistant
  continuous: false  # Enable continuous listening mode
  listen_timeout: 5  # Timeout in seconds for listening
  ollama_api_endpoint: https://ollama.com  # Endpoint for Ollama API
  ollama_api_key: your-actual-api-key-here  # API key for Ollama Turbo API
```

### MCP Configuration

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/Users/seaba/Desktop", "C:/Users/seaba/Documents"],
      "env": {}
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "disabled": false
    }
  }
}
```

To use the Ollama Turbo API, update the `voice` section in `config.yaml` with the appropriate `ollama_api_endpoint` and `ollama_api_key`.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Ollama installed and running locally

### Setup

1. Clone this repository

2. Create a virtual environment (recommended):

   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install MCP packages (for enhanced AI capabilities):

   ```bash
   # As administrator/root (if needed)
   npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-memory @modelcontextprotocol/server-puppeteer @playwright/mcp @modelcontextprotocol/server-postgres @modelcontextprotocol/server-sequential-thinking mcp-remote
   ```

   Or use the automated setup script:

   ```bash
   # Windows
   setup_charlie.bat

   # Or manually from requirements file
   npm install -g -r requirements-mcp.txt
   ```

4. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Set up voice environment:

   ```bash
   # Windows
   setup_june.bat

   # Or manually:
   python -m venv june-env
   june-env\Scripts\activate  # On Windows
   pip install june-va
   ```

6. Download required models:

   ```bash
   ollama pull gpt-oss:120b
   ```

Run the application with:

```bash
python charlie.py
```

### Command-line Options

```bash
python charlie.py [options]

Options:
  --config PATH       Path to configuration file
  --voice             Enable voice mode
  --text              Enable text-only mode
  --continuous        Enable continuous listening mode
  --wake-word WORD    Set wake word for voice activation
```

### Voice Mode

Voice mode allows you to interact with Charlie-Chat using speech:

```bash
python charlie.py --voice
```

For continuous listening with a wake word:

```bash
python charlie.py --voice --continuous --wake-word Charlie
```

## Project Structure

```
Charlie-Chat/
├── charlie.py        # Main application entry point
├── config.yaml       # Configuration settings
├── requirements.txt  # Project dependencies
├── README.md         # This documentation file
├── Charlie.bat       # Windows launcher script
├── web_server.py     # Web interface server
└── src/              # Source code modules
    ├── config_manager.py  # Configuration handling
    ├── utils.py           # Utility functions
    └── voice/             # Voice assistant components
        ├── assistant.py   # Voice assistant integration
        └── cli.py         # Command-line interface for voice
└── web/              # Web interface files
    ├── index.html     # Web UI
    ├── main.js        # JavaScript for web interface
    └── styles.css     # Styling for web interface
```

## Troubleshooting

### Common Issues and Solutions

#### Voice Assistant Issues

**"June environment not found"**
- **Solution**: Update `june_env_path` in `config.yaml` to the correct path
- **Or**: Run `setup_june.bat` or manually create: `python -m venv june-env && pip install june-va`

**"Python not found in June environment"**
- **Solution**: Reinstall June: `pip install june-va` in the June environment
- **Check**: Ensure you're in the activated environment: `june-env\Scripts\activate`

**"June binary not found"**
- **Solution**: The application will fall back to using the Python module
- **Alternative**: Run `pip install june-va` to reinstall the package

#### MCP Server Issues

**"MCP server failed to start"**
- **Solution**: Check that Node.js and npm are installed
- **Install packages**: Run `npm install -g @modelcontextprotocol/server-filesystem` etc.
- **Enable servers**: Set `"disabled": false` in `mcp_config.json`

**"Permission denied" for npm packages**
- **Solution**: Run command prompt as administrator
- **Alternative**: Install packages locally in your project directory

#### Configuration Issues

**"Missing voice configuration keys"**
- **Solution**: Check that `config.yaml` has all required keys in the `voice` section
- **Required keys**: `ollama_model`, `whisper_model`, `june_env_path`
- **Check**: Validate YAML syntax and ensure no missing values

**"Invalid log level"**
- **Solution**: Set valid log levels in config: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### Testing Your Setup

1. **Test imports**:
   ```bash
   python -c "import src.voice.assistant; print('Voice assistant imports OK')"
   ```

2. **Test configuration**:
   ```bash
   python -c "from src.config_manager import ConfigManager; cm = ConfigManager(); print(cm.get_section('voice', {}))"
   ```

3. **Test voice only**:
   ```bash
   python test_voice.py
   ```

4. **Test web interface**:
   ```bash
   python web_server.py
   ```

### Logs and Debugging

- **Enable debug logging**: Set `log_level: DEBUG` in `config.yaml`
- **Check logs**: Look for detailed error messages in the console
- **Test components**: Use individual test files to isolate issues

### Environment Variables

You can override configuration with environment variables:
- `CHARLIE_DISABLE_VOICE=1` - Disable voice features
- `OLLAMA_API_KEY=your-key` - Override Ollama API key

## Development

This project follows these coding standards:

- PEP 8 for Python code style
- Clear docstrings for all modules, classes, and functions
- Consistent naming conventions:
  - Variables: `camelCase`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`

## Voice Assistant Integration

Charlie-Chat now uses the **pyttsx3** library for offline text‑to‑speech synthesis, providing cross‑platform audio output without external model dependencies.

Charlie-Chat integrates with June for voice interaction capabilities:

- **Speech Recognition**: Uses Whisper via Hugging Face Transformers
- **Text-to-Speech**: Uses pyttsx3 offline TTS engine
- **LLM Integration**: Connects to Ollama for local language model responses
- **Conversation Memory**: Maintains context across interactions
- **Privacy-Focused**: All processing happens locally with no data sent to external servers

## License

[MIT License](LICENSE)
