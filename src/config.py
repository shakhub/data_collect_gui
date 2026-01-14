import json
import os


# --- CONFIGURATION LOADING ---
def load_config(config_path="config.json"):
    """Load configuration from a JSON file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file {config_path} not found. Using defaults.")
        return {
            "camera": {
                "default_width": 1640,
                "default_height": 1232,
                "display_width": 960,
                "display_height": 540,
                "framerate": "30/1",
                "exposure_min": 13000,
                "exposure_multiplier": 3000000,
                "gain_min": 1.0,
                "gain_max": 1.0,
            },
            "app": {
                "window_title": "Jetson Data Collector Pro",
                "window_geometry": [50, 50, 1100, 800],
                "save_directory": "captured_data",
            },
        }

CONFIG = load_config()
CAM_CONF = CONFIG["camera"]
APP_CONF = CONFIG["app"]

DEFAULT_WIDTH = CAM_CONF["default_width"]
DEFAULT_HEIGHT = CAM_CONF["default_height"]
DISPLAY_WIDTH = CAM_CONF["display_width"]
DISPLAY_HEIGHT = CAM_CONF["display_height"]
