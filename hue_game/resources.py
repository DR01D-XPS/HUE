import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return base_path / relative_path


def asset_path(*parts: str) -> Path:
    return resource_path(str(Path("assets", *parts)))


def music_asset(file_name: str) -> Path:
    return asset_path("music", file_name)


def image_asset(file_name: str) -> Path:
    return asset_path("images", file_name)
