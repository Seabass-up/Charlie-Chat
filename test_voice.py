#!/usr/bin/env python3
"""
Test script for Charlie's voice assistant functionality.
"""

import argparse
import logging
import sys
from src.voice.assistant import VoiceAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('VoiceTest')

def main():
    """Main entry point for the voice assistant test script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Test Charlie Voice Assistant')
    parser.add_argument('--model', type=str, default='llama2', help='Ollama model to use')
    parser.add_argument('--whisper-model', type=str, default='openai/whisper-small.en', help='Whisper model to use')
    parser.add_argument('--tts-model', type=str, default='tts_models/en/ljspeech/glow-tts', help='TTS model to use')
    parser.add_argument('--text', action='store_true', help='Test text input instead of voice')
    
    args = parser.parse_args()
    
    # Print test configuration
    print("=" * 50)
    print("Charlie Voice Assistant Test")
    print("=" * 50)
    print(f"Ollama Model: {args.model}")
    print(f"Whisper Model: {args.whisper_model}")
    print(f"TTS Model: {args.tts_model}")
    print(f"Mode: {'Text Input' if args.text else 'Voice Input'}")
    print("=" * 50)
    
    # Create voice assistant configuration
    voice_config = {
        'ollama_model': args.model,
        'whisper_model': args.whisper_model,
        'tts_model': args.tts_model
    }
    
    try:
        # Initialize voice assistant
        print("\nInitializing voice assistant...")
        assistant = VoiceAssistant(voice_config)
        print("Voice assistant initialized successfully!")
        
        # Test voice assistant
        if args.text:
            test_text_mode(assistant)
        else:
            test_voice_mode(assistant)
            
    except Exception as e:
        logger.error(f"Error testing voice assistant: {e}")
        print(f"\nError: {e}")
        return 1
    
    return 0

def test_text_mode(assistant):
    """Test the voice assistant with text input."""
    print("\nTesting text input mode...")
    print("Type 'exit' or 'quit' to end the test.")
    print("-" * 50)
    
    while True:
        # Get user input
        user_input = input("You: ")
        
        # Check if user wants to exit
        if user_input.lower() in ['exit', 'quit']:
            break
        
        # Process user input
        print("Processing...")
        response = assistant.process_input(user_input)
        
        # Print and speak response
        print(f"Charlie: {response}")
        print("Speaking response...")
        assistant.speak(response)
        print("-" * 50)

def test_voice_mode(assistant):
    """Test the voice assistant with voice input."""
    print("\nTesting voice input mode...")
    print("Say 'exit' or 'quit' to end the test.")
    print("Press Ctrl+C to interrupt.")
    print("-" * 50)
    
    try:
        while True:
            # Listen for user input
            print("Listening...")
            user_input = assistant.listen()
            print(f"You said: {user_input}")
            
            # Check if user wants to exit
            if user_input.lower() in ['exit', 'quit']:
                break
            
            # Process user input
            print("Processing...")
            response = assistant.process_input(user_input)
            
            # Print and speak response
            print(f"Charlie: {response}")
            print("Speaking response...")
            assistant.speak(response)
            print("-" * 50)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    
if __name__ == "__main__":
    sys.exit(main())
