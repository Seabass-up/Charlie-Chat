# pytest unit tests for ConfigManager

import os
import yaml
import tempfile

from src.config_manager import ConfigManager


def test_default_config_load():
    """ConfigManager should load default config when file is missing."""
    # Use a temporary directory without a config.yaml
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily change cwd to the temp dir so ConfigManager looks there
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            cm = ConfigManager()
            # Default config should contain expected keys
            assert cm.get('application', 'name') == 'Charlie'
            assert cm.get('application', 'version') == '0.1.0'
            assert cm.get('features', 'voice_enabled', False) is False  # default does not include voice_enabled
        finally:
            os.chdir(original_cwd)


def test_custom_config_load():
    """ConfigManager should load values from a provided config file."""
    custom_config = {
        'application': {'name': 'TestApp', 'version': '9.9.9', 'log_level': 'DEBUG'},
        'features': {'voice_enabled': True}
    }
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.yaml') as tmpfile:
        yaml.safe_dump(custom_config, tmpfile)
        tmpfile_path = tmpfile.name
    try:
        cm = ConfigManager(config_path=tmpfile_path)
        assert cm.get('application', 'name') == 'TestApp'
        assert cm.get('application', 'version') == '9.9.9'
        assert cm.get('application', 'log_level') == 'DEBUG'
        assert cm.get('features', 'voice_enabled') is True
    finally:
        os.remove(tmpfile_path)
