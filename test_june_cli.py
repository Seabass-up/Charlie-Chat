#!/usr/bin/env python
"""
Test script for the June voice assistant CLI integration.

This script tests the direct interaction with the June CLI
to ensure our voice assistant implementation works correctly.
"""

import os
import sys
import subprocess
import time
import json
import argparse
import logging
import io
import threading
import queue

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('JuneTest')

def setup_june_config(model="gemma3:12b"):
    """Set up the June configuration file."""
    june_config_dir = os.path.expanduser("~/.june")
    june_config_file = os.path.join(june_config_dir, "config.json")
    
    # Create config directory if it doesn't exist
    os.makedirs(june_config_dir, exist_ok=True)
    
    # Read existing config if it exists
    config = {}
    if os.path.exists(june_config_file):
        try:
            with open(june_config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading June config file: {e}")
    
    # Update config with our settings
    config.update({
        "stt_model": "openai/whisper-small.en",
        "tts_model": "tts_models/en/ljspeech/glow-tts",
        "ollama_model": model,
        "memory": True,
        "memory_size": 5
    })
    
    # Write updated config
    try:
        with open(june_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Updated June config file at {june_config_file}")
    except Exception as e:
        logger.error(f"Error writing June config file: {e}")
        return False
    
    return True

def run_june_command(query=None, timeout=30):
    """Run the June command and return the output."""
    june_env_path = "C:\\Users\\seaba\\june-env"
    june_cmd = os.path.join(june_env_path, "Scripts", "june-va.exe")
    
    if not os.path.exists(june_cmd):
        logger.error(f"June command not found at {june_cmd}")
        return None
    
    # Start June process
    try:
        process = subprocess.Popen(
            [june_cmd],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # If a query is provided, send it to June
        if query:
            logger.info(f"Sending query: {query}")
            process.stdin.write(f"{query}\n")
            process.stdin.flush()
        
        # Set a timeout for the process
        start_time = time.time()
        response = ""
        
        while time.time() - start_time < timeout:
            # Check if the process is still running
            if process.poll() is not None:
                break
                
            # Read any available output
            output = process.stdout.readline()
            if output:
                print(output.strip())
                response += output
                
                # Check if we've received a response from the assistant
                if "[assistant]>" in output:
                    logger.info("Received response from assistant")
                    break
            
            # Sleep a bit to avoid high CPU usage
            time.sleep(0.1)
        
        # If we've timed out, terminate the process
        if time.time() - start_time >= timeout:
            logger.warning("Process timed out, terminating")
            process.terminate()
        
        # Get any remaining output
        remaining_output, _ = process.communicate(timeout=2)
        if remaining_output:
            print(remaining_output.strip())
            response += remaining_output
        
        return response
        
    except Exception as e:
        logger.error(f"Error running June command: {e}")
        return None

def test_june_simple():
    """Run a simple test with June."""
    logger.info("Running simple June test...")
    
    # Run June and send a query
    response = run_june_command("Tell me a short joke")
    
    if response:
        logger.info("Test completed successfully")
        return True
    else:
        logger.error("Test failed")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test June voice assistant CLI integration.")
    parser.add_argument("--model", default="gemma3:12b", help="Ollama model to use")
    parser.add_argument("--query", default="Tell me a short joke", help="Query to test with")
    
    args = parser.parse_args()
    
    # Set up June config
    if not setup_june_config(args.model):
        logger.error("Failed to set up June config.")
        return 1
    
    # Run the test
    if args.query:
        success = run_june_command(args.query) is not None
    else:
        success = test_june_simple()
    
    if success:
        logger.info("Test completed successfully.")
        return 0
    else:
        logger.error("Test failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
