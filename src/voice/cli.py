"""
Command-line interface for the Charlie Voice Assistant.

This module provides a simple CLI for interacting with the voice assistant.
"""

import argparse
import logging
import sys
import time
from typing import Dict, Any

from .assistant import VoiceAssistant

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('Charlie.Voice.CLI')


def create_config_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Create a configuration dictionary from command-line arguments.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        dict: Configuration dictionary.
    """
    config = {
        'ollama_model': args.model,
        'whisper_model': args.whisper_model,
        'tts_model': args.tts_model,
        'wake_word': args.wake_word,
        'continuous': args.continuous,
        'listen_timeout': args.timeout,
    }
    return config


def main():
    """Main entry point for the CLI."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Charlie Voice Assistant CLI')
    parser.add_argument('--model', type=str, default='llama2',
                        help='Ollama model to use (default: llama2)')
    parser.add_argument('--whisper-model', type=str, default='openai/whisper-small.en',
                        help='Whisper model to use for speech recognition (default: openai/whisper-small.en)')
    parser.add_argument('--tts-model', type=str, default='tts_models/en/ljspeech/glow-tts',
                        help='TTS model to use for speech synthesis (default: tts_models/en/ljspeech/glow-tts)')
    parser.add_argument('--wake-word', type=str, default=None,
                        help='Wake word to trigger the assistant (default: None)')
    parser.add_argument('--continuous', action='store_true',
                        help='Enable continuous listening mode')
    parser.add_argument('--timeout', type=int, default=5,
                        help='Timeout in seconds for listening (default: 5)')
    parser.add_argument('--text-mode', action='store_true',
                        help='Enable text-only mode (no voice)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Create voice assistant
    assistant = VoiceAssistant(config)
    
    try:
        # Initialize the assistant
        assistant.initialize()
        
        if args.text_mode:
            # Text-only mode
            print("Charlie Voice Assistant (Text Mode)")
            print("Type 'exit' or 'quit' to exit")
            print("=" * 50)
            
            while True:
                # Get user input
                user_input = input("You: ")
                
                # Check if user wants to exit
                if user_input.lower() in ['exit', 'quit']:
                    break
                    
                # Process input
                response = assistant.process_input(user_input)
                
                # Print response
                print(f"Charlie: {response}")
                print("-" * 50)
                
        elif args.continuous:
            # Continuous listening mode
            print("Charlie Voice Assistant (Continuous Listening Mode)")
            print(f"Wake word: {args.wake_word or 'None'}")
            print("Say 'exit' or 'quit' to exit")
            print("=" * 50)
            
            # Define callback function for continuous listening
            def on_transcription(text):
                if text.lower() in ['exit', 'quit']:
                    assistant.stop_listening()
                    return
                    
                print(f"You: {text}")
                
                # Process input and speak response
                response = assistant.process_and_speak(text)
                
                print(f"Charlie: {response}")
                print("-" * 50)
            
            # Start continuous listening
            assistant.start_continuous_listening(
                callback=on_transcription,
                wake_word=args.wake_word,
                listen_timeout=args.timeout
            )
            
            # Keep the main thread alive
            try:
                while assistant.is_listening:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                assistant.stop_listening()
                
        else:
            # Interactive mode
            print("Charlie Voice Assistant (Interactive Mode)")
            print("Press Enter to start listening, or type 'exit' or 'quit' to exit")
            print("=" * 50)
            
            while True:
                # Prompt user to start listening
                user_input = input("Press Enter to start listening (or type to send text directly): ")
                
                # Check if user wants to exit
                if user_input.lower() in ['exit', 'quit']:
                    break
                    
                if user_input:
                    # Process text input
                    response = assistant.process_and_speak(user_input)
                else:
                    # Listen, process, and speak
                    print("Listening...")
                    response = assistant.listen_process_speak()
                    
                if response:
                    print(f"Charlie: {response}")
                    print("-" * 50)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Clean up
        if assistant.is_listening:
            assistant.stop_listening()
            
    print("Goodbye!")


if __name__ == "__main__":
    main()
