from dataclasses import dataclass


@dataclass(frozen=True)
class WindowSettings:
    width: int = 1280
    height: int = 720
    min_width: int = 1024
    min_height: int = 640
    title: str = "HUE - головоломка"
    fps: int = 60


@dataclass(frozen=True)
class GameplaySettings:
    tile_size: int = 28
    top_margin: int = 104
    player_size: int = 20
    crate_size: int = 23
    move_duration: float = 0.17
    slow_time_scale: float = 0.18
    input_buffer_seconds: float = 0.18
    hold_step_delay: float = 0.045
    level_finish_delay: float = 0.45
    warning_duration: float = 1.45
    particle_limit: int = 520


@dataclass(frozen=True)
class AudioSettings:
    sample_rate: int = 44100
    bit_depth: int = -16
    channels: int = 2
    buffer_size: int = 512
    default_music_volume: float = 0.42
    default_sfx_volume: float = 0.72
    music_fade_ms: int = 900


@dataclass(frozen=True)
class Palette:
    background: tuple[int, int, int] = (18, 22, 32)
    background_deep: tuple[int, int, int] = (10, 13, 20)
    floor: tuple[int, int, int] = (31, 37, 52)
    floor_alt: tuple[int, int, int] = (37, 43, 59)
    grid: tuple[int, int, int] = (48, 57, 78)
    grid_soft: tuple[int, int, int] = (38, 45, 63)
    text: tuple[int, int, int] = (232, 236, 244)
    muted_text: tuple[int, int, int] = (158, 169, 190)
    panel: tuple[int, int, int] = (28, 34, 49)
    panel_light: tuple[int, int, int] = (47, 57, 80)
    panel_shadow: tuple[int, int, int] = (4, 6, 11)
    player: tuple[int, int, int] = (255, 138, 43)
    player_outline: tuple[int, int, int] = (116, 55, 17)
    player_glow: tuple[int, int, int] = (255, 191, 92)
    black_wall: tuple[int, int, int] = (5, 6, 9)
    black_wall_edge: tuple[int, int, int] = (43, 45, 52)
    finish: tuple[int, int, int] = (42, 216, 105)
    finish_inner: tuple[int, int, int] = (191, 255, 161)
    finish_shadow: tuple[int, int, int] = (18, 74, 42)
    crate: tuple[int, int, int] = (174, 126, 70)
    crate_light: tuple[int, int, int] = (217, 171, 103)
    crate_outline: tuple[int, int, int] = (88, 56, 32)
    plate: tuple[int, int, int] = (216, 178, 65)
    plate_done: tuple[int, int, int] = (75, 209, 121)
    plate_outline: tuple[int, int, int] = (84, 65, 28)
    door: tuple[int, int, int] = (104, 75, 42)
    door_bar: tuple[int, int, int] = (151, 111, 56)
    door_open: tuple[int, int, int] = (81, 97, 82)
    trap: tuple[int, int, int] = (192, 47, 68)
    trap_dark: tuple[int, int, int] = (70, 18, 31)
    arrow_floor: tuple[int, int, int] = (56, 67, 92)
    arrow_mark: tuple[int, int, int] = (178, 190, 218)
    warning: tuple[int, int, int] = (255, 202, 103)
    success: tuple[int, int, int] = (90, 229, 142)
    danger: tuple[int, int, int] = (242, 93, 93)


WINDOW = WindowSettings()
GAMEPLAY = GameplaySettings()
AUDIO = AudioSettings()
PALETTE = Palette()


ACTIVE_RED = "Red"
ACTIVE_BLUE = "Blue"
ACTIVE_YELLOW = "Yellow"
ACTIVE_PURPLE = "Purple"
ACTIVE_COLORS = [ACTIVE_RED, ACTIVE_BLUE, ACTIVE_YELLOW, ACTIVE_PURPLE]

COLOR_LABELS = {
    ACTIVE_RED: "Красный",
    ACTIVE_BLUE: "Синий",
    ACTIVE_YELLOW: "Желтый",
    ACTIVE_PURPLE: "Фиолетовый",
}

COLOR_DATA = {
    ACTIVE_RED: {
        "symbol": "R",
        "color": (232, 73, 73),
        "dark": (112, 29, 36),
        "soft": (255, 150, 140),
    },
    ACTIVE_BLUE: {
        "symbol": "B",
        "color": (55, 133, 245),
        "dark": (18, 57, 133),
        "soft": (141, 191, 255),
    },
    ACTIVE_YELLOW: {
        "symbol": "Y",
        "color": (238, 205, 61),
        "dark": (129, 95, 19),
        "soft": (255, 232, 124),
    },
    ACTIVE_PURPLE: {
        "symbol": "V",
        "color": (165, 91, 236),
        "dark": (77, 38, 122),
        "soft": (211, 169, 255),
    },
}

SYMBOL_TO_COLOR = {data["symbol"]: name for name, data in COLOR_DATA.items()}

TILE_EMPTY = "."
TILE_BLACK_WALL = "#"
TILE_CRATE = "C"
TILE_PLATE = "O"
TILE_DOOR = "D"
TILE_START = "P"
TILE_FINISH = "F"
TILE_TRAP = "X"
TILE_ONE_WAY_UP = "^"
TILE_ONE_WAY_DOWN = "v"
TILE_ONE_WAY_LEFT = "<"
TILE_ONE_WAY_RIGHT = ">"

ONE_WAY_DIRECTIONS = {
    TILE_ONE_WAY_UP: (-1, 0),
    TILE_ONE_WAY_DOWN: (1, 0),
    TILE_ONE_WAY_LEFT: (0, -1),
    TILE_ONE_WAY_RIGHT: (0, 1),
}

STATE_MENU = "menu"
STATE_GAME = "game"
STATE_SETTINGS = "settings"
STATE_LEVEL_SELECT = "level_select"
STATE_WIN = "win"

MENU_START = "Начать игру"
MENU_LEVEL_SELECT = "Выбор уровней"
MENU_SETTINGS = "Настройки звука"
MENU_QUIT = "Выход"
MENU_ITEMS = [MENU_START, MENU_SETTINGS, MENU_QUIT]

CONTROL_HINTS = {
    "menu": "ENTER - выбрать    F11 - полный экран    Выход - пункт меню",
    "game": "SPACE - цвет    R - заново    M - звук    F11 - полный экран    ESC - меню",
    "settings": "Стрелки/WASD - настройка    ENTER/ESC - назад    Мышь - перетащить ползунок",
    "level_select": "ENTER - выбрать уровень    ESC - назад",
    "wheel": "Отпусти SPACE, чтобы выбрать",
    "win": "Нажми ENTER, чтобы вернуться в меню",
}

WARNING_MESSAGES = {
    "moving": "Подожди, пока движение закончится",
    "blocked_switch": "Сначала выйди из стены или убери ящик",
    "blocked_move": "Путь закрыт",
    "crate_blocked": "Ящик некуда толкать",
    "trap_hit": "Ловушка! Возврат к старту",
    "one_way_blocked": "Стрелка пускает только в одну сторону",
}

ROLE_FILE_NAME = "TEAM_ROLES_AND_CODE_EXPLANATION.md"
BUILD_EXCLUDED_FILES = [ROLE_FILE_NAME]


def get_color_rgb(color_name: str) -> tuple[int, int, int]:
    return COLOR_DATA[color_name]["color"]


def get_color_dark(color_name: str) -> tuple[int, int, int]:
    return COLOR_DATA[color_name]["dark"]


def get_color_soft(color_name: str) -> tuple[int, int, int]:
    return COLOR_DATA[color_name]["soft"]


def get_color_label(color_name: str) -> str:
    return COLOR_LABELS.get(color_name, color_name)


def get_color_symbol(color_name: str) -> str:
    return COLOR_DATA[color_name]["symbol"]


def color_from_symbol(symbol: str) -> str | None:
    return SYMBOL_TO_COLOR.get(symbol)


def is_color_symbol(symbol: str) -> bool:
    return symbol in SYMBOL_TO_COLOR


def is_solid_symbol(symbol: str) -> bool:
    return symbol == TILE_BLACK_WALL


def is_dynamic_symbol(symbol: str) -> bool:
    return symbol in SYMBOL_TO_COLOR or symbol in {TILE_DOOR, TILE_CRATE, TILE_TRAP, *ONE_WAY_DIRECTIONS}


def all_tile_symbols() -> set[str]:
    return {
        TILE_EMPTY,
        TILE_BLACK_WALL,
        TILE_CRATE,
        TILE_PLATE,
        TILE_DOOR,
        TILE_START,
        TILE_FINISH,
        TILE_TRAP,
        *ONE_WAY_DIRECTIONS.keys(),
        *SYMBOL_TO_COLOR.keys(),
    }
