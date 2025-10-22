"""
Configuration Manager for Charlie application.

This module handles loading, parsing, and accessing configuration settings.
"""

import os
import yaml
import logging

logger = logging.getLogger('Charlie.ConfigManager')

class ConfigManager:
    """Manages application configuration settings."""
    
    def __init__(self, config_path=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                Defaults to 'config.yaml' in the application root directory.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'config.yaml'
        )
        self.config = {}
        self.load_config()
        
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as config_file:
                self.config = yaml.safe_load(config_file)
            logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found at {self.config_path}")
            self.config = self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            self.config = self._get_default_config()
        
    def get(self, section, key, default=None):
        """
        Get a configuration value.
        
        Args:
            section (str): Configuration section name.
            key (str): Configuration key name.
            default: Default value to return if key is not found.
            
        Returns:
            The configuration value or default if not found.
        """
        try:
            return self.config.get(section, {}).get(key, default)
        except (KeyError, AttributeError):
            logger.warning(f"Configuration key {section}.{key} not found")
            return default
            
    def get_section(self, section, default=None):
        """
        Get an entire configuration section.
        
        Args:
            section (str): Configuration section name.
            default: Default value to return if section is not found.
            
        Returns:
            The configuration section or default if not found.
        """
        return self.config.get(section, default or {})
        
    def save_config(self):
        """Save current configuration to YAML file."""
        try:
            with open(self.config_path, 'w') as config_file:
                yaml.dump(self.config, config_file, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
    def update(self, section, key, value):
        """
        Update a configuration value.
        
        Args:
            section (str): Configuration section name.
            key (str): Configuration key name.
            value: New value to set.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        return self.save_config()
        
    def _get_default_config(self):
        """Return default configuration settings."""
        return {
            "application": {
                "name": "Charlie",
                "version": "0.1.0",
                "debug_mode": False,
                "log_level": "INFO"
            },
            "user": {
                "username": "default_user",
                "theme": "light",
                "language": "en"
            },
            "features": {
                "advanced_mode": False,
                "notifications": True,
                "auto_update": True
            },
            "services": {
                "timeout_seconds": 30,
                "retry_attempts": 3,
                "base_url": "https://api.example.com/v1"
            }
        }
