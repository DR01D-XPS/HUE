from dataclasses import dataclass, field

from .geometry import direction_name, move_cell, smoothstep
from .levels import LevelDefinition
from .settings import (
    ACTIVE_COLORS,
    ACTIVE_RED,
    GAMEPLAY,
    ONE_WAY_DIRECTIONS,
    SYMBOL_TO_COLOR,
    TILE_BLACK_WALL,
    TILE_CRATE,
    TILE_DOOR,
    TILE_EMPTY,
    TILE_FINISH,
    TILE_PLATE,
    TILE_START,
    TILE_TRAP,
    WARNING_MESSAGES,
)


@dataclass
class MovingCrate:
    index: int
    start_cell: tuple[int, int]
    end_cell: tuple[int, int]


@dataclass
class MovementState:
    active: bool = False
    timer: float = 0.0
    start_cell: tuple[int, int] = (0, 0)
    end_cell: tuple[int, int] = (0, 0)
    crate: MovingCrate | None = None

    def progress(self) -> float:
        if not self.active:
            return 1.0
        return min(1.0, self.timer / GAMEPLAY.move_duration)

    def eased_progress(self) -> float:
        return smoothstep(self.progress())

    def reset(self, cell: tuple[int, int]) -> None:
        self.active = False
        self.timer = 0.0
        self.start_cell = cell
        self.end_cell = cell
        self.crate = None


@dataclass
class WarningState:
    text: str = ""
    timer: float = 0.0

    def show(self, text: str, duration: float | None = None) -> None:
        self.text = text
        self.timer = GAMEPLAY.warning_duration if duration is None else duration

    def update(self, delta_time: float) -> None:
        self.timer = max(0.0, self.timer - delta_time)

    def is_visible(self) -> bool:
        return self.timer > 0 and bool(self.text)


@dataclass
class InputBuffer:
    direction: tuple[int, int] | None = None
    timer: float = 0.0

    def push(self, direction: tuple[int, int] | None) -> None:
        if direction is None:
            return
        self.direction = direction
        self.timer = GAMEPLAY.input_buffer_seconds

    def update(self, delta_time: float) -> None:
        if self.timer <= 0:
            self.direction = None
            return
        self.timer -= delta_time
        if self.timer <= 0:
            self.direction = None

    def consume(self) -> tuple[int, int] | None:
        direction = self.direction
        self.direction = None
        self.timer = 0.0
        return direction


@dataclass
class LevelEvent:
    name: str
    cell: tuple[int, int] | None = None
    color: str | None = None
    direction: tuple[int, int] | None = None
    payload: dict = field(default_factory=dict)


class LevelState:
    def __init__(self, definition: LevelDefinition):
        self.definition = definition
        self.name = definition.name
        self.subtitle = definition.subtitle
        self.raw_map: list[list[str]] = []
        self.rows = 0
        self.columns = 0
        self.black_walls: list[tuple[int, int]] = []
        self.colored_walls: dict[str, list[tuple[int, int]]] = {color: [] for color in ACTIVE_COLORS}
        self.doors: list[tuple[int, int]] = []
        self.plates: list[tuple[int, int]] = []
        self.traps: list[tuple[int, int]] = []
        self.one_way_cells: dict[tuple[int, int], tuple[int, int]] = {}
        self.crates: list[tuple[int, int]] = []
        self.start_cell = (0, 0)
        self.player_cell = (0, 0)
        self.finish_cell = (0, 0)
        self.active_color = ACTIVE_RED
        self.previous_color = ACTIVE_RED
        self.color_blend = 1.0
        self.move_count = 0
        self.switch_count = 0
        self.complete = False
        self.finish_timer = 0.0
        self.movement = MovementState()
        self.warning = WarningState()
        self.input_buffer = InputBuffer()
        self.events: list[LevelEvent] = []
        self._last_plate_count = 0
        self._last_doors_open = False
        self.load(definition)

    def load(self, definition: LevelDefinition) -> None:
        self.definition = definition
        self.name = definition.name
        self.subtitle = definition.subtitle
        normalized = definition.normalized_map()
        self.raw_map = [list(row) for row in normalized]
        self.rows = len(self.raw_map)
        self.columns = len(self.raw_map[0]) if self.rows else 0
        self.black_walls.clear()
        self.doors.clear()
        self.plates.clear()
        self.traps.clear()
        self.one_way_cells.clear()
        self.crates.clear()
        self.colored_walls = {color: [] for color in ACTIVE_COLORS}
        self.active_color = ACTIVE_RED
        self.previous_color = ACTIVE_RED
        self.color_blend = 1.0
        self.move_count = 0
        self.switch_count = 0
        self.complete = False
        self.finish_timer = 0.0
        self.warning = WarningState()
        self.input_buffer = InputBuffer()
        self.events = [LevelEvent("level_loaded")]

        for row_index, row in enumerate(self.raw_map):
            for column_index, symbol in enumerate(row):
                cell = (row_index, column_index)
                self._parse_symbol(cell, symbol)

        self.movement.reset(self.player_cell)
        self._last_plate_count = self.pressed_plate_count()
        self._last_doors_open = self.are_doors_open()

    def _parse_symbol(self, cell: tuple[int, int], symbol: str) -> None:
        row_index, column_index = cell
        if symbol == TILE_BLACK_WALL:
            self.black_walls.append(cell)
        elif symbol in SYMBOL_TO_COLOR:
            self.colored_walls[SYMBOL_TO_COLOR[symbol]].append(cell)
        elif symbol == TILE_DOOR:
            self.doors.append(cell)
        elif symbol == TILE_PLATE:
            self.plates.append(cell)
        elif symbol == TILE_TRAP:
            self.traps.append(cell)
        elif symbol in ONE_WAY_DIRECTIONS:
            self.one_way_cells[cell] = ONE_WAY_DIRECTIONS[symbol]
        elif symbol == TILE_CRATE:
            self.crates.append(cell)
            self.raw_map[row_index][column_index] = TILE_EMPTY
        elif symbol == TILE_START:
            self.start_cell = cell
            self.player_cell = cell
            self.raw_map[row_index][column_index] = TILE_EMPTY
        elif symbol == TILE_FINISH:
            self.finish_cell = cell
            self.raw_map[row_index][column_index] = TILE_EMPTY

    def update(self, delta_time: float, held_direction: tuple[int, int] | None) -> None:
        self.warning.update(delta_time)
        self.input_buffer.update(delta_time)
        self.color_blend = min(1.0, self.color_blend + delta_time * 7.0)

        if held_direction is not None:
            self.input_buffer.push(held_direction)

        if self.movement.active:
            self._update_movement(delta_time)
        else:
            direction = self.input_buffer.consume()
            if direction is not None:
                self.try_move(direction)

        self._update_level_completion(delta_time)
        self._detect_plate_and_door_changes()

    def _update_movement(self, delta_time: float) -> None:
        self.movement.timer += delta_time
        if self.movement.timer < GAMEPLAY.move_duration:
            return
        self.movement.reset(self.player_cell)
        self.events.append(LevelEvent("player_step_finished", self.player_cell))
        if self.tile_at(self.player_cell) == TILE_TRAP:
            self._trigger_trap()

    def _update_level_completion(self, delta_time: float) -> None:
        if self.complete:
            self.finish_timer += delta_time
            return
        if self.movement.active:
            return
        if self.player_cell == self.finish_cell:
            self.complete = True
            self.finish_timer = 0.0
            self.events.append(LevelEvent("finish_reached", self.finish_cell))

    def _detect_plate_and_door_changes(self) -> None:
        pressed_count = self.pressed_plate_count()
        doors_open = self.are_doors_open()

        if pressed_count != self._last_plate_count:
            self.events.append(
                LevelEvent(
                    "plate_changed",
                    payload={
                        "pressed": pressed_count,
                        "total": len(self.plates),
                    },
                )
            )

        if doors_open != self._last_doors_open:
            self.events.append(LevelEvent("door_opened" if doors_open else "door_closed"))

        self._last_plate_count = pressed_count
        self._last_doors_open = doors_open

    def try_move(self, direction: tuple[int, int]) -> bool:
        if self.complete:
            return False
        if self.movement.active:
            self.input_buffer.push(direction)
            return False

        target_cell = move_cell(self.player_cell, direction)
        crate_index = self.get_crate_index_at(target_cell)

        if crate_index is not None:
            return self._try_push_crate(crate_index, target_cell, direction)

        if self.can_player_enter(target_cell, direction):
            self._start_player_move(target_cell, direction)
            return True

        warning_key = "one_way_blocked" if self.one_way_blocks_direction(target_cell, direction) else "blocked_move"
        self.warning.show(WARNING_MESSAGES[warning_key], 0.55)
        self.events.append(LevelEvent("move_blocked", target_cell, direction=direction))
        return False

    def _try_push_crate(
        self,
        crate_index: int,
        crate_cell: tuple[int, int],
        direction: tuple[int, int],
    ) -> bool:
        crate_target = move_cell(crate_cell, direction)
        if not self.can_crate_move_to(crate_target, direction):
            self.warning.show(WARNING_MESSAGES["crate_blocked"], 0.7)
            self.events.append(LevelEvent("crate_blocked", crate_target, direction=direction))
            return False

        self._start_player_move(crate_cell, direction)
        self.movement.crate = MovingCrate(crate_index, crate_cell, crate_target)
        self.crates[crate_index] = crate_target
        self.events.append(LevelEvent("crate_pushed", crate_target, direction=direction))
        return True

    def _start_player_move(self, target_cell: tuple[int, int], direction: tuple[int, int]) -> None:
        self.movement.active = True
        self.movement.timer = 0.0
        self.movement.start_cell = self.player_cell
        self.movement.end_cell = target_cell
        self.player_cell = target_cell
        self.move_count += 1
        self.events.append(LevelEvent("player_step_started", target_cell, direction=direction))

    def _trigger_trap(self) -> None:
        trap_cell = self.player_cell
        self.player_cell = self.start_cell
        self.movement.reset(self.player_cell)
        self.input_buffer = InputBuffer()
        self.warning.show(WARNING_MESSAGES["trap_hit"], 1.1)
        self.events.append(LevelEvent("trap_hit", trap_cell, payload={"start": self.start_cell}))

    def try_set_active_color(self, color_name: str) -> bool:
        if color_name == self.active_color:
            return True
        if self.movement.active:
            self.warning.show(WARNING_MESSAGES["moving"])
            return False
        if not self.objects_clear_for_color(color_name):
            self.warning.show(WARNING_MESSAGES["blocked_switch"])
            self.events.append(LevelEvent("color_switch_blocked", color=color_name))
            return False

        self.previous_color = self.active_color
        self.active_color = color_name
        self.color_blend = 0.0
        self.switch_count += 1
        self.events.append(LevelEvent("color_changed", self.player_cell, color=color_name))
        return True

    def objects_clear_for_color(self, color_name: str) -> bool:
        if self.cell_blocks_for_color(self.player_cell, color_name):
            return False
        return all(not self.cell_blocks_for_color(crate_cell, color_name) for crate_cell in self.crates)

    def can_player_enter(self, cell: tuple[int, int], direction: tuple[int, int] | None = None) -> bool:
        if self.get_crate_index_at(cell) is not None:
            return False
        return not self.cell_blocks_for_movement(cell, self.active_color, direction)

    def can_crate_move_to(self, cell: tuple[int, int], direction: tuple[int, int] | None = None) -> bool:
        if self.get_crate_index_at(cell) is not None:
            return False
        if self.tile_at(cell) == TILE_TRAP:
            return False
        return not self.cell_blocks_for_movement(cell, self.active_color, direction)

    def cell_blocks_for_movement(
        self,
        cell: tuple[int, int],
        color_name: str,
        direction: tuple[int, int] | None,
    ) -> bool:
        if self.cell_blocks_for_color(cell, color_name):
            return True
        return self.one_way_blocks_direction(cell, direction)

    def one_way_blocks_direction(
        self,
        cell: tuple[int, int],
        direction: tuple[int, int] | None,
    ) -> bool:
        required_direction = self.one_way_cells.get(cell)
        return required_direction is not None and direction is not None and required_direction != direction

    def cell_blocks_for_color(self, cell: tuple[int, int], color_name: str) -> bool:
        tile = self.tile_at(cell)
        if tile == TILE_BLACK_WALL:
            return True
        if tile in SYMBOL_TO_COLOR and SYMBOL_TO_COLOR[tile] != color_name:
            return True
        if tile == TILE_DOOR and not self.are_doors_open():
            return True
        return False

    def tile_at(self, cell: tuple[int, int]) -> str:
        row_index, column_index = cell
        if row_index < 0 or column_index < 0:
            return TILE_BLACK_WALL
        if row_index >= self.rows or column_index >= self.columns:
            return TILE_BLACK_WALL
        return self.raw_map[row_index][column_index]

    def get_crate_index_at(self, cell: tuple[int, int]) -> int | None:
        for index, crate_cell in enumerate(self.crates):
            if crate_cell == cell:
                return index
        return None

    def are_doors_open(self) -> bool:
        return bool(self.plates) and all(plate in self.crates for plate in self.plates)

    def pressed_plate_count(self) -> int:
        return sum(1 for plate in self.plates if plate in self.crates)

    def total_plate_count(self) -> int:
        return len(self.plates)

    def completion_ratio(self) -> float:
        if not self.plates:
            return 1.0
        return self.pressed_plate_count() / len(self.plates)

    def player_visual_cell(self) -> tuple[float, float]:
        if not self.movement.active:
            return float(self.player_cell[0]), float(self.player_cell[1])
        progress = self.movement.eased_progress()
        start_row, start_column = self.movement.start_cell
        end_row, end_column = self.movement.end_cell
        return (
            start_row + (end_row - start_row) * progress,
            start_column + (end_column - start_column) * progress,
        )

    def crate_visual_cell(self, index: int) -> tuple[float, float]:
        moving = self.movement.crate
        if not self.movement.active or moving is None or moving.index != index:
            row, column = self.crates[index]
            return float(row), float(column)
        progress = self.movement.eased_progress()
        start_row, start_column = moving.start_cell
        end_row, end_column = moving.end_cell
        return (
            start_row + (end_row - start_row) * progress,
            start_column + (end_column - start_column) * progress,
        )

    def consume_events(self) -> list[LevelEvent]:
        events = self.events[:]
        self.events.clear()
        return events

    def reset_warning(self) -> None:
        self.warning = WarningState()

    def is_cell_visible_color(self, cell: tuple[int, int]) -> str | None:
        tile = self.tile_at(cell)
        return SYMBOL_TO_COLOR.get(tile)

    def all_blocking_cells(self) -> set[tuple[int, int]]:
        cells = set(self.black_walls)
        if not self.are_doors_open():
            cells.update(self.doors)
        for color_name, color_cells in self.colored_walls.items():
            if color_name != self.active_color:
                cells.update(color_cells)
        return cells

    def all_passable_color_cells(self) -> list[tuple[int, int]]:
        return list(self.colored_walls.get(self.active_color, []))

    def stats(self) -> dict[str, int | str]:
        return {
            "level": self.name,
            "moves": self.move_count,
            "switches": self.switch_count,
            "plates_pressed": self.pressed_plate_count(),
            "plates_total": self.total_plate_count(),
        }

    def debug_grid(self) -> list[str]:
        grid = [row[:] for row in self.raw_map]
        for crate in self.crates:
            row, column = crate
            grid[row][column] = TILE_CRATE
        player_row, player_column = self.player_cell
        finish_row, finish_column = self.finish_cell
        grid[finish_row][finish_column] = TILE_FINISH
        grid[player_row][player_column] = TILE_START
        return ["".join(row) for row in grid]

    def direction_label(self, direction: tuple[int, int] | None) -> str:
        return direction_name(direction)
