import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SETTINGS_FILE_NAME = "settings.json"
APP_FOLDER_NAME = "HUE"


@dataclass
class StoredAudioSettings:
    music_volume: float
    sfx_volume: float
    muted: bool
    music_track: str = "hue_theme"


def config_directory() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_FOLDER_NAME
    return Path.home() / f".{APP_FOLDER_NAME.lower()}"


def settings_path() -> Path:
    return config_directory() / SETTINGS_FILE_NAME


def ensure_config_directory() -> None:
    config_directory().mkdir(parents=True, exist_ok=True)


def load_audio_settings() -> StoredAudioSettings | None:
    data = read_settings_file()
    if not isinstance(data, dict):
        return None

    audio = data.get("audio")
    if not isinstance(audio, dict):
        return None

    music = normalize_volume(audio.get("music_volume"))
    sfx = normalize_volume(audio.get("sfx_volume"))
    muted = audio.get("muted")
    music_track = audio.get("music_track", "hue_theme")

    if music is None or sfx is None or not isinstance(muted, bool):
        return None
    if not isinstance(music_track, str) or not music_track:
        music_track = "hue_theme"

    return StoredAudioSettings(
        music_volume=music,
        sfx_volume=sfx,
        muted=muted,
        music_track=music_track,
    )


def save_audio_settings(
    music_volume: float,
    sfx_volume: float,
    muted: bool,
    music_track: str = "hue_theme",
) -> None:
    data = read_settings_file()
    if not isinstance(data, dict):
        data = {}

    data["audio"] = {
        "music_volume": normalize_volume(music_volume, fallback=0.0),
        "sfx_volume": normalize_volume(sfx_volume, fallback=0.0),
        "muted": bool(muted),
        "music_track": music_track,
    }
    write_settings_file(data)


def load_game_completed() -> bool:
    return load_bool_setting("progress", "game_completed", False)


def save_game_completed(value: bool) -> None:
    save_bool_setting("progress", "game_completed", value)


def load_cat_unlocked() -> bool:
    return load_bool_setting("progress", "cat_unlocked", False)


def save_cat_unlocked(value: bool) -> None:
    save_bool_setting("progress", "cat_unlocked", value)


def load_bool_setting(section: str, key: str, default: bool = False) -> bool:
    data = read_settings_file()
    if not isinstance(data, dict):
        return default
    section_data = data.get(section)
    if not isinstance(section_data, dict):
        return default
    value = section_data.get(key)
    return value if isinstance(value, bool) else default


def save_bool_setting(section: str, key: str, value: bool) -> None:
    data = read_settings_file()
    if not isinstance(data, dict):
        data = {}
    section_data = data.get(section)
    if not isinstance(section_data, dict):
        section_data = {}
    section_data[key] = bool(value)
    data[section] = section_data
    write_settings_file(data)


def read_settings_file() -> dict[str, Any] | None:
    path = settings_path()
    if not path.exists():
        return None

    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text)
    except (OSError, json.JSONDecodeError):
        return None


def write_settings_file(data: dict[str, Any]) -> None:
    try:
        ensure_config_directory()
        settings_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def normalize_volume(value: Any, fallback: float | None = None) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(0.0, min(1.0, number))


def describe_storage() -> str:
    return str(settings_path())
