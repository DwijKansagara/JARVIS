import json, os
from pathlib import Path
import platform

_CONFIG_PATH = Path(__file__).parent / "api_keys.json"

def get_config() -> dict:
    if not _CONFIG_PATH.exists():
        return {}
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_os() -> str:
    """Returns: 'windows' | 'mac' | 'linux'"""
    detected = {"Windows": "windows", "Darwin": "mac", "Linux": "linux"}.get(platform.system(), "linux")
    return get_config().get("os_system", detected).lower()

def is_windows() -> bool: return get_os() == "windows"
def is_mac()     -> bool: return get_os() == "mac"
def is_linux()   -> bool: return get_os() == "linux"
