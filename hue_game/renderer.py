import math

import pygame

from .effects import FloatingTextLayer, ParticleSystem
from .geometry import (
    GridMetrics,
    calculate_level_offset,
    clamp01,
    color_lerp,
    color_mul,
    pulse,
)
from .model import LevelState
from .resources import image_asset
from .settings import (
    ACTIVE_COLORS,
    GAMEPLAY,
    ONE_WAY_DIRECTIONS,
    PALETTE,
    SYMBOL_TO_COLOR,
    TILE_BLACK_WALL,
    TILE_DOOR,
    TILE_TRAP,
    get_color_dark,
    get_color_rgb,
    get_color_soft,
)
from .ui import FontBook, HudView


class GameRenderer:
    def __init__(self, fonts: FontBook):
        self.fonts = fonts
        self.hud = HudView()
        self.metrics = GridMetrics(GAMEPLAY.tile_size, 0, 0)
        self.level_rect = pygame.Rect(0, 0, 0, 0)
        self.time_value = 0.0
        self.background_color = PALETTE.background
        self.previous_background_color = PALETTE.background
        self.active_background_color = PALETTE.background
        self.cat_player = False
        self.cat_surface: pygame.Surface | None = None

    def set_cat_player(self, enabled: bool) -> None:
        self.cat_player = enabled
        if enabled and self.cat_surface is None:
            self.cat_surface = self.load_cat_surface()

    def load_cat_surface(self) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(image_asset("cat.jpg"))).convert()
        except pygame.error:
            return None
        width, height = image.get_size()
        side = min(width, height)
        crop = pygame.Rect((width - side) // 2, (height - side) // 2, side, side)
        cropped = image.subsurface(crop).copy()
        return pygame.transform.smoothscale(cropped, (GAMEPLAY.player_size + 6, GAMEPLAY.player_size + 6))

    def resize(self, screen_size: tuple[int, int], level_state: LevelState) -> None:
        offset = calculate_level_offset(
            screen_size[0],
            screen_size[1],
            level_state.columns,
            level_state.rows,
            GAMEPLAY.tile_size,
            GAMEPLAY.top_margin,
        )
        self.metrics = GridMetrics(GAMEPLAY.tile_size, offset[0], offset[1])
        self.level_rect = pygame.Rect(
            offset[0],
            offset[1],
            level_state.columns * GAMEPLAY.tile_size,
            level_state.rows * GAMEPLAY.tile_size,
        )

    def update(self, delta_time: float, level_state: LevelState) -> None:
        self.time_value += delta_time
        active_color = get_color_rgb(level_state.active_color)
        target = color_lerp(PALETTE.background, active_color, 0.18)
        self.active_background_color = target
        self.background_color = color_lerp(self.background_color, target, min(1.0, delta_time * 5.5))

    def draw_game(
        self,
        surface: pygame.Surface,
        level_state: LevelState,
        particles: ParticleSystem,
        floating_text: FloatingTextLayer,
        camera_offset: tuple[int, int],
    ) -> None:
        self.draw_background(surface, level_state)
        level_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self.draw_level(level_layer, level_state)
        particles.draw(level_layer, camera_offset)
        floating_text.draw(level_layer, self.fonts.small, camera_offset)
        surface.blit(level_layer, camera_offset)
        self.draw_hud(surface, level_state)

    def draw_background(self, surface: pygame.Surface, level_state: LevelState) -> None:
        width, height = surface.get_size()
        for y in range(0, height, 3):
            amount = y / max(1, height)
            color = color_lerp(self.background_color, PALETTE.background_deep, amount * 0.72)
            pygame.draw.rect(surface, color, pygame.Rect(0, y, width, 3))

        active = get_color_rgb(level_state.active_color)
        glow_radius = max(width, height) // 2
        glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*active, 24), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow, (width // 2 - glow_radius, height // 2 - glow_radius), special_flags=0)

    def draw_level(self, surface: pygame.Surface, level_state: LevelState) -> None:
        self.draw_floor(surface, level_state)
        self.draw_mechanisms(surface, level_state)
        self.draw_plates(surface, level_state)
        self.draw_finish(surface, level_state)
        self.draw_walls(surface, level_state)
        self.draw_doors(surface, level_state)
        self.draw_crates(surface, level_state)
        self.draw_player(surface, level_state)

    def draw_floor(self, surface: pygame.Surface, level_state: LevelState) -> None:
        shadow = self.level_rect.move(0, 7)
        pygame.draw.rect(surface, (*PALETTE.panel_shadow, 180), shadow, border_radius=6)
        pygame.draw.rect(surface, PALETTE.floor, self.level_rect, border_radius=4)

        tile = GAMEPLAY.tile_size
        for row in range(level_state.rows):
            for column in range(level_state.columns):
                if (row + column) % 2 == 0:
                    rect = self.cell_rect((row, column))
                    pygame.draw.rect(surface, PALETTE.floor_alt, rect)

        for x in range(self.level_rect.left, self.level_rect.right + 1, tile):
            pygame.draw.line(surface, PALETTE.grid_soft, (x, self.level_rect.top), (x, self.level_rect.bottom))
        for y in range(self.level_rect.top, self.level_rect.bottom + 1, tile):
            pygame.draw.line(surface, PALETTE.grid_soft, (self.level_rect.left, y), (self.level_rect.right, y))

        pygame.draw.rect(surface, (107, 121, 154), self.level_rect, 3, border_radius=4)

    def draw_mechanisms(self, surface: pygame.Surface, level_state: LevelState) -> None:
        for trap in level_state.traps:
            self.draw_trap(surface, trap)
        for cell, direction in level_state.one_way_cells.items():
            self.draw_one_way_arrow(surface, cell, direction)

    def draw_trap(self, surface: pygame.Surface, cell: tuple[int, int]) -> None:
        rect = self.cell_rect(cell, inset=2)
        self.draw_glow(surface, rect.center, PALETTE.trap, 24, 35)
        pygame.draw.rect(surface, PALETTE.trap_dark, rect, border_radius=4)
        pygame.draw.rect(surface, PALETTE.trap, rect, 2, border_radius=4)

        left, top = rect.left + 4, rect.top + 5
        step = max(5, rect.width // 4)
        for index in range(3):
            x = left + index * step
            spike = [
                (x, rect.bottom - 5),
                (x + step // 2, top),
                (x + step, rect.bottom - 5),
            ]
            pygame.draw.polygon(surface, PALETTE.trap, spike)
            pygame.draw.polygon(surface, (255, 154, 154), spike, 1)

    def draw_one_way_arrow(
        self,
        surface: pygame.Surface,
        cell: tuple[int, int],
        direction: tuple[int, int],
    ) -> None:
        rect = self.cell_rect(cell, inset=4)
        pygame.draw.rect(surface, PALETTE.arrow_floor, rect, border_radius=4)
        pygame.draw.rect(surface, (29, 35, 50), rect, 1, border_radius=4)

        cx, cy = rect.center
        length = rect.width // 3
        if direction == ONE_WAY_DIRECTIONS["^"]:
            points = [(cx, cy - length), (cx - length, cy + length // 2), (cx + length, cy + length // 2)]
        elif direction == ONE_WAY_DIRECTIONS["v"]:
            points = [(cx, cy + length), (cx - length, cy - length // 2), (cx + length, cy - length // 2)]
        elif direction == ONE_WAY_DIRECTIONS["<"]:
            points = [(cx - length, cy), (cx + length // 2, cy - length), (cx + length // 2, cy + length)]
        else:
            points = [(cx + length, cy), (cx - length // 2, cy - length), (cx - length // 2, cy + length)]
        pygame.draw.polygon(surface, PALETTE.arrow_mark, points)

    def draw_plates(self, surface: pygame.Surface, level_state: LevelState) -> None:
        for plate in level_state.plates:
            is_pressed = plate in level_state.crates
            rect = self.cell_rect(plate, inset=5)
            color = PALETTE.plate_done if is_pressed else PALETTE.plate
            glow_alpha = 52 if is_pressed else 22
            self.draw_glow(surface, rect.center, color, 26, glow_alpha)
            pygame.draw.rect(surface, color, rect, border_radius=5)
            pygame.draw.rect(surface, PALETTE.plate_outline, rect, 2, border_radius=5)

    def draw_finish(self, surface: pygame.Surface, level_state: LevelState) -> None:
        rect = self.cell_rect(level_state.finish_cell, inset=2)
        glow_radius = round(31 + pulse(self.time_value, speed=3.0, low=-3, high=5))
        self.draw_glow(surface, rect.center, PALETTE.finish, glow_radius, 72)
        pygame.draw.rect(surface, PALETTE.finish, rect, border_radius=5)
        pygame.draw.rect(surface, PALETTE.finish_shadow, rect, 2, border_radius=5)
        inner_rect = rect.inflate(-10, -10)
        pygame.draw.rect(surface, PALETTE.finish_inner, inner_rect, border_radius=3)

    def draw_walls(self, surface: pygame.Surface, level_state: LevelState) -> None:
        for cell in level_state.black_walls:
            self.draw_black_wall(surface, cell)

        for color_name in ACTIVE_COLORS:
            for cell in level_state.colored_walls[color_name]:
                self.draw_colored_wall(surface, cell, color_name, level_state)

    def draw_black_wall(self, surface: pygame.Surface, cell: tuple[int, int]) -> None:
        rect = self.cell_rect(cell)
        pygame.draw.rect(surface, PALETTE.black_wall, rect)
        pygame.draw.rect(surface, PALETTE.black_wall_edge, rect, 2)
        top = pygame.Rect(rect.left + 2, rect.top + 2, rect.width - 4, 4)
        pygame.draw.rect(surface, (25, 27, 34), top)

    def draw_colored_wall(
        self,
        surface: pygame.Surface,
        cell: tuple[int, int],
        color_name: str,
        level_state: LevelState,
    ) -> None:
        rect = self.cell_rect(cell)
        color = get_color_rgb(color_name)
        dark = get_color_dark(color_name)

        if color_name == level_state.active_color:
            alpha = 42 + int(22 * pulse(self.time_value, speed=2.0))
            self.draw_transparent_rect(surface, rect, (*color, alpha))
            pygame.draw.rect(surface, (*dark, 120), rect, 1)
            return

        self.draw_glow(surface, rect.center, color, 21, 24)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, dark, rect, 2)
        highlight = pygame.Rect(rect.left + 3, rect.top + 3, rect.width - 6, 4)
        pygame.draw.rect(surface, get_color_soft(color_name), highlight)

    def draw_doors(self, surface: pygame.Surface, level_state: LevelState) -> None:
        doors_open = level_state.are_doors_open()
        for door in level_state.doors:
            rect = self.cell_rect(door)
            if doors_open:
                self.draw_transparent_rect(surface, rect, (*PALETTE.door_open, 75))
                pygame.draw.rect(surface, PALETTE.door_open, rect, 1)
                continue

            pygame.draw.rect(surface, PALETTE.door, rect, border_radius=2)
            pygame.draw.rect(surface, (48, 34, 23), rect, 2, border_radius=2)
            bar_rect = rect.inflate(-14, -5)
            pygame.draw.rect(surface, PALETTE.door_bar, bar_rect, border_radius=3)

    def draw_crates(self, surface: pygame.Surface, level_state: LevelState) -> None:
        for index, _ in enumerate(level_state.crates):
            rect = self.crate_rect(level_state, index)
            shadow = rect.move(3, 4)
            pygame.draw.rect(surface, (*PALETTE.panel_shadow, 125), shadow, border_radius=5)
            pygame.draw.rect(surface, PALETTE.crate, rect, border_radius=5)
            pygame.draw.rect(surface, PALETTE.crate_outline, rect, 2, border_radius=5)
            stripe = rect.inflate(-8, -8)
            pygame.draw.rect(surface, PALETTE.crate_light, stripe, 2, border_radius=3)
            cross_a = (stripe.left, stripe.top), (stripe.right, stripe.bottom)
            cross_b = (stripe.right, stripe.top), (stripe.left, stripe.bottom)
            pygame.draw.line(surface, PALETTE.crate_outline, *cross_a, 2)
            pygame.draw.line(surface, PALETTE.crate_outline, *cross_b, 2)

    def draw_player(self, surface: pygame.Surface, level_state: LevelState) -> None:
        rect = self.player_rect(level_state)
        glow_radius = round(23 + pulse(self.time_value, speed=4.5, low=-2, high=4))
        self.draw_glow(surface, rect.center, PALETTE.player_glow, glow_radius, 54)
        shadow = rect.move(3, 5)
        pygame.draw.rect(surface, (*PALETTE.panel_shadow, 130), shadow, border_radius=4)
        if self.cat_player and self.cat_surface is not None:
            cat_rect = self.cat_surface.get_rect(center=rect.center)
            surface.blit(self.cat_surface, cat_rect)
            pygame.draw.rect(surface, PALETTE.player_outline, cat_rect, 2, border_radius=5)
            return

        pygame.draw.rect(surface, PALETTE.player, rect, border_radius=4)
        pygame.draw.rect(surface, PALETTE.player_outline, rect, 2, border_radius=4)

        eye_y = rect.top + 6
        pygame.draw.rect(surface, (45, 29, 20), pygame.Rect(rect.left + 5, eye_y, 4, 4), border_radius=2)
        pygame.draw.rect(surface, (45, 29, 20), pygame.Rect(rect.right - 9, eye_y, 4, 4), border_radius=2)

    def draw_hud(self, surface: pygame.Surface, level_state: LevelState) -> None:
        warning = level_state.warning.text if level_state.warning.is_visible() else None
        self.hud.draw(
            surface=surface,
            fonts=self.fonts,
            level_number=self.current_level_number(level_state),
            level_name=level_state.name,
            subtitle=level_state.subtitle,
            active_color=level_state.active_color,
            moves=level_state.move_count,
            switches=level_state.switch_count,
            plate_count=(level_state.pressed_plate_count(), level_state.total_plate_count()),
            warning_text=warning,
        )

    def current_level_number(self, level_state: LevelState) -> int:
        return getattr(level_state, "level_number", 1)

    def cell_rect(self, cell: tuple[int, int], inset: int = 0) -> pygame.Rect:
        x, y = self.metrics.top_left(cell)
        rect = pygame.Rect(x, y, GAMEPLAY.tile_size, GAMEPLAY.tile_size)
        if inset:
            rect.inflate_ip(-inset * 2, -inset * 2)
        return rect

    def visual_cell_center(self, visual_cell: tuple[float, float]) -> tuple[int, int]:
        row, column = visual_cell
        x = self.metrics.offset_x + column * GAMEPLAY.tile_size + GAMEPLAY.tile_size / 2
        y = self.metrics.offset_y + row * GAMEPLAY.tile_size + GAMEPLAY.tile_size / 2
        return round(x), round(y)

    def player_rect(self, level_state: LevelState) -> pygame.Rect:
        center = self.visual_cell_center(level_state.player_visual_cell())
        rect = pygame.Rect(0, 0, GAMEPLAY.player_size, GAMEPLAY.player_size)
        rect.center = center
        return rect

    def crate_rect(self, level_state: LevelState, index: int) -> pygame.Rect:
        center = self.visual_cell_center(level_state.crate_visual_cell(index))
        rect = pygame.Rect(0, 0, GAMEPLAY.crate_size, GAMEPLAY.crate_size)
        rect.center = center
        return rect

    def draw_transparent_rect(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int, int],
    ) -> None:
        tile = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        tile.fill(color)
        surface.blit(tile, rect.topleft)

    def draw_glow(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        color: tuple[int, int, int],
        radius: int,
        alpha: int,
    ) -> None:
        if radius <= 0 or alpha <= 0:
            return
        glow = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, alpha), (radius + 1, radius + 1), radius)
        surface.blit(glow, (center[0] - radius - 1, center[1] - radius - 1))

    def center_of_cell(self, cell: tuple[int, int]) -> tuple[int, int]:
        return self.metrics.center(cell)

    def line_between_cells(
        self,
        start_cell: tuple[int, int],
        end_cell: tuple[int, int],
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        return self.metrics.center(start_cell), self.metrics.center(end_cell)

    def make_color_snapshot(self, level_state: LevelState) -> dict[str, int]:
        return {
            "active_cells": len(level_state.all_passable_color_cells()),
            "blocking_cells": len(level_state.all_blocking_cells()),
            "door_cells": len(level_state.doors),
            "crate_cells": len(level_state.crates),
        }


def draw_vignette(surface: pygame.Surface, strength: int = 90) -> None:
    width, height = surface.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    max_radius = math.hypot(width, height) / 2
    center = (width / 2, height / 2)
    step = 18
    for radius in range(int(max_radius), 0, -step):
        amount = 1.0 - radius / max_radius
        alpha = int(strength * amount * amount)
        pygame.draw.circle(overlay, (0, 0, 0, alpha), center, radius)
    surface.blit(overlay, (0, 0))


def draw_scanlines(surface: pygame.Surface, alpha: int = 18) -> None:
    width, height = surface.get_size()
    line_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(0, height, 4):
        pygame.draw.line(line_surface, (0, 0, 0, alpha), (0, y), (width, y))
    surface.blit(line_surface, (0, 0))


def draw_debug_grid_numbers(
    surface: pygame.Surface,
    fonts: FontBook,
    renderer: GameRenderer,
    level_state: LevelState,
) -> None:
    for row in range(level_state.rows):
        for column in range(level_state.columns):
            cell = (row, column)
            rect = renderer.cell_rect(cell)
            label = fonts.tiny.render(f"{row},{column}", True, color_mul(PALETTE.muted_text, 0.75))
            label_rect = label.get_rect(center=rect.center)
            surface.blit(label, label_rect)
