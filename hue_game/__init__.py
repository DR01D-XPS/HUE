"""HUE package.

The package contains a small pygame puzzle game split into focused modules:
configuration, level data, level state, audio, visual effects, UI, rendering and
app control. The root ``main.py`` file only creates and runs the application.
"""

__all__ = [
    "app",
    "audio",
    "effects",
    "geometry",
    "levels",
    "model",
    "renderer",
    "resources",
    "settings",
    "storage",
    "ui",
]
