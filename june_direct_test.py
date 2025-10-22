#!/usr/bin/env python
"""
Direct test script for June voice assistant.

This script directly tests the June voice assistant by running it as a subprocess
and sending input through stdin.
"""

import os
import sys
import subprocess
import json
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_june_config(model="gemma3:12b"):
    """Update the June configuration file."""
    june_config_dir = os.path.expanduser("~/.june")
    june_config_file = os.path.join(june_config_dir, "config.json")
    
    # Create config directory if it doesn't exist
    os.makedirs(june_config_dir, exist_ok=True)
    
    # Default config
    config = {
        "stt_model": "openai/whisper-small.en",
        "tts_model": "tts_models/en/ljspeech/glow-tts",
        "ollama_model": model,
        "memory": True,
        "memory_size": 5
    }
    
    # Read existing config if it exists
    if os.path.exists(june_config_file):
        try:
            with open(june_config_file, 'r') as f:
                existing_config = json.load(f)
                config.update(existing_config)  # Keep existing settings
        except Exception as e:
            logger.warning(f"Error reading June config: {e}")
    
    # Update with new model
    config["ollama_model"] = model
    
    # Write updated config
    try:
        with open(june_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Updated June config with model: {model}")
        return True
    except Exception as e:
        logger.error(f"Error updating June config: {e}")
        return False

def test_june(query="Tell me a joke"):
    """Test June with a simple query."""
    june_env = "C:\\Users\\seaba\\june-env"
    june_exe = os.path.join(june_env, "Scripts", "june-va.exe")
    
    if not os.path.exists(june_exe):
        logger.error(f"June executable not found at: {june_exe}")
        return False
    
    logger.info(f"Testing June with query: {query}")
    
    try:
        # Start June process
        process = subprocess.Popen(
            [june_exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Wait a moment for June to initialize
        time.sleep(2)
        
        # Send query
        logger.info("Sending query to June...")
        process.stdin.write(f"{query}\n")
        process.stdin.flush()
        
        # Wait for response (maximum 30 seconds)
        logger.info("Waiting for response...")
        start_time = time.time()
        response_received = False
        
        while time.time() - start_time < 30:
            # Check if process is still running
            if process.poll() is not None:
                logger.warning("June process terminated unexpectedly")
                break
            
            # Try to read output
            output = process.stdout.readline().strip()
            if output:
                print(output)
                
                # Check if we got a response
                if "[assistant]>" in output:
                    response_received = True
                    response = output.replace("[assistant]>", "").strip()
                    logger.info(f"Response received: {response}")
                    break
            
            # Small delay to prevent high CPU usage
            time.sleep(0.1)
        
        # Terminate process
        logger.info("Terminating June process...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Process did not terminate gracefully, killing...")
            process.kill()
        
        return response_received
        
    except Exception as e:
        logger.error(f"Error testing June: {e}")
        return False

def main():
    """Main function."""
    # Get model from command line
    model = "gemma3:12b"
    if len(sys.argv) > 1:
        model = sys.argv[1]
    
    # Get query from command line
    query = "Tell me a joke"
    if len(sys.argv) > 2:
        query = sys.argv[2]
    
    # Update June config
    if not update_june_config(model):
        logger.error("Failed to update June config")
        return 1
    
    # Test June
    if test_june(query):
        logger.info("June test successful")
        return 0
    else:
        logger.error("June test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
