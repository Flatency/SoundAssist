import json
import os

CONFIG_FILE = 'config.json'

DEFAULT_CONFIG = {
    "use_gpu": False,
    "chunk_duration": 1.0,
    "top_k": 3,
    "confidence_threshold": 0.2,
    "enable_radar": False,
    "normalize_audio": False,
    "normalization_threshold": 0.01,
    "apply_hamming": False,
    "show_debug": False,
    "audio_device": None,
    "radar_position": "Bottom Center",
    "radar_size": 300,
    "channel_map": "Standard",
    "show_channel_levels": False
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
