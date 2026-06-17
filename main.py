import math
import sys

import pygame


WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 640
MIN_WINDOW_WIDTH = 1024
MIN_WINDOW_HEIGHT = 640
FPS = 60

TILE_SIZE = 28
TOP_MARGIN = 92
PLAYER_SIZE = 20
CRATE_SIZE = 23
MOVE_DURATION = 0.16
SLOW_TIME_SCALE = 0.18

BACKGROUND_COLOR = (18, 22, 32)
FLOOR_COLOR = (31, 37, 52)
GRID_COLOR = (45, 53, 72)
TEXT_COLOR = (232, 236, 244)
MUTED_TEXT_COLOR = (158, 169, 190)
PLAYER_COLOR = (255, 138, 43)
PLAYER_OUTLINE = (116, 55, 17)
BLACK_WALL_COLOR = (5, 6, 9)
FINISH_COLOR = (42, 216, 105)
FINISH_INNER = (191, 255, 161)
CRATE_COLOR = (174, 126, 70)
CRATE_OUTLINE = (88, 56, 32)
PLATE_COLOR = (216, 178, 65)
PLATE_DONE_COLOR = (75, 209, 121)
DOOR_COLOR = (104, 75, 42)
DOOR_OPEN_COLOR = (81, 97, 82)
WARNING_COLOR = (255, 202, 103)

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
        "outline": (112, 29, 36),
    },
    ACTIVE_BLUE: {
        "symbol": "B",
        "color": (55, 133, 245),
        "outline": (18, 57, 133),
    },
    ACTIVE_YELLOW: {
        "symbol": "Y",
        "color": (238, 205, 61),
        "outline": (129, 95, 19),
    },
    ACTIVE_PURPLE: {
        "symbol": "V",
        "color": (165, 91, 236),
        "outline": (77, 38, 122),
    },
}

SYMBOL_TO_COLOR = {data["symbol"]: name for name, data in COLOR_DATA.items()}

TILE_BLACK_WALL = "#"
TILE_CRATE = "C"
TILE_PLATE = "O"
TILE_DOOR = "D"
TILE_START = "P"
TILE_FINISH = "F"

STATE_MENU = "menu"
STATE_GAME = "game"
STATE_WIN = "win"


LEVELS = [
    {
        "name": "Цветной коридор",
        "map": [
            "############################",
            "#P...R.....B.....Y.....V..F#",
            "############################",
        ],
    },
    {
        "name": "Черный лабиринт",
        "map": [
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
    },
    {
        "name": "Первый механизм",
        "map": [
            "############################",
            "#P.....C..O...D...B...Y..F##",
            "#......####...D..###########",
            "#..........................#",
            "############################",
        ],
    },
    {
        "name": "Синий ящик",
        "map": [
            "############################",
            "#P..B..C..O..D......Y....F##",
            "#...#####...D..#############",
            "#.......R................###",
            "############################",
        ],
    },
    {
        "name": "Две плиты",
        "map": [
            "############################",
            "#P..B..C..O..D.....Y.....F##",
            "#...####..D..###############",
            "#...C..O..D.....V....R...###",
            "#.........D..#####.#########",
            "#.........................##",
            "############################",
        ],
    },
    {
        "name": "Призматический замок",
        "map": [
            "##################################",
            "#P..R..C..O..D....B.......########",
            "#.#####.###..D..#####.###.########",
            "#.....#...C..O.....Y...#..########",
            "#####.#.######D#########..########",
            "#.....#....V...D.....C..O.########",
            "#.###########..D..################",
            "#........R....B....Y....V....R.F##",
            "##################################",
        ],
    },
]


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Hue Maze - головоломка")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.window_width, self.window_height = self.screen.get_size()
        self.windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.is_fullscreen = False

        self.title_font = pygame.font.SysFont("arial", 64, bold=True)
        self.large_font = pygame.font.SysFont("arial", 38)
        self.font = pygame.font.SysFont("arial", 24)
        self.small_font = pygame.font.SysFont("arial", 18)

        self.state = STATE_MENU
        self.menu_items = ["Начать игру", "Выход"]
        self.selected_menu_index = 0

        self.level_index = 0
        self.level_name = ""
        self.level_map = []
        self.level_columns = 0
        self.level_rows = 0
        self.level_rect = pygame.Rect(0, 0, 0, 0)
        self.level_offset = (0, 0)

        self.black_walls = []
        self.colored_walls = {color: [] for color in ACTIVE_COLORS}
        self.doors = []
        self.plates = []
        self.crates = []
        self.finish_cell = (0, 0)

        self.active_color = ACTIVE_RED
        self.wheel_open = False
        self.wheel_hover_color = ACTIVE_RED

        self.player_cell = (0, 0)
        self.player_from_cell = (0, 0)
        self.player_to_cell = (0, 0)
        self.player_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.is_moving = False
        self.move_timer = 0.0
        self.moving_crate = None

        self.warning_text = ""
        self.warning_timer = 0.0

    def run(self):
        while True:
            real_delta_time = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(real_delta_time)
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                self.resize_window(event.w, event.h)
                continue

            if event.type == pygame.KEYDOWN and self.is_fullscreen_shortcut(event):
                self.toggle_fullscreen()
                continue

            if self.state == STATE_MENU:
                self.handle_menu_event(event)
            elif self.state == STATE_GAME:
                self.handle_game_event(event)
            elif self.state == STATE_WIN:
                self.handle_win_event(event)

    def is_fullscreen_shortcut(self, event):
        alt_enter = event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT
        return event.key == pygame.K_F11 or alt_enter

    def resize_window(self, width, height):
        width = max(MIN_WINDOW_WIDTH, width)
        height = max(MIN_WINDOW_HEIGHT, height)
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.window_width, self.window_height = self.screen.get_size()
        self.windowed_size = (self.window_width, self.window_height)
        self.recenter_level()

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.is_fullscreen = False
        else:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.is_fullscreen = True

        self.window_width, self.window_height = self.screen.get_size()
        self.recenter_level()

    def handle_menu_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_menu_index = (self.selected_menu_index - 1) % len(self.menu_items)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_menu_index = (self.selected_menu_index + 1) % len(self.menu_items)
            elif event.key == pygame.K_RETURN:
                self.activate_menu_item()
            elif event.key == pygame.K_ESCAPE:
                self.quit_game()

        if event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.get_menu_item_rects()):
                if rect.collidepoint(event.pos):
                    self.selected_menu_index = index

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.get_menu_item_rects()):
                if rect.collidepoint(event.pos):
                    self.selected_menu_index = index
                    self.activate_menu_item()

    def handle_game_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.wheel_open:
                    self.close_color_wheel(apply_selection=False)
                else:
                    self.state = STATE_MENU
            elif event.key == pygame.K_r:
                self.load_level(self.level_index)
            elif event.key == pygame.K_SPACE:
                self.open_color_wheel()

        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            self.close_color_wheel(apply_selection=True)

    def handle_win_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN:
            self.state = STATE_MENU
        elif event.key == pygame.K_ESCAPE:
            self.state = STATE_MENU

    def activate_menu_item(self):
        selected_item = self.menu_items[self.selected_menu_index]
        if selected_item == "Начать игру":
            self.level_index = 0
            self.load_level(self.level_index)
            self.state = STATE_GAME
        elif selected_item == "Выход":
            self.quit_game()

    def load_level(self, level_index):
        level = LEVELS[level_index]
        raw_map = level["map"]
        self.level_name = level["name"]
        self.level_columns = max(len(row) for row in raw_map)
        self.level_rows = len(raw_map)
        self.level_map = [list(row.ljust(self.level_columns, TILE_BLACK_WALL)) for row in raw_map]

        offset_x, offset_y = self.calculate_level_offset(self.level_columns, self.level_rows)
        self.level_offset = (offset_x, offset_y)
        self.level_rect = pygame.Rect(
            offset_x,
            offset_y,
            self.level_columns * TILE_SIZE,
            self.level_rows * TILE_SIZE,
        )

        self.black_walls = []
        self.colored_walls = {color: [] for color in ACTIVE_COLORS}
        self.doors = []
        self.plates = []
        self.crates = []
        self.active_color = ACTIVE_RED
        self.wheel_open = False
        self.wheel_hover_color = self.active_color
        self.warning_text = ""
        self.warning_timer = 0.0
        self.is_moving = False
        self.move_timer = 0.0
        self.moving_crate = None

        for row_index, row in enumerate(self.level_map):
            for column_index, tile in enumerate(row):
                cell = (row_index, column_index)

                if tile == TILE_BLACK_WALL:
                    self.black_walls.append(cell)
                elif tile in SYMBOL_TO_COLOR:
                    self.colored_walls[SYMBOL_TO_COLOR[tile]].append(cell)
                elif tile == TILE_DOOR:
                    self.doors.append(cell)
                elif tile == TILE_PLATE:
                    self.plates.append(cell)
                elif tile == TILE_CRATE:
                    self.crates.append(cell)
                    self.level_map[row_index][column_index] = "."
                elif tile == TILE_START:
                    self.player_cell = cell
                    self.player_from_cell = cell
                    self.player_to_cell = cell
                    self.level_map[row_index][column_index] = "."
                elif tile == TILE_FINISH:
                    self.finish_cell = cell
                    self.level_map[row_index][column_index] = "."

        self.update_player_rect_for_cell(self.player_cell)

    def calculate_level_offset(self, columns, rows):
        level_width = columns * TILE_SIZE
        level_height = rows * TILE_SIZE
        offset_x = (self.window_width - level_width) // 2
        extra_height = max(0, self.window_height - TOP_MARGIN - level_height)
        offset_y = TOP_MARGIN + extra_height // 2
        return offset_x, offset_y

    def recenter_level(self):
        if self.level_columns == 0 or self.level_rows == 0:
            return

        offset_x, offset_y = self.calculate_level_offset(self.level_columns, self.level_rows)
        self.level_offset = (offset_x, offset_y)
        self.level_rect = pygame.Rect(
            offset_x,
            offset_y,
            self.level_columns * TILE_SIZE,
            self.level_rows * TILE_SIZE,
        )
        self.update_player_rect_from_motion()

    def update(self, real_delta_time):
        if self.state != STATE_GAME:
            return

        if self.wheel_open:
            self.update_color_wheel_from_mouse()

        self.warning_timer = max(0.0, self.warning_timer - real_delta_time)
        game_delta_time = real_delta_time * self.get_time_scale()
        self.update_motion(game_delta_time)

        if not self.is_moving:
            self.try_start_player_move()

        if not self.is_moving and self.player_cell == self.finish_cell:
            self.finish_level()

    def get_time_scale(self):
        if self.wheel_open:
            return SLOW_TIME_SCALE
        return 1.0

    def finish_level(self):
        if self.level_index + 1 >= len(LEVELS):
            self.state = STATE_WIN
        else:
            self.level_index += 1
            self.load_level(self.level_index)

    def try_start_player_move(self):
        direction = self.get_input_direction()
        if direction is None:
            return

        target_cell = self.add_cells(self.player_cell, direction)
        crate_index = self.get_crate_index_at(target_cell)

        if crate_index is not None:
            crate_target = self.add_cells(target_cell, direction)
            if self.can_crate_move_to(crate_target):
                self.start_player_move(target_cell)
                self.start_crate_move(crate_index, target_cell, crate_target)
            return

        if self.can_player_enter(target_cell):
            self.start_player_move(target_cell)

    def get_input_direction(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            return (0, -1)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            return (0, 1)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            return (-1, 0)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            return (1, 0)
        return None

    def start_player_move(self, target_cell):
        self.is_moving = True
        self.move_timer = 0.0
        self.player_from_cell = self.player_cell
        self.player_to_cell = target_cell
        self.player_cell = target_cell
        self.update_player_rect_from_motion()

    def start_crate_move(self, crate_index, from_cell, to_cell):
        self.moving_crate = {
            "index": crate_index,
            "from": from_cell,
            "to": to_cell,
        }
        self.crates[crate_index] = to_cell

    def update_motion(self, delta_time):
        if not self.is_moving:
            self.update_player_rect_for_cell(self.player_cell)
            return

        self.move_timer += delta_time
        if self.move_timer >= MOVE_DURATION:
            self.is_moving = False
            self.move_timer = 0.0
            self.moving_crate = None
            self.player_from_cell = self.player_cell
            self.player_to_cell = self.player_cell
            self.update_player_rect_for_cell(self.player_cell)
            return

        self.update_player_rect_from_motion()

    def update_player_rect_from_motion(self):
        if not self.is_moving:
            self.update_player_rect_for_cell(self.player_cell)
            return

        t = self.move_timer / MOVE_DURATION
        t = max(0.0, min(1.0, t))
        eased_t = t * t * (3 - 2 * t)
        x1, y1 = self.cell_center(self.player_from_cell)
        x2, y2 = self.cell_center(self.player_to_cell)
        center_x = x1 + (x2 - x1) * eased_t
        center_y = y1 + (y2 - y1) * eased_t
        self.player_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.player_rect.center = (round(center_x), round(center_y))

    def update_player_rect_for_cell(self, cell):
        self.player_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.player_rect.center = self.cell_center(cell)

    def open_color_wheel(self):
        self.wheel_open = True
        self.wheel_hover_color = self.active_color
        self.update_color_wheel_from_mouse()

    def close_color_wheel(self, apply_selection):
        if not self.wheel_open:
            return

        selected_color = self.wheel_hover_color
        self.wheel_open = False

        if apply_selection:
            self.try_set_active_color(selected_color)

    def update_color_wheel_from_mouse(self):
        center = self.get_wheel_center()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - center[0]
        dy = mouse_y - center[1]

        if dx * dx + dy * dy < 22 * 22:
            return

        angle = math.atan2(dy, dx)
        if angle < 0:
            angle += math.tau

        sector = int(((angle + math.pi / 4) % math.tau) / (math.tau / len(ACTIVE_COLORS)))
        self.wheel_hover_color = ACTIVE_COLORS[sector]

    def try_set_active_color(self, new_color):
        if new_color == self.active_color:
            return
        if self.is_moving:
            self.show_warning("Подожди, пока движение закончится")
            return
        if not self.objects_clear_for_color(new_color):
            self.show_warning("Сначала выйди из стены или убери ящик")
            return

        self.active_color = new_color
        self.warning_text = ""
        self.warning_timer = 0.0

    def objects_clear_for_color(self, color):
        if self.cell_blocks_for_color(self.player_cell, color):
            return False
        for crate_cell in self.crates:
            if self.cell_blocks_for_color(crate_cell, color):
                return False
        return True

    def show_warning(self, text):
        self.warning_text = text
        self.warning_timer = 1.35

    def can_player_enter(self, cell):
        return not self.cell_blocks_for_color(cell, self.active_color) and self.get_crate_index_at(cell) is None

    def can_crate_move_to(self, cell):
        return not self.cell_blocks_for_color(cell, self.active_color) and self.get_crate_index_at(cell) is None

    def cell_blocks_for_color(self, cell, color):
        tile = self.tile_at(cell)
        if tile == TILE_BLACK_WALL:
            return True
        if tile in SYMBOL_TO_COLOR and SYMBOL_TO_COLOR[tile] != color:
            return True
        if tile == TILE_DOOR and not self.are_doors_open():
            return True
        return False

    def tile_at(self, cell):
        row, column = cell
        if row < 0 or column < 0 or row >= self.level_rows or column >= self.level_columns:
            return TILE_BLACK_WALL
        return self.level_map[row][column]

    def get_crate_index_at(self, cell):
        for index, crate_cell in enumerate(self.crates):
            if crate_cell == cell:
                return index
        return None

    def are_doors_open(self):
        return bool(self.plates) and all(plate in self.crates for plate in self.plates)

    def add_cells(self, cell, direction):
        return cell[0] + direction[0], cell[1] + direction[1]

    def cell_top_left(self, cell):
        row, column = cell
        return self.level_offset[0] + column * TILE_SIZE, self.level_offset[1] + row * TILE_SIZE

    def cell_center(self, cell):
        x, y = self.cell_top_left(cell)
        return x + TILE_SIZE // 2, y + TILE_SIZE // 2

    def cell_rect(self, cell, inset=0):
        x, y = self.cell_top_left(cell)
        rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        if inset:
            rect.inflate_ip(-inset * 2, -inset * 2)
        return rect

    def get_crate_rect(self, crate_index):
        crate_cell = self.crates[crate_index]
        rect = pygame.Rect(0, 0, CRATE_SIZE, CRATE_SIZE)

        if self.moving_crate and self.moving_crate["index"] == crate_index:
            t = self.move_timer / MOVE_DURATION
            t = max(0.0, min(1.0, t))
            eased_t = t * t * (3 - 2 * t)
            x1, y1 = self.cell_center(self.moving_crate["from"])
            x2, y2 = self.cell_center(self.moving_crate["to"])
            rect.center = (round(x1 + (x2 - x1) * eased_t), round(y1 + (y2 - y1) * eased_t))
            return rect

        rect.center = self.cell_center(crate_cell)
        return rect

    def draw(self):
        self.screen.fill(self.get_background_color())

        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_GAME:
            self.draw_game()
        elif self.state == STATE_WIN:
            self.draw_win_screen()

        pygame.display.flip()

    def get_background_color(self):
        active = COLOR_DATA[self.active_color]["color"]
        return (
            (BACKGROUND_COLOR[0] * 4 + active[0]) // 5,
            (BACKGROUND_COLOR[1] * 4 + active[1]) // 5,
            (BACKGROUND_COLOR[2] * 4 + active[2]) // 5,
        )

    def draw_menu(self):
        title_surface = self.title_font.render("Hue Maze", True, TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(self.window_width // 2, self.window_height // 2 - 140))
        self.screen.blit(title_surface, title_rect)

        subtitle_surface = self.font.render("Цветовое колесо, ящики, плиты и двери", True, MUTED_TEXT_COLOR)
        subtitle_rect = subtitle_surface.get_rect(center=(self.window_width // 2, self.window_height // 2 - 88))
        self.screen.blit(subtitle_surface, subtitle_rect)

        for index, rect in enumerate(self.get_menu_item_rects()):
            is_selected = index == self.selected_menu_index
            fill_color = (65, 79, 110) if is_selected else (42, 50, 69)
            outline_color = TEXT_COLOR if is_selected else (78, 90, 116)

            pygame.draw.rect(self.screen, fill_color, rect)
            pygame.draw.rect(self.screen, outline_color, rect, 2)

            label = self.font.render(self.menu_items[index], True, TEXT_COLOR)
            label_rect = label.get_rect(center=rect.center)
            self.screen.blit(label, label_rect)

        hint = self.small_font.render("ENTER - выбрать    F11 - полный экран    ESC - выход", True, MUTED_TEXT_COLOR)
        hint_rect = hint.get_rect(center=(self.window_width // 2, self.window_height - 70))
        self.screen.blit(hint, hint_rect)

    def get_menu_item_rects(self):
        rects = []
        start_y = self.window_height // 2
        for index in range(len(self.menu_items)):
            rects.append(pygame.Rect(self.window_width // 2 - 105, start_y + index * 62, 210, 44))
        return rects

    def draw_game(self):
        self.draw_hud()
        self.draw_floor()
        self.draw_plates()
        self.draw_finish()
        self.draw_walls()
        self.draw_doors()
        self.draw_crates()
        self.draw_player()

        if self.wheel_open:
            self.draw_color_wheel()

    def draw_hud(self):
        level_text = self.font.render(f"Уровень {self.level_index + 1}: {self.level_name}", True, TEXT_COLOR)
        self.screen.blit(level_text, (20, 10))

        color_label = self.font.render("Цвет:", True, MUTED_TEXT_COLOR)
        self.screen.blit(color_label, (20, 42))
        self.draw_color_swatch((82, 42), self.active_color, selected=True)

        help_text = self.small_font.render(
            "Удерживай SPACE - колесо цвета    R - заново    F11 - полный экран    ESC - меню",
            True,
            MUTED_TEXT_COLOR,
        )
        self.screen.blit(help_text, (180, 47))

        if self.plates:
            plate_count = sum(1 for plate in self.plates if plate in self.crates)
            plate_text = self.small_font.render(f"Плиты: {plate_count}/{len(self.plates)}", True, TEXT_COLOR)
            plate_rect = plate_text.get_rect(topright=(self.window_width - 20, 14))
            self.screen.blit(plate_text, plate_rect)

        if self.warning_timer > 0:
            warning = self.small_font.render(self.warning_text, True, WARNING_COLOR)
            warning_rect = warning.get_rect(topright=(self.window_width - 20, 45))
            self.screen.blit(warning, warning_rect)

    def draw_color_swatch(self, top_left, color_name, selected=False):
        color = COLOR_DATA[color_name]["color"]
        outline = TEXT_COLOR if selected else COLOR_DATA[color_name]["outline"]
        rect = pygame.Rect(top_left[0], top_left[1], 112, 24)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, outline, rect, 2)
        label = self.small_font.render(COLOR_LABELS[color_name], True, (20, 22, 28))
        label_rect = label.get_rect(center=rect.center)
        self.screen.blit(label, label_rect)

    def draw_floor(self):
        pygame.draw.rect(self.screen, FLOOR_COLOR, self.level_rect)

        for x in range(self.level_rect.left, self.level_rect.right + 1, TILE_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, self.level_rect.top), (x, self.level_rect.bottom))
        for y in range(self.level_rect.top, self.level_rect.bottom + 1, TILE_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (self.level_rect.left, y), (self.level_rect.right, y))

        pygame.draw.rect(self.screen, (107, 121, 154), self.level_rect, 3)

    def draw_plates(self):
        for plate in self.plates:
            is_pressed = plate in self.crates
            rect = self.cell_rect(plate, inset=5)
            pygame.draw.rect(self.screen, PLATE_DONE_COLOR if is_pressed else PLATE_COLOR, rect)
            pygame.draw.rect(self.screen, (84, 65, 28), rect, 2)

    def draw_finish(self):
        rect = self.cell_rect(self.finish_cell, inset=2)
        pygame.draw.rect(self.screen, FINISH_COLOR, rect)
        pygame.draw.rect(self.screen, (19, 94, 51), rect, 2)
        inner_rect = rect.inflate(-10, -10)
        pygame.draw.rect(self.screen, FINISH_INNER, inner_rect)

    def draw_walls(self):
        for wall in self.black_walls:
            rect = self.cell_rect(wall)
            pygame.draw.rect(self.screen, BLACK_WALL_COLOR, rect)
            pygame.draw.rect(self.screen, (43, 45, 52), rect, 2)

        for color_name, cells in self.colored_walls.items():
            for cell in cells:
                self.draw_colored_wall(cell, color_name)

    def draw_colored_wall(self, cell, color_name):
        rect = self.cell_rect(cell)
        color = COLOR_DATA[color_name]["color"]
        outline = COLOR_DATA[color_name]["outline"]

        if color_name == self.active_color:
            self.draw_transparent_rect(rect, (*color, 55))
            pygame.draw.rect(self.screen, outline, rect, 1)
            return

        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, outline, rect, 2)

    def draw_doors(self):
        doors_open = self.are_doors_open()
        for door in self.doors:
            rect = self.cell_rect(door)
            if doors_open:
                self.draw_transparent_rect(rect, (*DOOR_OPEN_COLOR, 80))
                pygame.draw.rect(self.screen, DOOR_OPEN_COLOR, rect, 1)
            else:
                pygame.draw.rect(self.screen, DOOR_COLOR, rect)
                pygame.draw.rect(self.screen, (48, 34, 23), rect, 2)
                bar_rect = rect.inflate(-14, -5)
                pygame.draw.rect(self.screen, (151, 111, 56), bar_rect)

    def draw_crates(self):
        for index, crate in enumerate(self.crates):
            rect = self.get_crate_rect(index)
            pygame.draw.rect(self.screen, CRATE_COLOR, rect)
            pygame.draw.rect(self.screen, CRATE_OUTLINE, rect, 2)
            stripe = rect.inflate(-8, -8)
            pygame.draw.rect(self.screen, (202, 154, 91), stripe, 2)

    def draw_player(self):
        pygame.draw.rect(self.screen, PLAYER_COLOR, self.player_rect)
        pygame.draw.rect(self.screen, PLAYER_OUTLINE, self.player_rect, 2)

    def draw_transparent_rect(self, rect, color):
        surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surface.fill(color)
        self.screen.blit(surface, rect.topleft)

    def draw_color_wheel(self):
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 92))
        self.screen.blit(overlay, (0, 0))

        center = self.get_wheel_center()
        radius = 116
        inner_radius = 43
        sector_size = math.tau / len(ACTIVE_COLORS)

        for index, color_name in enumerate(ACTIVE_COLORS):
            start_angle = index * sector_size - sector_size / 2
            end_angle = start_angle + sector_size
            points = self.make_sector_points(center, radius, start_angle, end_angle)
            color = COLOR_DATA[color_name]["color"]
            pygame.draw.polygon(self.screen, color, points)

            outline_width = 5 if color_name == self.wheel_hover_color else 2
            pygame.draw.lines(self.screen, TEXT_COLOR, True, points[1:], outline_width)

        pygame.draw.circle(self.screen, BACKGROUND_COLOR, center, inner_radius)
        pygame.draw.circle(self.screen, TEXT_COLOR, center, inner_radius, 2)

        label = self.font.render(COLOR_LABELS[self.wheel_hover_color], True, TEXT_COLOR)
        label_rect = label.get_rect(center=center)
        self.screen.blit(label, label_rect)

        hint = self.small_font.render("Отпусти SPACE, чтобы выбрать", True, TEXT_COLOR)
        hint_rect = hint.get_rect(center=(center[0], center[1] + radius + 34))
        self.screen.blit(hint, hint_rect)

    def get_wheel_center(self):
        return self.window_width // 2, self.window_height // 2

    def make_sector_points(self, center, radius, start_angle, end_angle):
        points = [center]
        steps = 18
        for step in range(steps + 1):
            t = step / steps
            angle = start_angle + (end_angle - start_angle) * t
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            points.append((round(x), round(y)))
        return points

    def draw_win_screen(self):
        title_surface = self.title_font.render("Победа!", True, TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(self.window_width // 2, self.window_height // 2 - 70))
        self.screen.blit(title_surface, title_rect)

        hint_surface = self.large_font.render("Нажми ENTER, чтобы вернуться в меню", True, MUTED_TEXT_COLOR)
        hint_rect = hint_surface.get_rect(center=(self.window_width // 2, self.window_height // 2 + 5))
        self.screen.blit(hint_surface, hint_rect)

    def quit_game(self):
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
