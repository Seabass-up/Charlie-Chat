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

Charlie's configuration is managed through a YAML file (`config.yaml`). You can customize various settings including:

- **Application Settings**: Name, version, debug mode, and log level.
- **User Preferences**: Username, theme, and language.
- **Feature Toggles**: Enable or disable features like voice capabilities.
- **Voice Assistant Settings**: Specify models for Ollama, Whisper, and TTS, as well as API endpoint and key for Ollama Turbo API.

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

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

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

## Development

This project follows these coding standards:

- PEP 8 for Python code style
- Clear docstrings for all modules, classes, and functions
- Consistent naming conventions:
  - Variables: `camelCase`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`

## Voice Assistant Integration

Charlie now uses the **pyttsx3** library for offline text‑to‑speech synthesis, providing cross‑platform audio output without external model dependencies.

Charlie integrates with June for voice interaction capabilities:

- **Speech Recognition**: Uses Whisper via Hugging Face Transformers
- **Text-to-Speech**: Uses pyttsx3 offline TTS engine
- **LLM Integration**: Connects to Ollama for local language model responses
- **Conversation Memory**: Maintains context across interactions
- **Privacy-Focused**: All processing happens locally with no data sent to external servers

## License

[MIT License](LICENSE)
