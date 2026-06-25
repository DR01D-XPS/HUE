from dataclasses import dataclass

from .settings import (
    ACTIVE_BLUE,
    ACTIVE_PURPLE,
    ACTIVE_RED,
    ACTIVE_YELLOW,
    TILE_BLACK_WALL,
    TILE_CRATE,
    TILE_DOOR,
    TILE_EMPTY,
    TILE_FINISH,
    TILE_PLATE,
    TILE_START,
    all_tile_symbols,
)


@dataclass(frozen=True)
class LevelDefinition:
    name: str
    map: list[str]
    subtitle: str
    main_color: str = ACTIVE_RED
    par_moves: int = 0
    par_switches: int = 0

    @property
    def width(self) -> int:
        return max(len(row) for row in self.map)

    @property
    def height(self) -> int:
        return len(self.map)

    def normalized_map(self) -> list[str]:
        width = self.width
        return [row.ljust(width, TILE_BLACK_WALL) for row in self.map]


LEVELS = [
    LevelDefinition(
        name="Цветной коридор",
        subtitle="Проведи мышь в сторону нужного цвета и отпусти SPACE.",
        main_color=ACTIVE_RED,
        par_moves=28,
        par_switches=3,
        map=[
            "############################",
            "#P...R.....B.....Y.....V..F#",
            "############################",
        ],
    ),
    LevelDefinition(
        name="Черный лабиринт",
        subtitle="Черные стены не исчезают: цвет помогает только с цветными блоками.",
        main_color=ACTIVE_PURPLE,
        par_moves=46,
        par_switches=1,
        map=[
            "############################",
            "#P...R....#.....B....#....F#",
            "#..###....#..###.....#.#####",
            "#....#....Y....#.....#.....#",
            "####.#.#########.###.#####.#",
            "#....#...........#...V.....#",
            "#.###############.#.######.#",
            "#.................#........#",
            "############################",
        ],
    ),
    LevelDefinition(
        name="Первый механизм",
        subtitle="Ящик нужен обязательно: дверь не откроется, пока плита свободна.",
        main_color=ACTIVE_BLUE,
        par_moves=34,
        par_switches=0,
        map=[
            "############################",
            "#P........D..............F#",
            "#.........D.###############",
            "#..C.O....D...............#",
            "#.........D.###############",
            "#.........D...............#",
            "############################",
        ],
    ),
    LevelDefinition(
        name="Синий ящик",
        subtitle="Чтобы поставить ящик на плиту, сначала сделай синюю стену проходом.",
        main_color=ACTIVE_BLUE,
        par_moves=36,
        par_switches=2,
        map=[
            "############################",
            "#P........D..............F#",
            "#.........D.###############",
            "#..CBO....D.......Y.......#",
            "#.........D.###############",
            "#....R....D...............#",
            "############################",
        ],
    ),
    LevelDefinition(
        name="Две плиты",
        subtitle="Два ящика должны остаться на двух плитах, иначе дверь снова закрыта.",
        main_color=ACTIVE_YELLOW,
        par_moves=48,
        par_switches=3,
        map=[
            "##############################",
            "#P........D...............F#",
            "#..C.O....D.###############",
            "#.........D.......V.......#",
            "#..CYO....D.###############",
            "#.........D...............#",
            "##############################",
        ],
    ),
    LevelDefinition(
        name="Три ключа",
        subtitle="Три линии, три плиты и несколько смен цвета перед финалом.",
        main_color=ACTIVE_PURPLE,
        par_moves=62,
        par_switches=6,
        map=[
            "##################################",
            "#P###########D###################",
            "#..CRO#######D###################",
            "#..##########D###################",
            "#..CBO#######D###################",
            "#..##########D###################",
            "#..CYO#######D###################",
            "#............D....R....B....Y..F#",
            "##################################",
        ],
    ),
    LevelDefinition(
        name="Цветной узел",
        subtitle="Ловушки закрывают ложные ветки, а стрелки не дают просто откатиться назад.",
        main_color=ACTIVE_RED,
        par_moves=62,
        par_switches=4,
        map=[
            "##################################",
            "#P.>>>>>>###########X#############",
            "########v###########X#############",
            "########vXXXX##....V.....#########",
            "########.######.########.#########",
            "###..B...######.########.#########",
            "###.###########.XXXX####.#########",
            "###.XXX########.########.XXXX#####",
            "###.###########.########.#########",
            "###........Y....########.#########",
            "##########X#############.#########",
            "##########.#############...R...F##",
            "##########X#################X#####",
            "############################X#####",
            "##################################",
        ],
    ),
    LevelDefinition(
        name="Два крыла",
        subtitle="Два ящика в разных крыльях: один идёт вправо, другой вниз, а тупики стали ловушками.",
        main_color=ACTIVE_PURPLE,
        par_moves=44,
        par_switches=4,
        map=[
            "####################################",
            "#P.>>XXXXRXXX#######################",
            "####v#######X#######################",
            "####vC.B.>O#X#######################",
            "#########v##XXXXX###################",
            "#########v>>>>Y.>>>###XXXXXX########",
            "##################.###X#############",
            "############XXXXX#C###X#############",
            "################X#.###X#############",
            "################X#V###XXXXXX########",
            "################XX.....#############",
            "##################O###.#############",
            "##################X###.#############",
            "##################XXXX..D....Y...F##",
            "####################################",
        ],
    ),
    LevelDefinition(
        name="Три комнаты с ловушками",
        subtitle="Сложный уровень: три склада, стрелки на важных толчках и ловушки вместо пустых зон.",
        main_color=ACTIVE_BLUE,
        par_moves=82,
        par_switches=4,
        map=[
            "######################################",
            "#P.>>X.>>>>>>>>#######################",
            "####v#.#######.###X###################",
            "####vC.B.>O###v###X###################",
            "##########XXXXvYXXX####X##############",
            "##############v########X##############",
            "##############..>>>>....X#############",
            "##############.########.X#############",
            "##############C###XXXXX..#############",
            "########XXBXXX.#########....##########",
            "########X#####V#########X##.##########",
            "########.#####.######O.Y..C.##########",
            "########X#####O#########.XXXVXXX######",
            "########X#####XXXXXXXX...#############",
            "########XXXXXXXXXXX###.###############",
            "######################........D..R.F##",
            "######################################",
        ],
    ),
    LevelDefinition(
        name="Сердце лабиринта",
        subtitle="Очень сложный хаб: ящики идут вверх, вправо и вниз, а финальная зона полна стрелок.",
        main_color=ACTIVE_PURPLE,
        par_moves=105,
        par_switches=7,
        map=[
            "########################################",
            "######X#################################",
            "######X#################################",
            "###XXXOXXXX#######XXXXXXX#####.>>>V.>###",
            "######^#######################.#####.###",
            "######B###########..C..Y>O####.XXX##.###",
            "######.###########.###########^#####.###",
            "######C###########.XXBXXX#####^#.<B.v###",
            "######.###########.###########^#.#######",
            "##P.>>..>>>>>>..>>..>>>.......D#.#######",
            "######X#######.#################.#######",
            "######X####XXX.XXX############YX.XXX####",
            "###XXXXXRXX###C#################.#######",
            "##############.#################..Y...##",
            "##############V######################.##",
            "##############.#################XXVX#.##",
            "###########XXXOXXXX##################R##",
            "##################################XXXF##",
            "########################################",
        ],
    ),
    LevelDefinition(
        name="Без права на ошибку",
        subtitle="Финальный экзамен: хаб, ловушки, стрелки, три ящика и длинный цветной коридор после двери.",
        main_color=ACTIVE_YELLOW,
        par_moves=122,
        par_switches=13,
        map=[
            "############################################",
            "######X#####################################",
            "######X#####################################",
            "###XXXOXXXX#######XXXXXXX#####.>>>V.>#######",
            "######^#######################.#####.#######",
            "######B###########..C..Y>O####.XXX##.#######",
            "######.###########.###########^#####.#######",
            "######C###########.XXBXXX#####^#.<B.v#######",
            "######.###########.###########^#.###########",
            "##P.>>..>>>>>>..>>..>>>.......D#.###########",
            "######X#######.#################.###########",
            "######X####XXX.XXX############YX.XXX########",
            "###XXXXXRXX###C#################.###########",
            "##############.#################..Y...######",
            "##############V######################.######",
            "##############.#################XXVX#.######",
            "###########XXXOXXXX##################R######",
            "##################################XXXv.B.Y.#",
            "##########################################.#",
            "################################F.V.Y.B.R..#",
            "############################################",
        ],
    ),
]


def get_level(index: int) -> LevelDefinition:
    return LEVELS[index]


def get_level_count() -> int:
    return len(LEVELS)


def iter_levels() -> list[LevelDefinition]:
    return list(LEVELS)


def count_symbol(level: LevelDefinition, symbol: str) -> int:
    return sum(row.count(symbol) for row in level.normalized_map())


def count_crates(level: LevelDefinition) -> int:
    return count_symbol(level, TILE_CRATE)


def count_plates(level: LevelDefinition) -> int:
    return count_symbol(level, TILE_PLATE)


def count_doors(level: LevelDefinition) -> int:
    return count_symbol(level, TILE_DOOR)


def count_colored_walls(level: LevelDefinition) -> int:
    return sum(
        count_symbol(level, symbol)
        for symbol in ["R", "B", "Y", "V"]
    )


def describe_level_stats(level: LevelDefinition) -> dict[str, int]:
    return {
        "width": level.width,
        "height": level.height,
        "crates": count_crates(level),
        "plates": count_plates(level),
        "doors": count_doors(level),
        "colored_walls": count_colored_walls(level),
    }


def validate_level(level: LevelDefinition) -> list[str]:
    errors = []
    allowed = all_tile_symbols()
    normalized = level.normalized_map()
    start_count = count_symbol(level, TILE_START)
    finish_count = count_symbol(level, TILE_FINISH)
    crate_count = count_symbol(level, TILE_CRATE)
    plate_count = count_symbol(level, TILE_PLATE)

    if not normalized:
        errors.append(f"Уровень {level.name}: карта пустая")
    if start_count != 1:
        errors.append(f"Уровень {level.name}: старт P должен быть ровно один")
    if finish_count != 1:
        errors.append(f"Уровень {level.name}: финиш F должен быть ровно один")
    if crate_count != plate_count:
        errors.append(f"Уровень {level.name}: количество ящиков и плит должно совпадать")

    for row_index, row in enumerate(normalized):
        for column_index, symbol in enumerate(row):
            if symbol not in allowed:
                errors.append(
                    f"Уровень {level.name}: неизвестный символ {symbol!r} "
                    f"в клетке {row_index}:{column_index}"
                )

    return errors


def validate_all_levels() -> list[str]:
    errors = []
    for level in LEVELS:
        errors.extend(validate_level(level))
    return errors


def level_has_symbol(level: LevelDefinition, symbol: str) -> bool:
    return any(symbol in row for row in level.normalized_map())


def level_has_crates(level: LevelDefinition) -> bool:
    return level_has_symbol(level, TILE_CRATE)


def level_has_doors(level: LevelDefinition) -> bool:
    return level_has_symbol(level, TILE_DOOR)


def level_has_colored_walls(level: LevelDefinition) -> bool:
    return any(level_has_symbol(level, symbol) for symbol in ["R", "B", "Y", "V"])


def first_cell(level: LevelDefinition, symbol: str) -> tuple[int, int] | None:
    for row_index, row in enumerate(level.normalized_map()):
        column_index = row.find(symbol)
        if column_index != -1:
            return row_index, column_index
    return None


def level_bounds(level: LevelDefinition) -> tuple[int, int]:
    return level.width, level.height


def make_debug_overview() -> list[str]:
    lines = []
    for index, level in enumerate(LEVELS, start=1):
        stats = describe_level_stats(level)
        lines.append(
            f"{index}. {level.name}: "
            f"{stats['width']}x{stats['height']}, "
            f"ящики={stats['crates']}, "
            f"плиты={stats['plates']}, "
            f"двери={stats['doors']}, "
            f"цветные стены={stats['colored_walls']}"
        )
    return lines


def normalize_custom_map(rows: list[str]) -> list[str]:
    if not rows:
        return []
    width = max(len(row) for row in rows)
    return [row.ljust(width, TILE_BLACK_WALL) for row in rows]


def make_level_from_rows(name: str, rows: list[str], subtitle: str = "") -> LevelDefinition:
    normalized = normalize_custom_map(rows)
    return LevelDefinition(
        name=name,
        subtitle=subtitle,
        map=normalized or [TILE_BLACK_WALL],
    )
