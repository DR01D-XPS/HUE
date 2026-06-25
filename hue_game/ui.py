import math
from dataclasses import dataclass

import pygame

from .geometry import angle_from_points, clamp01, color_lerp, pulse, sector_index, sector_points
from .settings import (
    ACTIVE_COLORS,
    CONTROL_HINTS,
    MENU_ITEMS,
    PALETTE,
    COLOR_LABELS,
    get_color_dark,
    get_color_rgb,
)


@dataclass
class FontBook:
    title: pygame.font.Font
    large: pygame.font.Font
    normal: pygame.font.Font
    small: pygame.font.Font
    tiny: pygame.font.Font

    @classmethod
    def create(cls) -> "FontBook":
        return cls(
            title=pygame.font.SysFont("arial", 64, bold=True),
            large=pygame.font.SysFont("arial", 38, bold=False),
            normal=pygame.font.SysFont("arial", 24, bold=False),
            small=pygame.font.SysFont("arial", 18, bold=False),
            tiny=pygame.font.SysFont("arial", 15, bold=False),
        )


class Button:
    def __init__(self, text: str, rect: pygame.Rect):
        self.text = text
        self.rect = rect
        self.hover = False
        self.selected = False
        self.press_timer = 0.0

    def update(self, mouse_pos: tuple[int, int], delta_time: float) -> None:
        self.hover = self.rect.collidepoint(mouse_pos)
        self.press_timer = max(0.0, self.press_timer - delta_time)

    def press(self) -> None:
        self.press_timer = 0.12

    def draw(self, surface: pygame.Surface, fonts: FontBook) -> None:
        active = self.hover or self.selected
        offset = 2 if self.press_timer > 0 else 0
        shadow = self.rect.move(0, 5)
        pygame.draw.rect(surface, PALETTE.panel_shadow, shadow, border_radius=8)

        color = PALETTE.panel_light if active else PALETTE.panel
        outline = PALETTE.text if active else (75, 88, 116)
        rect = self.rect.move(0, offset)
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, outline, rect, 2, border_radius=8)

        label = fonts.normal.render(self.text, True, PALETTE.text)
        label_rect = label.get_rect(center=rect.center)
        surface.blit(label, label_rect)


class MenuView:
    def __init__(self, items: list[str] | None = None, button_width: int = 280):
        self.selected_index = 0
        self.items = items[:] if items is not None else MENU_ITEMS[:]
        self.button_width = button_width
        self.buttons: list[Button] = []
        self.rebuild((0, 0))

    def set_items(self, items: list[str], screen_size: tuple[int, int]) -> None:
        self.items = items[:]
        self.selected_index = min(self.selected_index, max(0, len(self.items) - 1))
        self.rebuild(screen_size)

    def rebuild(self, screen_size: tuple[int, int]) -> None:
        width, height = screen_size
        center_x = width // 2
        self.buttons = []

        if len(self.items) > 8:
            columns = 2 if width >= 860 else 1
            rows_per_column = math.ceil(len(self.items) / columns)
            gap_x = 24
            gap_y = 12 if rows_per_column <= 7 else 8
            button_height = 40 if rows_per_column <= 7 else 34
            column_width = min(
                self.button_width,
                max(280, (width - 96 - (columns - 1) * gap_x) // columns),
            )
            total_width = columns * column_width + (columns - 1) * gap_x
            total_height = rows_per_column * button_height + (rows_per_column - 1) * gap_y
            title_y = height // 2 - 150
            start_x = center_x - total_width // 2
            start_y = min(max(title_y + 96, 92), max(92, height - 106 - total_height))

            for index, text in enumerate(self.items):
                column = index // rows_per_column
                row = index % rows_per_column
                rect = pygame.Rect(
                    start_x + column * (column_width + gap_x),
                    start_y + row * (button_height + gap_y),
                    column_width,
                    button_height,
                )
                button = Button(text, rect)
                button.selected = index == self.selected_index
                self.buttons.append(button)
            return

        start_y = height // 2 - max(0, len(self.items) - 3) * 26
        for index, text in enumerate(self.items):
            rect = pygame.Rect(center_x - self.button_width // 2, start_y + index * 58, self.button_width, 44)
            button = Button(text, rect)
            button.selected = index == self.selected_index
            self.buttons.append(button)

    def move_selection(self, amount: int) -> None:
        self.selected_index = (self.selected_index + amount) % len(self.buttons)
        for index, button in enumerate(self.buttons):
            button.selected = index == self.selected_index

    def update(self, mouse_pos: tuple[int, int], delta_time: float) -> None:
        for index, button in enumerate(self.buttons):
            button.update(mouse_pos, delta_time)
            if button.hover:
                self.selected_index = index
        for index, button in enumerate(self.buttons):
            button.selected = index == self.selected_index

    def handle_mouse_click(self, mouse_pos: tuple[int, int]) -> str | None:
        for index, button in enumerate(self.buttons):
            if button.rect.collidepoint(mouse_pos):
                self.selected_index = index
                button.press()
                return button.text
        return None

    def selected_item(self) -> str:
        return self.items[self.selected_index]

    def draw(
        self,
        surface: pygame.Surface,
        fonts: FontBook,
        time_value: float,
        title_text: str = "HUE",
        subtitle_text: str = "Цвет, ящики, плиты, двери и звук",
        hint_text: str | None = None,
    ) -> None:
        width, height = surface.get_size()
        title_y = height // 2 - 150
        glow_amount = pulse(time_value, speed=2.4, low=0.25, high=0.65)
        glow_color = color_lerp((45, 65, 105), (99, 143, 220), glow_amount)

        for radius, alpha in [(190, 28), (125, 34), (72, 46)]:
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*glow_color, alpha), (radius, radius), radius)
            surface.blit(glow, (width // 2 - radius, title_y - radius // 2))

        title = fonts.title.render(title_text, True, PALETTE.text)
        title_rect = title.get_rect(center=(width // 2, title_y))
        surface.blit(title, title_rect)

        subtitle = fonts.normal.render(subtitle_text, True, PALETTE.muted_text)
        subtitle_rect = subtitle.get_rect(center=(width // 2, title_y + 52))
        surface.blit(subtitle, subtitle_rect)

        for button in self.buttons:
            button.draw(surface, fonts)

        hint = fonts.small.render(hint_text or CONTROL_HINTS["menu"], True, PALETTE.muted_text)
        hint_rect = hint.get_rect(center=(width // 2, height - 58))
        surface.blit(hint, hint_rect)


class HudView:
    def draw(
        self,
        surface: pygame.Surface,
        fonts: FontBook,
        level_number: int,
        level_name: str,
        subtitle: str,
        active_color: str,
        moves: int,
        switches: int,
        plate_count: tuple[int, int],
        warning_text: str | None,
    ) -> None:
        panel = pygame.Rect(16, 12, surface.get_width() - 32, 76)
        pygame.draw.rect(surface, (*PALETTE.panel_shadow, 155), panel.move(0, 3), border_radius=10)
        pygame.draw.rect(surface, PALETTE.panel, panel, border_radius=10)
        pygame.draw.rect(surface, PALETTE.panel_light, panel, 1, border_radius=10)

        title = fonts.normal.render(f"Уровень {level_number}: {level_name}", True, PALETTE.text)
        surface.blit(title, (32, 22))

        subtitle_surface = fonts.tiny.render(subtitle, True, PALETTE.muted_text)
        surface.blit(subtitle_surface, (32, 53))

        color_x = 360
        label = fonts.small.render("Цвет:", True, PALETTE.muted_text)
        surface.blit(label, (color_x, 26))
        self.draw_swatch(surface, fonts, (color_x + 58, 22), active_color, selected=True)

        stats = fonts.small.render(f"Шаги: {moves}    Цвета: {switches}", True, PALETTE.text)
        surface.blit(stats, (color_x + 194, 26))

        if plate_count[1] > 0:
            plates = fonts.small.render(f"Плиты: {plate_count[0]}/{plate_count[1]}", True, PALETTE.text)
            surface.blit(plates, (color_x + 194, 50))

        hint = fonts.tiny.render(CONTROL_HINTS["game"], True, PALETTE.muted_text)
        hint_rect = hint.get_rect(topright=(surface.get_width() - 32, 53))
        surface.blit(hint, hint_rect)

        if warning_text:
            warning = fonts.small.render(warning_text, True, PALETTE.warning)
            warning_rect = warning.get_rect(topright=(surface.get_width() - 32, 24))
            surface.blit(warning, warning_rect)

    def draw_swatch(
        self,
        surface: pygame.Surface,
        fonts: FontBook,
        top_left: tuple[int, int],
        color_name: str,
        selected: bool = False,
    ) -> None:
        rect = pygame.Rect(top_left[0], top_left[1], 116, 28)
        color = get_color_rgb(color_name)
        outline = PALETTE.text if selected else get_color_dark(color_name)
        pygame.draw.rect(surface, color, rect, border_radius=6)
        pygame.draw.rect(surface, outline, rect, 2, border_radius=6)
        text_color = (20, 22, 28)
        label = fonts.small.render(COLOR_LABELS[color_name], True, text_color)
        label_rect = label.get_rect(center=rect.center)
        surface.blit(label, label_rect)


class ColorWheelView:
    def __init__(self):
        self.open = False
        self.hover_color = ACTIVE_COLORS[0]
        self.radius = 125
        self.inner_radius = 44
        self.animation = 0.0

    def show(self, active_color: str) -> None:
        self.open = True
        self.hover_color = active_color
        self.animation = 0.0

    def hide(self) -> str:
        self.open = False
        return self.hover_color

    def update(self, delta_time: float, mouse_pos: tuple[int, int], center: tuple[int, int]) -> None:
        if not self.open:
            self.animation = max(0.0, self.animation - delta_time * 6.0)
            return
        self.animation = min(1.0, self.animation + delta_time * 9.0)
        if (mouse_pos[0] - center[0]) ** 2 + (mouse_pos[1] - center[1]) ** 2 < 24 * 24:
            return
        angle = angle_from_points(center, mouse_pos)
        index = sector_index(angle, len(ACTIVE_COLORS), math.pi / 4)
        self.hover_color = ACTIVE_COLORS[index]

    def draw(self, surface: pygame.Surface, fonts: FontBook, center: tuple[int, int]) -> None:
        if self.animation <= 0:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(105 * self.animation)))
        surface.blit(overlay, (0, 0))

        radius = self.radius * (0.75 + 0.25 * self.animation)
        sector_size = math.tau / len(ACTIVE_COLORS)

        for index, color_name in enumerate(ACTIVE_COLORS):
            start_angle = index * sector_size - sector_size / 2
            end_angle = start_angle + sector_size
            points = sector_points(center, radius, start_angle, end_angle)
            color = get_color_rgb(color_name)
            pygame.draw.polygon(surface, color, points)

            selected = color_name == self.hover_color
            outline_width = 5 if selected else 2
            outline = PALETTE.text if selected else get_color_dark(color_name)
            pygame.draw.lines(surface, outline, True, points[1:], outline_width)

        pygame.draw.circle(surface, PALETTE.background, center, self.inner_radius)
        pygame.draw.circle(surface, PALETTE.text, center, self.inner_radius, 2)

        label = fonts.normal.render(COLOR_LABELS[self.hover_color], True, PALETTE.text)
        label_rect = label.get_rect(center=center)
        surface.blit(label, label_rect)

        hint = fonts.small.render(CONTROL_HINTS["wheel"], True, PALETTE.text)
        hint_rect = hint.get_rect(center=(center[0], center[1] + int(radius) + 36))
        surface.blit(hint, hint_rect)


class SettingsView:
    def __init__(self):
        self.selected_index = 0
        self.dragging_slider: str | None = None
        self.panel_rect = pygame.Rect(0, 0, 760, 560)
        self.track_rect = pygame.Rect(0, 0, 0, 0)
        self.slider_rects: dict[str, pygame.Rect] = {}
        self.rebuild((0, 0))

    def rebuild(self, screen_size: tuple[int, int]) -> None:
        width, height = screen_size
        panel_width = min(760, max(640, width - 180))
        panel_height = min(560, max(500, height - 80))
        self.panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        self.panel_rect.center = (width // 2, height // 2)
        content_left = self.panel_rect.left + 88
        content_width = self.panel_rect.width - 176
        self.track_rect = pygame.Rect(content_left, self.panel_rect.top + 160, content_width, 44)
        self.slider_rects = {
            "music": pygame.Rect(content_left, self.panel_rect.top + 286, content_width, 18),
            "sfx": pygame.Rect(content_left, self.panel_rect.top + 402, content_width, 18),
        }

    def move_selection(self, amount: int) -> None:
        self.selected_index = (self.selected_index + amount) % 3

    def selected_key(self) -> str:
        return ("track", "music", "sfx")[self.selected_index]

    def begin_drag(self, mouse_pos: tuple[int, int]) -> tuple[str, float] | None:
        for index, key in enumerate(("music", "sfx")):
            rect = self.slider_hit_rect(key)
            if rect.collidepoint(mouse_pos):
                self.selected_index = index + 1
                self.dragging_slider = key
                return key, self.value_from_mouse(key, mouse_pos)
        return None

    def track_click(self, mouse_pos: tuple[int, int]) -> int | None:
        if not self.track_rect.inflate(12, 12).collidepoint(mouse_pos):
            return None
        self.selected_index = 0
        if mouse_pos[0] < self.track_rect.centerx:
            return -1
        return 1

    def drag(self, mouse_pos: tuple[int, int]) -> tuple[str, float] | None:
        if self.dragging_slider is None:
            return None
        return self.dragging_slider, self.value_from_mouse(self.dragging_slider, mouse_pos)

    def end_drag(self) -> None:
        self.dragging_slider = None

    def value_from_mouse(self, key: str, mouse_pos: tuple[int, int]) -> float:
        rect = self.slider_rects[key]
        return clamp01((mouse_pos[0] - rect.left) / rect.width)

    def slider_hit_rect(self, key: str) -> pygame.Rect:
        return self.slider_rects[key].inflate(26, 34)

    def draw(
        self,
        surface: pygame.Surface,
        fonts: FontBook,
        music_volume: float,
        sfx_volume: float,
        track_title: str,
        muted: bool,
        status_text: str,
    ) -> None:
        shadow = self.panel_rect.move(0, 8)
        pygame.draw.rect(surface, (*PALETTE.panel_shadow, 180), shadow, border_radius=12)
        draw_panel(surface, self.panel_rect, alpha=242)

        title = fonts.large.render("Настройки звука", True, PALETTE.text)
        surface.blit(title, title.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 52)))

        status_color = PALETTE.warning if muted else PALETTE.muted_text
        status = fonts.small.render(status_text, True, status_color)
        surface.blit(status, status.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 98)))

        self.draw_track_selector(surface, fonts, track_title, self.selected_index == 0)
        self.draw_slider(surface, fonts, "music", "Музыка", music_volume, self.selected_index == 1)
        self.draw_slider(surface, fonts, "sfx", "Эффекты", sfx_volume, self.selected_index == 2)

        mute_text = "M - включить звук" if muted else "M - выключить звук"
        hint = f"{CONTROL_HINTS['settings']}    {mute_text}"
        hint_surface = fonts.tiny.render(hint, True, PALETTE.muted_text)
        hint_rect = hint_surface.get_rect(center=(self.panel_rect.centerx, self.panel_rect.bottom - 34))
        surface.blit(hint_surface, hint_rect)

    def draw_track_selector(
        self,
        surface: pygame.Surface,
        fonts: FontBook,
        track_title: str,
        selected: bool,
    ) -> None:
        label = fonts.normal.render("Трек", True, PALETTE.text)
        surface.blit(label, (self.track_rect.left, self.track_rect.top - 38))

        pygame.draw.rect(surface, (13, 17, 27), self.track_rect, border_radius=8)
        outline = PALETTE.text if selected else PALETTE.panel_light
        pygame.draw.rect(surface, outline, self.track_rect, 2, border_radius=8)

        left_arrow = fonts.normal.render("<", True, PALETTE.muted_text)
        right_arrow = fonts.normal.render(">", True, PALETTE.muted_text)
        surface.blit(left_arrow, left_arrow.get_rect(center=(self.track_rect.left + 24, self.track_rect.centery)))
        surface.blit(right_arrow, right_arrow.get_rect(center=(self.track_rect.right - 24, self.track_rect.centery)))

        title = fonts.small.render(track_title, True, PALETTE.text)
        title_rect = title.get_rect(center=self.track_rect.center)
        max_width = self.track_rect.width - 88
        if title_rect.width > max_width:
            clipped = pygame.Surface((max_width, title_rect.height), pygame.SRCALPHA)
            clipped.blit(title, (0, 0))
            surface.blit(clipped, (self.track_rect.centerx - max_width // 2, title_rect.top))
        else:
            surface.blit(title, title_rect)

    def draw_slider(
        self,
        surface: pygame.Surface,
        fonts: FontBook,
        key: str,
        label_text: str,
        value: float,
        selected: bool,
    ) -> None:
        value = clamp01(value)
        rect = self.slider_rects[key]
        label = fonts.normal.render(label_text, True, PALETTE.text)
        surface.blit(label, (rect.left, rect.top - 46))

        percent = fonts.normal.render(f"{round(value * 100)}%", True, PALETTE.text)
        surface.blit(percent, percent.get_rect(midright=(rect.right, rect.top - 32)))

        pygame.draw.rect(surface, (13, 17, 27), rect, border_radius=9)
        pygame.draw.rect(surface, PALETTE.panel_light, rect, 1, border_radius=9)

        fill_width = max(8, int(rect.width * value))
        fill_rect = pygame.Rect(rect.left, rect.top, fill_width, rect.height)
        fill_color = PALETTE.success if key == "music" else PALETTE.warning
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=9)

        knob_x = rect.left + int(rect.width * value)
        knob_rect = pygame.Rect(0, 0, 30, 30)
        knob_rect.center = (knob_x, rect.centery)
        knob_color = PALETTE.text if selected else PALETTE.muted_text
        pygame.draw.circle(surface, knob_color, knob_rect.center, 15)
        pygame.draw.circle(surface, PALETTE.background_deep, knob_rect.center, 9)

        if selected:
            pygame.draw.rect(surface, PALETTE.text, rect.inflate(12, 20), 2, border_radius=14)


class WinView:
    def draw(self, surface: pygame.Surface, fonts: FontBook, time_value: float) -> None:
        width, height = surface.get_size()
        glow = pulse(time_value, speed=2.0, low=0.25, high=0.75)
        glow_color = color_lerp(PALETTE.finish_shadow, PALETTE.finish, glow)
        for radius, alpha in [(210, 25), (140, 35), (76, 60)]:
            layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(layer, (*glow_color, alpha), (radius, radius), radius)
            surface.blit(layer, (width // 2 - radius, height // 2 - radius - 40))

        title = fonts.title.render("Победа!", True, PALETTE.text)
        title_rect = title.get_rect(center=(width // 2, height // 2 - 72))
        surface.blit(title, title_rect)

        subtitle = fonts.large.render(CONTROL_HINTS["win"], True, PALETTE.muted_text)
        subtitle_rect = subtitle.get_rect(center=(width // 2, height // 2 + 6))
        surface.blit(subtitle, subtitle_rect)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, alpha: int = 230) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*PALETTE.panel, alpha), panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, (*PALETTE.panel_light, alpha), panel.get_rect(), 1, border_radius=10)
    surface.blit(panel, rect.topleft)


def draw_text_with_shadow(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int] = PALETTE.text,
    shadow_color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    shadow = font.render(text, True, shadow_color)
    surface.blit(shadow, (position[0] + 2, position[1] + 2))
    rendered = font.render(text, True, color)
    surface.blit(rendered, position)
