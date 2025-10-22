"""
Voice Assistant Integration for Charlie.

This module integrates with June for voice interaction capabilities,
providing speech-to-text and text-to-speech functionality.
"""

import os
import logging
import threading
import time
import subprocess
import sys
import shutil
import json
import pyttsx3
from typing import Callable, Optional, Dict, Any

# Set up logging
logger = logging.getLogger('Charlie.Voice')

class VoiceAssistant:
    """
    Voice Assistant class that integrates with June for speech recognition and synthesis.
    
    This class provides a wrapper around June's functionality to enable voice
    interaction within the Charlie application.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Voice Assistant.
        
        Args:
            config: Configuration dictionary for the voice assistant.
        """
        self.config = config or {}
        self.is_listening = False
        self.is_speaking = False
        self.june_instance = None
        
        # Get model configurations from config
        # The config passed is already the voice section from charlie.py
        self.ollama_model = self.config.get('ollama_model', 'gpt-oss:120b')
        self.whisper_model = self.config.get('whisper_model', 'openai/whisper-small.en')
        self.tts_model = self.config.get('tts_model', 'coqui/XTTS-v2')
        self.ollama_api_endpoint = self.config.get('ollama_api_endpoint', 'https://api.ollama.com')
        self.ollama_api_key = self.config.get('ollama_api_key', 'your_api_key_here')
        # Initialize pyttsx3 engine for TTS (offline, works on Python 3.12)
        try:
            self.engine = pyttsx3.init()
            # Optionally set voice properties (rate, volume, etc.)
            self.engine.setProperty('rate', 150)
            logger.info("Initialized pyttsx3 TTS engine")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}")
            self.engine = None
        
        logger.info(f"Using Ollama model: {self.ollama_model}")
        logger.info(f"Using Ollama API endpoint: {self.ollama_api_endpoint}")
        
        # Find the June virtual environment
        self.june_env_path = "C:\\Users\\seaba\\june-env"
        self.june_cmd = os.path.join(self.june_env_path, "Scripts", "june-va.exe")
        self.june_python = os.path.join(self.june_env_path, "Scripts", "python.exe")
        
        # June configuration file path
        self.june_config_dir = os.path.expanduser("~/.june")
        self.june_config_file = os.path.join(self.june_config_dir, "config.json")
        
        # Initialize June components lazily to avoid importing until needed
        self._initialized = False
        
    def initialize(self):
        """Initialize June components for voice interaction."""
        if self._initialized:
            return
            
        try:
            # Check if June environment exists
            logger.info("Checking June environment...")
            
            if not os.path.exists(self.june_env_path):
                logger.error(f"June environment not found at {self.june_env_path}")
                logger.error("Please create a virtual environment for June: python -m venv june-env")
                logger.error("Then install June: pip install june-va")
                raise ImportError(f"June environment not found at {self.june_env_path}")
                
            if not os.path.exists(self.june_cmd):
                # Try using the module directly if the command is not found
                self.use_module = True
                logger.warning(f"June command not found at {self.june_cmd}")
                logger.info("Will try using the module directly")
                
                if not os.path.exists(self.june_python):
                    logger.error(f"Python not found in June environment at {self.june_python}")
                    raise ImportError(f"Python not found in June environment at {self.june_python}")
            else:
                self.use_module = False
            
            # Update June configuration file with our settings
            self._update_june_config()
            
            logger.info("June environment found")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing June components: {e}")
            raise
    
    def _update_june_config(self):
        """Update the June configuration file with our settings."""
        # Create config directory if it doesn't exist
        os.makedirs(self.june_config_dir, exist_ok=True)
        
        # Read existing config if it exists
        config = {}
        if os.path.exists(self.june_config_file):
            try:
                with open(self.june_config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.warning(f"Error reading June config file: {e}")
        
        # Update config with our settings
        config.update({
            "stt_model": self.whisper_model,
            "tts_model": self.tts_model,
            "ollama_model": self.ollama_model,
            "ollama_api_endpoint": self.ollama_api_endpoint,
            "ollama_api_key": self.ollama_api_key,
            "memory": True,
            "memory_size": 5
        })
        
        # Write updated config
        try:
            with open(self.june_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Updated June config file at {self.june_config_file}")
        except Exception as e:
            logger.error(f"Error writing June config file: {e}")
    
    def listen(self) -> str:
        """
        Listen for speech and convert to text.
        
        Returns:
            str: Transcribed text from speech.
        """
        if not self._initialized:
            self.initialize()
            
        self.is_listening = True
        try:
            logger.info("Listening for speech...")
            
            # Create a temporary file to capture the output
            temp_file = os.path.join(os.getcwd(), "june_output.txt")
            
            # Run June in a way that captures the input
            if self.use_module:
                process = subprocess.Popen(
                    [self.june_python, "-m", "june_va", "-v"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            else:
                process = subprocess.Popen(
                    [self.june_cmd, "-v"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            
            # Wait for the user input prompt
            transcription = ""
            for line in process.stdout:
                logger.debug(f"June output: {line.strip()}")
                if "[user]>" in line:
                    transcription = line.replace("[user]>", "").strip()
                    # Kill the process once we get the transcription
                    process.terminate()
                    break
            
            # Clean up
            process.wait(timeout=2)
            
            if transcription:
                logger.info(f"Transcribed: {transcription}")
                return transcription
            else:
                logger.info("No speech detected")
                return ""
                
        except subprocess.SubprocessError as e:
            logger.error(f"Error during speech recognition: {e}")
            return ""
        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
            return ""
        finally:
            self.is_listening = False
    
    def process_input(self, text: str) -> str:
        """
        Process text input through the LLM.
        
        Args:
            text: Input text to process.
            
        Returns:
            str: Response from the LLM.
        """
        if not self._initialized:
            self.initialize()
            
        try:
            logger.info(f"Processing input: {text}")
            logger.info(f"Using model: {self.ollama_model}")
            
            # Create a temporary file with the input
            temp_input_file = os.path.join(os.getcwd(), "june_input.txt")
            with open(temp_input_file, 'w') as f:
                f.write(text)
            
            # Run June with the input file
            if self.use_module:
                process = subprocess.Popen(
                    [self.june_python, "-m", "june_va", "-v"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            else:
                process = subprocess.Popen(
                    [self.june_cmd, "-v"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            
            # Send the input text
            process.stdin.write(text + "\n")
            process.stdin.flush()
            
            # Wait for the assistant response
            response = ""
            for line in process.stdout:
                logger.debug(f"June output: {line.strip()}")
                if "[assistant]>" in line:
                    response = line.replace("[assistant]>", "").strip()
                    # Kill the process once we get the response
                    process.terminate()
                    break
            
            # Clean up
            process.wait(timeout=2)
            if os.path.exists(temp_input_file):
                os.remove(temp_input_file)
            
            logger.info(f"Response: {response}")
            return response
            
        except subprocess.SubprocessError as e:
            logger.error(f"Error processing input: {e}")
            return "I'm sorry, I encountered an error processing your request."
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return "I'm sorry, I encountered an error processing your request."
    
    def speak(self, text: str):
        """
        Convert text to speech using pyttsx3 (offline).
        
        Args:
            text: Text to convert to speech.
        """
        if not self._initialized:
            self.initialize()
        
        self.is_speaking = True
        try:
            logger.info(f"Speaking: {text}")
            if self.engine is None:
                logger.error("pyttsx3 engine is not initialized; cannot synthesize speech.")
                return
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error during speech synthesis: {e}")
        finally:
            self.is_speaking = False
    
    def process_and_speak(self, text: str) -> str:
        """
        Process text input and speak the response.
        
        Args:
            text: Input text to process.
            
        Returns:
            str: Response from the LLM.
        """
        response = self.process_input(text)
        self.speak(response)
        return response
    
    def listen_process_speak(self) -> str:
        """
        Listen for speech, process it, and speak the response.
        
        Returns:
            str: Response from the LLM.
        """
        text = self.listen()
        if text:
            return self.process_and_speak(text)
        return ""
    
    def start_continuous_listening(self, callback: Callable[[str], None], 
                                  wake_word: Optional[str] = None,
                                  listen_timeout: int = 5):
        """
        Start continuous listening for speech in a separate thread.
        
        Args:
            callback: Function to call with transcribed text.
            wake_word: Optional wake word to trigger processing.
            listen_timeout: Timeout in seconds for listening.
        """
        if not self._initialized:
            self.initialize()
            
        def listening_thread():
            logger.info("Starting continuous listening...")
            
            while self.is_listening:
                try:
                    # Listen for speech
                    transcription = self.listen()
                    
                    # Process if wake word is detected or not required
                    if transcription:
                        if wake_word is None or wake_word.lower() in transcription.lower():
                            # Remove wake word from transcription if present
                            if wake_word and wake_word.lower() in transcription.lower():
                                transcription = transcription.lower().replace(wake_word.lower(), "").strip()
                                
                            # Call callback with transcription
                            if transcription:
                                callback(transcription)
                        
                    # Wait a bit before listening again
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error in listening thread: {e}")
                    time.sleep(1)  # Wait a bit longer on error
        
        # Start listening thread
        self.is_listening = True
        thread = threading.Thread(target=listening_thread)
        thread.daemon = True
        thread.start()
    
    def stop_listening(self):
        """Stop continuous listening."""
        self.is_listening = False
