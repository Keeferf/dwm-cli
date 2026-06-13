import json
import shutil
from importlib.resources import files
from pathlib import Path
from typing import Dict, Any, Optional

CONFIG_DIR = Path.home() / ".watermark_configs"
CURRENT_PROFILE_FILE = Path.home() / ".watermark_current_profile"
DEFAULT_PROFILE_NAME = "default"
DEFAULT_OUTPUT_DIR = str(Path.home() / "Downloads")

# ----- Locate bundled Roboto font (Python 3.9+ only) -----
def _get_bundled_font_path() -> str:
    """Return absolute path to the bundled Roboto font, or empty string if not found."""
    try:
        font_path = files("dwm_cli") / "assets" / "fonts" / "Roboto-Regular.ttf"
        if font_path.is_file():
            return str(font_path)
    except (OSError, TypeError, AttributeError):
        pass
    # Fallback for development when package is not installed (optional)
    dev_path = Path(__file__).parent.parent / "assets" / "fonts" / "Roboto-Regular.ttf"
    if dev_path.exists():
        return str(dev_path)
    return ""

ROBOTO_FONT_PATH = _get_bundled_font_path()

DEFAULT_CONFIG: Dict[str, Any] = {
    "opacity": 0.5,
    "position": "bottom-right",
    "font": ROBOTO_FONT_PATH,
    "font_size": 36,
    "output_format": "png",
    "output_dir": DEFAULT_OUTPUT_DIR,
    "text_color": "white",
    "scale": 1.0,
}


def _ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _get_profile_path(profile_name: str) -> Path:
    """Return full path to a profile's JSON file."""
    return CONFIG_DIR / f"{profile_name}.json"


def _create_default_profile() -> None:
    """Create default profile with DEFAULT_CONFIG if missing."""
    _ensure_config_dir()
    default_path = _get_profile_path(DEFAULT_PROFILE_NAME)
    if not default_path.exists():
        with open(default_path, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)


def _get_current_profile_name() -> str:
    """Read the currently active profile name, fallback to 'default'."""
    if CURRENT_PROFILE_FILE.exists():
        try:
            name = CURRENT_PROFILE_FILE.read_text().strip()
            if name and _get_profile_path(name).exists():
                return name
        except OSError:
            pass
    return DEFAULT_PROFILE_NAME


def _set_current_profile_name(profile_name: str) -> None:
    """Write the active profile name to the current profile file."""
    CURRENT_PROFILE_FILE.write_text(profile_name)


def load_config(profile_name: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from the specified profile (or current active profile).

    If profile does not exist, fall back to default profile.
    """
    _create_default_profile()

    if profile_name is None:
        profile_name = _get_current_profile_name()

    profile_path = _get_profile_path(profile_name)
    if not profile_path.exists():
        profile_path = _get_profile_path(DEFAULT_PROFILE_NAME)
        profile_name = DEFAULT_PROFILE_NAME

    try:
        with open(profile_path, "r") as f:
            user_config = json.load(f)
    except (json.JSONDecodeError, OSError):
        user_config = {}
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    return config


def save_config(config: Dict[str, Any], profile_name: Optional[str] = None) -> None:
    """Save configuration to the specified profile (or current active profile)."""
    if profile_name is None:
        profile_name = _get_current_profile_name()
    _ensure_config_dir()
    profile_path = _get_profile_path(profile_name)
    with open(profile_path, "w") as f:
        json.dump(config, f, indent=2)


def list_profiles() -> list:
    """Return list of available profile names (without .json extension)."""
    _ensure_config_dir()
    profiles = [p.stem for p in CONFIG_DIR.glob("*.json")]
    if DEFAULT_PROFILE_NAME not in profiles:
        profiles.append(DEFAULT_PROFILE_NAME)
    return sorted(set(profiles))


def create_profile(profile_name: str, source_profile: Optional[str] = None) -> bool:
    """Create a new profile, optionally copying from an existing profile.

    Returns True if successful, False if profile already exists.
    """
    _ensure_config_dir()
    new_path = _get_profile_path(profile_name)
    if new_path.exists():
        return False
    if source_profile:
        src_path = _get_profile_path(source_profile)
        if src_path.exists():
            shutil.copy(src_path, new_path)
            return True
    with open(new_path, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return True


def delete_profile(profile_name: str) -> bool:
    """Delete a profile. Cannot delete the default profile.

    Returns True if deleted successfully, False if profile is default or does not exist.
    """
    if profile_name == DEFAULT_PROFILE_NAME:
        return False
    profile_path = _get_profile_path(profile_name)
    if profile_path.exists():
        profile_path.unlink()
        if _get_current_profile_name() == profile_name:
            switch_profile(DEFAULT_PROFILE_NAME)
        return True
    return False


def switch_profile(profile_name: str) -> bool:
    """Switch the current active profile. Must exist.

    Returns True if switch succeeded, False if profile does not exist.
    """
    if not _get_profile_path(profile_name).exists():
        return False
    _set_current_profile_name(profile_name)
    return True


def get_current_profile_name() -> str:
    """Public helper to get the current profile name."""
    return _get_current_profile_name()