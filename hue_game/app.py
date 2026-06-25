import sys

import pygame

from .audio import AudioManager
from .effects import ColorPulse, FadeTransition, FloatingTextLayer, ParticleSystem, ScreenShake
from .geometry import color_lerp, move_cell
from .levels import LEVELS, get_level, get_level_count, validate_all_levels
from .model import LevelEvent, LevelState
from .renderer import GameRenderer, draw_scanlines, draw_vignette
from .settings import (
    ACTIVE_COLORS,
    CONTROL_HINTS,
    GAMEPLAY,
    MENU_LEVEL_SELECT,
    MENU_QUIT,
    MENU_SETTINGS,
    MENU_START,
    PALETTE,
    STATE_GAME,
    STATE_LEVEL_SELECT,
    STATE_MENU,
    STATE_SETTINGS,
    STATE_WIN,
    WINDOW,
    get_color_rgb,
)
from .storage import load_cat_unlocked, load_game_completed, save_cat_unlocked, save_game_completed
from .ui import ColorWheelView, FontBook, MenuView, SettingsView, WinView


class GameApp:
    def __init__(self):
        self._validate_levels()
        AudioManager.pre_init()
        pygame.init()
        pygame.key.set_repeat(0)
        pygame.display.set_caption(WINDOW.title)
        self.screen = pygame.display.set_mode((WINDOW.width, WINDOW.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.window_width, self.window_height = self.screen.get_size()
        self.windowed_size = (WINDOW.width, WINDOW.height)
        self.is_fullscreen = False
        self.audio = AudioManager()

        self.fonts = FontBook.create()
        self.game_completed = load_game_completed()
        self.cat_unlocked = load_cat_unlocked()
        self.menu_view = MenuView()
        self.update_main_menu_items()
        self.menu_view.rebuild(self.screen.get_size())
        self.level_menu_view = MenuView(self.level_select_items(), button_width=520)
        self.level_menu_view.rebuild(self.screen.get_size())
        self.settings_view = SettingsView()
        self.settings_view.rebuild(self.screen.get_size())
        self.win_view = WinView()
        self.color_wheel = ColorWheelView()

        self.level_index = 0
        self.level_state = LevelState(get_level(self.level_index))
        self.level_state.level_number = self.level_index + 1
        self.renderer = GameRenderer(self.fonts)
        self.renderer.set_cat_player(self.cat_unlocked)
        self.renderer.resize(self.screen.get_size(), self.level_state)

        self.particles = ParticleSystem()
        self.floating_text = FloatingTextLayer()
        self.shake = ScreenShake()
        self.fade = FadeTransition()
        self.color_pulse = ColorPulse()

        self.state = STATE_MENU
        self.time_value = 0.0
        self.next_level_pending = False
        self.next_level_timer = 0.0
        self.debug_overlay = False
        self.return_state_after_settings = STATE_MENU
        self.wall_press_timer = 0.0
        self.hold_step_timer = 0.0

    def update_main_menu_items(self) -> None:
        items = [MENU_START]
        if self.game_completed:
            items.append(MENU_LEVEL_SELECT)
        items.extend([MENU_SETTINGS, MENU_QUIT])
        self.menu_view.set_items(items, self.screen.get_size())

    def level_select_items(self) -> list[str]:
        return [f"{index + 1}. {level.name}" for index, level in enumerate(LEVELS)] + ["Назад"]

    def _validate_levels(self) -> None:
        errors = validate_all_levels()
        if errors:
            raise ValueError("\n".join(errors))

    def run(self) -> None:
        while True:
            real_delta_time = self.clock.tick(WINDOW.fps) / 1000
            self.time_value += real_delta_time
            self.handle_events(real_delta_time)
            self.update(real_delta_time)
            self.draw()

    def handle_events(self, delta_time: float) -> None:
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
            elif self.state == STATE_SETTINGS:
                self.handle_settings_event(event)
            elif self.state == STATE_LEVEL_SELECT:
                self.handle_level_select_event(event)
            elif self.state == STATE_WIN:
                self.handle_win_event(event)

    def handle_menu_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.menu_view.move_selection(-1)
                self.audio.play("menu_move")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_view.move_selection(1)
                self.audio.play("menu_move")
            elif event.key == pygame.K_RETURN:
                self.audio.play("menu_confirm")
                self.activate_menu_item(self.menu_view.selected_item())
            elif event.key == pygame.K_ESCAPE:
                self.audio.play("menu_move")

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            item = self.menu_view.handle_mouse_click(event.pos)
            if item is not None:
                self.audio.play("menu_confirm")
                self.activate_menu_item(item)

    def handle_level_select_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.level_menu_view.move_selection(-1)
                self.audio.play("menu_move")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.level_menu_view.move_selection(1)
                self.audio.play("menu_move")
            elif event.key == pygame.K_RETURN:
                self.audio.play("menu_confirm")
                self.activate_level_select_item(self.level_menu_view.selected_item())
            elif event.key == pygame.K_ESCAPE:
                self.state = STATE_MENU
                self.fade.fade_in(280)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            item = self.level_menu_view.handle_mouse_click(event.pos)
            if item is not None:
                self.audio.play("menu_confirm")
                self.activate_level_select_item(item)

    def handle_game_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            direction = self.direction_from_key(event.key)
            if direction is not None:
                self.try_start_manual_step(direction)
            elif event.key == pygame.K_ESCAPE:
                if self.color_wheel.open:
                    self.color_wheel.hide()
                else:
                    self.state = STATE_MENU
                    self.fade.fade_in(520)
            elif event.key == pygame.K_r:
                self.reload_level()
            elif event.key == pygame.K_m:
                self.open_settings(STATE_GAME)
            elif event.key == pygame.K_SPACE:
                self.open_color_wheel()
            elif event.key == pygame.K_F3:
                self.debug_overlay = not self.debug_overlay

        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            self.close_color_wheel(apply_selection=True)

    def try_start_manual_step(self, direction: tuple[int, int]) -> None:
        if self.color_wheel.open or self.level_state.movement.active or self.level_state.complete:
            return
        self.level_state.try_move(direction)
        self.hold_step_timer = GAMEPLAY.hold_step_delay

    def handle_settings_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.close_settings()
            elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                amount = -1 if event.key in (pygame.K_UP, pygame.K_w) else 1
                self.settings_view.move_selection(amount)
                self.audio.play("menu_move")
            elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                amount = -1 if event.key in (pygame.K_LEFT, pygame.K_a) else 1
                self.adjust_selected_setting(amount)
            elif event.key == pygame.K_m:
                self.audio.toggle_mute()
                self.audio.play("menu_confirm")

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            track_direction = self.settings_view.track_click(event.pos)
            if track_direction is not None:
                self.audio.change_music_track(track_direction)
                self.audio.play("menu_confirm")
            else:
                result = self.settings_view.begin_drag(event.pos)
                if result is not None:
                    self.set_volume_from_slider(*result)
                    self.audio.play("menu_move")

        if event.type == pygame.MOUSEMOTION:
            result = self.settings_view.drag(event.pos)
            if result is not None:
                self.set_volume_from_slider(*result)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.settings_view.end_drag()

    def handle_win_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_RETURN:
            self.audio.play("menu_confirm")
            self.state = STATE_MENU
            self.fade.fade_in(520)
        elif event.key == pygame.K_ESCAPE:
            self.state = STATE_MENU
            self.fade.fade_in(520)

    def activate_menu_item(self, item: str) -> None:
        if item == MENU_START:
            self.level_index = 0
            self.load_level(self.level_index)
            self.state = STATE_GAME
            self.fade.fade_in(720)
        elif item == MENU_LEVEL_SELECT:
            self.level_menu_view.set_items(self.level_select_items(), self.screen.get_size())
            self.state = STATE_LEVEL_SELECT
            self.fade.fade_in(360)
        elif item == MENU_SETTINGS:
            self.open_settings(STATE_MENU)
        elif item == MENU_QUIT:
            self.quit_game()

    def activate_level_select_item(self, item: str) -> None:
        if item == "Назад":
            self.state = STATE_MENU
            self.fade.fade_in(280)
            return
        try:
            index = int(item.split(".", 1)[0]) - 1
        except (ValueError, IndexError):
            return
        if 0 <= index < get_level_count():
            self.load_level(index)
            self.state = STATE_GAME
            self.fade.fade_in(520)

    def open_settings(self, return_state: str) -> None:
        if self.color_wheel.open:
            self.color_wheel.hide()
        self.return_state_after_settings = return_state
        self.state = STATE_SETTINGS
        self.settings_view.rebuild(self.screen.get_size())
        self.fade.fade_in(280)

    def close_settings(self) -> None:
        self.state = self.return_state_after_settings
        self.audio.play("menu_confirm")
        self.fade.fade_in(280)

    def adjust_selected_setting(self, amount: int) -> None:
        selected = self.settings_view.selected_key()
        if selected == "track":
            self.audio.change_music_track(amount)
            self.audio.play("menu_confirm")
            return
        volume_step = amount * 0.05
        if selected == "music":
            self.audio.adjust_music_volume(volume_step)
        else:
            self.audio.adjust_sfx_volume(volume_step)
        self.audio.play("menu_move")

    def set_volume_from_slider(self, key: str, value: float) -> None:
        if key == "music":
            self.audio.set_music_volume(value)
        else:
            self.audio.set_sfx_volume(value)

    def resize_window(self, width: int, height: int) -> None:
        width = max(WINDOW.min_width, width)
        height = max(WINDOW.min_height, height)
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.window_width, self.window_height = self.screen.get_size()
        self.windowed_size = self.screen.get_size()
        self.menu_view.rebuild(self.screen.get_size())
        self.level_menu_view.rebuild(self.screen.get_size())
        self.settings_view.rebuild(self.screen.get_size())
        self.renderer.resize(self.screen.get_size(), self.level_state)

    def is_fullscreen_shortcut(self, event: pygame.event.Event) -> bool:
        alt_enter = event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT
        return event.key == pygame.K_F11 or alt_enter

    def toggle_fullscreen(self) -> None:
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.is_fullscreen = False
        else:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.is_fullscreen = True

        self.window_width, self.window_height = self.screen.get_size()
        self.menu_view.rebuild(self.screen.get_size())
        self.level_menu_view.rebuild(self.screen.get_size())
        self.settings_view.rebuild(self.screen.get_size())
        self.renderer.resize(self.screen.get_size(), self.level_state)

    def open_color_wheel(self) -> None:
        if self.level_state.movement.active:
            return
        self.color_wheel.show(self.level_state.active_color)

    def close_color_wheel(self, apply_selection: bool) -> None:
        if not self.color_wheel.open:
            return
        selected = self.color_wheel.hide()
        if not apply_selection:
            return
        previous = self.level_state.active_color
        if self.level_state.try_set_active_color(selected):
            if selected != previous:
                self.on_color_changed(selected)
        else:
            self.audio.play("switch_blocked")

    def on_color_changed(self, color_name: str) -> None:
        center = self.renderer.center_of_cell(self.level_state.player_cell)
        color = get_color_rgb(color_name)
        self.particles.burst(center, color, count=34, speed=(80, 220), radius=(2, 6))
        self.color_pulse.start(color, duration=0.32)
        self.shake.start(strength=2.5, duration=0.12)
        self.audio.play("switch")

    def reload_level(self) -> None:
        self.load_level(self.level_index)
        self.fade.fade_in(520)
        self.shake.start(strength=2.5, duration=0.12)
        self.audio.play("restart")

    def load_level(self, index: int) -> None:
        self.level_index = index
        self.level_state = LevelState(get_level(index))
        self.level_state.level_number = index + 1
        self.renderer.resize(self.screen.get_size(), self.level_state)
        self.particles.clear()
        self.floating_text.texts.clear()
        self.next_level_pending = False
        self.next_level_timer = 0.0
        self.wall_press_timer = 0.0
        self.hold_step_timer = 0.0

    def update(self, real_delta_time: float) -> None:
        self.fade.update(real_delta_time)
        self.shake.update(real_delta_time)
        self.color_pulse.update(real_delta_time)
        self.floating_text.update(real_delta_time)
        if self.state == STATE_LEVEL_SELECT:
            self.level_menu_view.update(pygame.mouse.get_pos(), real_delta_time)
        else:
            self.menu_view.update(pygame.mouse.get_pos(), real_delta_time)

        if self.state == STATE_GAME:
            self.update_game(real_delta_time)

        self.particles.update(real_delta_time)
        self.renderer.update(real_delta_time, self.level_state)

    def update_game(self, real_delta_time: float) -> None:
        wheel_center = (self.window_width // 2, self.window_height // 2)
        self.color_wheel.update(real_delta_time, pygame.mouse.get_pos(), wheel_center)
        game_delta_time = real_delta_time * self.get_time_scale()
        self.update_wall_easter_egg(real_delta_time)
        self.update_held_movement(game_delta_time)
        self.level_state.update(game_delta_time, None)
        self.handle_level_events(self.level_state.consume_events())

        if self.level_state.complete:
            self.next_level_timer += real_delta_time
            if self.next_level_timer >= GAMEPLAY.level_finish_delay and not self.next_level_pending:
                self.next_level_pending = True
                self.advance_level()

    def get_time_scale(self) -> float:
        if self.color_wheel.open:
            return GAMEPLAY.slow_time_scale
        return 1.0

    def get_held_direction(self) -> tuple[int, int] | None:
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

    def update_held_movement(self, delta_time: float) -> None:
        if self.color_wheel.open or self.level_state.complete:
            self.hold_step_timer = 0.0
            return

        direction = self.get_held_direction()
        if direction is None:
            self.hold_step_timer = 0.0
            return

        if self.level_state.movement.active:
            self.hold_step_timer = GAMEPLAY.hold_step_delay
            return

        if self.hold_step_timer > 0:
            self.hold_step_timer = max(0.0, self.hold_step_timer - delta_time)
            return

        moved = self.level_state.try_move(direction)
        self.hold_step_timer = GAMEPLAY.hold_step_delay if moved else 0.16

    def direction_from_key(self, key: int) -> tuple[int, int] | None:
        if key in (pygame.K_a, pygame.K_LEFT):
            return (0, -1)
        if key in (pygame.K_d, pygame.K_RIGHT):
            return (0, 1)
        if key in (pygame.K_w, pygame.K_UP):
            return (-1, 0)
        if key in (pygame.K_s, pygame.K_DOWN):
            return (1, 0)
        return None

    def update_wall_easter_egg(self, delta_time: float) -> None:
        if self.cat_unlocked or self.color_wheel.open or self.level_state.complete:
            self.wall_press_timer = 0.0
            return

        direction = self.get_held_direction()
        if direction is None:
            self.wall_press_timer = 0.0
            return

        target_cell = move_cell(self.level_state.player_cell, direction)
        hits_wall = self.is_easter_egg_wall_target(target_cell)
        if not hits_wall:
            self.wall_press_timer = 0.0
            return

        self.wall_press_timer += delta_time
        if self.wall_press_timer >= 5.0:
            self.unlock_cat_player()

    def is_easter_egg_wall_target(self, cell: tuple[int, int]) -> bool:
        if self.level_state.get_crate_index_at(cell) is not None:
            return False
        return self.level_state.cell_blocks_for_color(cell, self.level_state.active_color)

    def unlock_cat_player(self) -> None:
        if self.cat_unlocked:
            return
        self.cat_unlocked = True
        save_cat_unlocked(True)
        self.renderer.set_cat_player(True)
        center = self.renderer.center_of_cell(self.level_state.player_cell)
        self.particles.burst(center, PALETTE.player_glow, count=44, speed=(90, 210), radius=(2, 5), life=(0.35, 0.9))
        self.floating_text.add("Теперь ты кот!", (center[0], center[1] - 34), PALETTE.success)
        self.audio.play("finish")

    def handle_level_events(self, events: list[LevelEvent]) -> None:
        for event in events:
            if event.name == "player_step_started":
                self.handle_player_step_event(event)
            elif event.name == "crate_pushed":
                self.handle_crate_pushed_event(event)
            elif event.name == "crate_blocked":
                self.handle_blocked_event(event)
            elif event.name == "move_blocked":
                self.handle_blocked_event(event)
            elif event.name == "trap_hit":
                self.handle_trap_event(event)
            elif event.name == "plate_changed":
                self.handle_plate_changed_event(event)
            elif event.name == "door_opened":
                self.handle_door_changed_event(opened=True)
            elif event.name == "door_closed":
                self.handle_door_changed_event(opened=False)
            elif event.name == "finish_reached":
                self.handle_finish_event(event)

    def handle_player_step_event(self, event: LevelEvent) -> None:
        if event.cell is None:
            return
        center = self.renderer.center_of_cell(event.cell)
        self.particles.dust(center, event.direction)
        self.audio.play("step")

    def handle_crate_pushed_event(self, event: LevelEvent) -> None:
        if event.cell is None:
            return
        center = self.renderer.center_of_cell(event.cell)
        self.particles.dust(center, event.direction)
        self.shake.start(strength=1.4, duration=0.08)
        self.audio.play("crate")

    def handle_blocked_event(self, event: LevelEvent) -> None:
        if event.cell is None:
            return
        center = self.renderer.center_of_cell(event.cell)
        self.particles.burst(center, PALETTE.danger, count=8, speed=(20, 80), radius=(1, 3), life=(0.18, 0.35))
        self.shake.start(strength=1.7, duration=0.08)
        self.audio.play("blocked")

    def handle_trap_event(self, event: LevelEvent) -> None:
        if event.cell is None:
            return
        center = self.renderer.center_of_cell(event.cell)
        self.particles.burst(center, PALETTE.danger, count=34, speed=(80, 210), radius=(2, 5), life=(0.22, 0.7))
        self.floating_text.add("Ловушка!", (center[0], center[1] - 34), PALETTE.danger)
        self.shake.start(strength=4.0, duration=0.18)
        self.audio.play("blocked")

    def handle_plate_changed_event(self, event: LevelEvent) -> None:
        pressed = event.payload.get("pressed", 0)
        total = event.payload.get("total", 0)
        color = PALETTE.success if pressed == total else PALETTE.plate
        for plate in self.level_state.plates:
            if plate in self.level_state.crates:
                center = self.renderer.center_of_cell(plate)
                self.particles.burst(center, color, count=12, speed=(30, 90), radius=(1, 4), life=(0.2, 0.55))
        if total:
            position = (self.renderer.level_rect.centerx, self.renderer.level_rect.top - 18)
            self.floating_text.add(f"Плиты: {pressed}/{total}", position, color)
            self.audio.play("plate")

    def handle_door_changed_event(self, opened: bool) -> None:
        color = PALETTE.success if opened else PALETTE.warning
        for door in self.level_state.doors:
            center = self.renderer.center_of_cell(door)
            self.particles.burst(center, color, count=10, speed=(20, 95), radius=(1, 4), life=(0.2, 0.55))
        if opened:
            self.shake.start(strength=2.5, duration=0.12)
            self.audio.play("door_open")
        else:
            self.audio.play("door_close")

    def handle_finish_event(self, event: LevelEvent) -> None:
        if event.cell is None:
            return
        center = self.renderer.center_of_cell(event.cell)
        self.particles.burst(center, PALETTE.finish, count=60, speed=(110, 270), radius=(2, 7), life=(0.4, 1.0))
        self.floating_text.add("Уровень пройден!", (center[0], center[1] - 32), PALETTE.success)
        self.shake.start(strength=3.5, duration=0.18)
        self.audio.play("finish")

    def advance_level(self) -> None:
        if self.level_index + 1 >= get_level_count():
            self.game_completed = True
            save_game_completed(True)
            self.update_main_menu_items()
            self.state = STATE_WIN
            self.fade.fade_in(620)
            return
        self.load_level(self.level_index + 1)
        self.fade.fade_in(620)

    def draw(self) -> None:
        camera_offset = self.shake.offset()
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_GAME:
            self.draw_game(camera_offset)
        elif self.state == STATE_SETTINGS:
            self.draw_settings(camera_offset)
        elif self.state == STATE_LEVEL_SELECT:
            self.draw_level_select()
        elif self.state == STATE_WIN:
            self.draw_win()

        self.color_pulse.draw(self.screen)
        self.fade.draw(self.screen)
        pygame.display.flip()

    def draw_menu(self) -> None:
        self.screen.fill(PALETTE.background)
        self.renderer.draw_background(self.screen, self.level_state)
        self.menu_view.draw(self.screen, self.fonts, self.time_value)
        draw_vignette(self.screen, strength=55)
        draw_scanlines(self.screen, alpha=9)

    def draw_level_select(self) -> None:
        self.screen.fill(PALETTE.background)
        self.renderer.draw_background(self.screen, self.level_state)
        self.level_menu_view.draw(
            self.screen,
            self.fonts,
            self.time_value,
            title_text="Выбор уровней",
            subtitle_text="Открывается после полного прохождения",
            hint_text=CONTROL_HINTS["level_select"],
        )
        draw_vignette(self.screen, strength=55)
        draw_scanlines(self.screen, alpha=9)

    def draw_game(self, camera_offset: tuple[int, int]) -> None:
        self.renderer.draw_game(
            self.screen,
            self.level_state,
            self.particles,
            self.floating_text,
            camera_offset,
        )
        self.color_wheel.draw(self.screen, self.fonts, (self.window_width // 2, self.window_height // 2))
        draw_vignette(self.screen, strength=45)
        draw_scanlines(self.screen, alpha=7)

    def draw_win(self) -> None:
        self.screen.fill(PALETTE.background)
        self.renderer.draw_background(self.screen, self.level_state)
        self.win_view.draw(self.screen, self.fonts, self.time_value)
        draw_vignette(self.screen, strength=60)
        draw_scanlines(self.screen, alpha=8)

    def draw_settings(self, camera_offset: tuple[int, int]) -> None:
        if self.return_state_after_settings == STATE_GAME:
            self.draw_game(camera_offset)
        else:
            self.draw_menu()
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        self.settings_view.draw(
            self.screen,
            self.fonts,
            self.audio.state.music_volume,
            self.audio.state.sfx_volume,
            self.audio.current_track_title(),
            self.audio.state.muted,
            self.audio.status_text(),
        )

    def quit_game(self) -> None:
        self.audio.stop_music()
        pygame.quit()
        sys.exit()


def run() -> None:
    GameApp().run()
