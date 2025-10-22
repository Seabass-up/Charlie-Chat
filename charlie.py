#!/usr/bin/env python3
"""
Charlie - A voice-enabled AI assistant application

This is the main entry point for the Charlie application.
"""

import sys
import logging
import argparse
from datetime import datetime
import os

from src.config_manager import ConfigManager
from src.utils import get_system_info, format_timestamp

# Configure logging
logging.basicConfig(
    level=logging.NOTSET,  # Will be set from configuration later
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('Charlie')


class Charlie:
    """Main Charlie application class."""
    
    def __init__(self, config_path: str | None = None) -> None:
        """Initialize the Charlie application.

        Args:
            config_path: Optional path to the configuration file.
        """
        self.start_time = datetime.now()
        logger.info(f"Charlie initialized at {self.start_time}")

        # Load configuration
        self.config_manager = ConfigManager(config_path)

        # Set log level from configuration with safety guard
        log_level_str = self.config_manager.get('application', 'log_level', 'INFO')
        try:
            log_level = getattr(logging, log_level_str)
        except AttributeError:
            logger.warning(f"Invalid log level '{log_level_str}' in config; defaulting to INFO")
            log_level = logging.INFO
        logging.getLogger().setLevel(log_level)

        # Initialize voice assistant if enabled
        self.voice_assistant = None
        # Allow environment variable override to disable voice in certain contexts (e.g., web server)
        disable_voice_env = os.environ.get('CHARLIE_DISABLE_VOICE', '').lower() in ('1', 'true', 'yes')
        if (self.config_manager.get('features', 'voice_enabled', False)) and not disable_voice_env:
            self._init_voice_assistant()
    
    def _init_voice_assistant(self) -> None:
        """Initialize the voice assistant component.

        Attempts to import and instantiate the voice assistant based on configuration.
        If any import or initialization error occurs, the voice features are disabled
        and a warning is logged with actionable solutions.
        """
        try:
            from src.voice.assistant import VoiceAssistant

            # Get voice assistant configuration with validation
            voiceConfig = self.config_manager.get_section('voice', {})

            # Validate critical voice configuration
            required_keys = ['ollama_model', 'whisper_model', 'june_env_path']
            missing_keys = [key for key in required_keys if key not in voiceConfig or not voiceConfig[key]]

            if missing_keys:
                logger.warning(f"Missing voice configuration keys: {missing_keys}")
                logger.warning("Please check your config.yaml file in the 'voice' section")
                logger.warning("Required keys: ollama_model, whisper_model, june_env_path")
                logger.warning("Voice features will be disabled")
                return

            # Validate June environment path exists
            june_path = voiceConfig.get('june_env_path')
            if june_path and not os.path.exists(june_path):
                logger.warning(f"June environment not found at: {june_path}")
                logger.warning("SOLUTION: Create it with 'python -m venv june-env' and 'pip install june-va'")
                logger.warning("Or update 'june_env_path' in config.yaml to the correct path")
                logger.warning("Voice features will be disabled")
                return

            # Create voice assistant
            self.voice_assistant = VoiceAssistant(voiceConfig)
            logger.info("Voice assistant initialized successfully")

        except ImportError as e:
            logger.warning(f"Could not import voice assistant: {e}")
            logger.warning("SOLUTION: Install required packages: pip install pyttsx3 transformers torch")
            logger.warning("Voice features will be disabled")
        except FileNotFoundError as e:
            logger.warning(f"Voice assistant configuration file not found: {e}")
            logger.warning("SOLUTION: Check that config.yaml exists and has a 'voice' section")
            logger.warning("Voice features will be disabled")
        except Exception as e:
            logger.error(f"Error initializing voice assistant: {e}")
            logger.error("SOLUTION: Check your June installation and configuration")
            logger.error("Run: python -c 'import src.voice.assistant' to test imports")
            logger.warning("Voice features will be disabled")
    
    def run(self, args: list[str] | None = None) -> None:
        """Run the main application.

        Args:
            args: Optional list of command‑line arguments. If ``None`` the arguments
                are taken from ``sys.argv`` as usual.
        """
        logger.info("Charlie is running...")

        # Parse command-line arguments using a dedicated parser builder
        parser = self._build_parser()
        parsedArgs = parser.parse_args(args)

        # Print welcome message
        self._print_welcome()

        # Determine which mode to run in
        if parsedArgs.voice or self.config_manager.get('features', 'voice_enabled', False):
            self._run_voice_mode(parsedArgs)
        else:
            self._run_text_mode()
    
    def _print_welcome(self) -> None:
        """Display a friendly welcome banner with optional system info.

        The version and start time are read from the configuration. When
        ``debug_mode`` is enabled, additional system information is printed.
        """
        print("=" * 50)
        print("Welcome to Charlie - Your AI Assistant")
        print(f"Version: {self.config_manager.get('application', 'version', '0.1.0')}")
        print(f"Started at: {format_timestamp(self.start_time)}")
        print("=" * 50)

        if self.config_manager.get('application', 'debug_mode', False):
            print("\nSystem Information:")
            for key, value in get_system_info().items():
                print(f"  {key}: {value}")
            print("=" * 50)

    def _build_parser(self) -> argparse.ArgumentParser:
        """Create and return the argparse parser for the CLI.

        Centralising parser construction makes it easier to test and to add
        new arguments in the future.
        """
        parser = argparse.ArgumentParser(description='Charlie AI Assistant')
        parser.add_argument('--config', type=str, help='Path to configuration file')
        parser.add_argument('--voice', action='store_true', help='Enable voice mode')
        parser.add_argument('--text', action='store_true', help='Enable text-only mode')
        parser.add_argument('--continuous', action='store_true', help='Enable continuous listening mode')
        parser.add_argument('--wake-word', type=str, help='Set wake word for voice activation')
        return parser
    
    def _run_voice_mode(self, args) -> None:
        """Run the application in voice mode.

        Args:
            args: Parsed command‑line arguments (as returned by ``_build_parser``).
        """
        # Ensure the voice assistant is initialized
        if self.voice_assistant is None:
            self._init_voice_assistant()

        if self.voice_assistant is None:
            logger.error("Voice assistant could not be initialized")
            print("Voice mode is not available. Falling back to text mode.")
            self._run_text_mode()
            return

        # Import voice CLI and build its argument list
        try:
            from src.voice.cli import main as voice_cli_main

            cliArgs: list[str] = []

            # Model configuration
            model = self.config_manager.get('voice', 'ollama_model', 'llama2')
            cliArgs.extend(['--model', model])

            whisperModel = self.config_manager.get('voice', 'whisper_model', 'openai/whisper-small.en')
            cliArgs.extend(['--whisper-model', whisperModel])

            ttsModel = self.config_manager.get('voice', 'tts_model', 'tts_models/en/ljspeech/glow-tts')
            cliArgs.extend(['--tts-model', ttsModel])

            # Wake word handling
            wakeWord = args.wake_word or self.config_manager.get('voice', 'wake_word')
            if wakeWord:
                cliArgs.extend(['--wake-word', wakeWord])

            # Continuous listening flag
            if args.continuous or self.config_manager.get('voice', 'continuous', False):
                cliArgs.append('--continuous')

            # Text‑only mode flag
            if args.text:
                cliArgs.append('--text-mode')

            # Execute the voice CLI with the constructed arguments
            sys.argv = [sys.argv[0]] + cliArgs
            voice_cli_main()

        except ImportError as e:
            logger.error(f"Could not import voice CLI: {e}")
            print("Voice mode is not available. Falling back to text mode.")
            self._run_text_mode()
        except Exception as e:
            logger.error(f"Error running voice mode: {e}")
            print("Error in voice mode. Falling back to text mode.")
            self._run_text_mode()
    
    def _run_text_mode(self) -> None:
        """Run the application in interactive text‑only mode.

        The REPL gracefully handles ``KeyboardInterrupt`` and ``EOFError`` so the
        user can exit with ``Ctrl‑C`` or ``Ctrl‑D`` (Windows ``Ctrl‑Z``).
        """
        print("\nCharlie Text Mode")
        print("Type 'exit' or 'quit' to exit")
        print("=" * 50)

        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                response = self._process_text_input(user_input)
                print(f"Charlie: {response}")
                print("-" * 50)
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nEOF received – exiting.")
                break
            except Exception as e:
                logger.error(f"Error processing input: {e}")
                print(f"Error: {e}")

    def _process_text_input(self, text: str) -> str:
        """Process a line of text input and return a response.

        Args:
            text: The raw user input.

        Returns:
            A response string. If a voice assistant is configured it will be used;
            otherwise a simple echo is returned.
        """
        if self.voice_assistant is not None:
            return self.voice_assistant.process_input(text)
        return f"You said: {text}"
    
    def shutdown(self) -> None:
        """Perform cleanup actions and log runtime information."""
        end_time = datetime.now()
        runtime = end_time - self.start_time
        logger.info(f"Charlie shutting down. Runtime: {runtime}")
        # Future resource cleanup (e.g., microphone streams) can be added here


def main() -> None:
        """Application entry point.

        Reads the optional ``CHARLIE_CONFIG`` environment variable to locate the
        configuration file, instantiates the ``Charlie`` class and runs the
        application. All unexpected exceptions are logged and a graceful shutdown
        is performed.
        """
        config_path = os.environ.get('CHARLIE_CONFIG')
        app = Charlie(config_path)
        try:
            app.run()
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            logger.error(f"Error in Charlie: {e}")
        finally:
            app.shutdown()


if __name__ == "__main__":
    main()
