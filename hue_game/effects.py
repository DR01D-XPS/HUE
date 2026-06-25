import math
import random
from dataclasses import dataclass

import pygame

from .geometry import clamp01, color_lerp, ease_out_cubic
from .settings import GAMEPLAY, PALETTE


@dataclass
class Particle:
    position: pygame.Vector2
    velocity: pygame.Vector2
    color: tuple[int, int, int]
    radius: float
    life: float
    max_life: float
    gravity: float = 0.0
    drag: float = 0.95

    def update(self, delta_time: float) -> bool:
        self.life -= delta_time
        if self.life <= 0:
            return False
        self.velocity.y += self.gravity * delta_time
        self.position += self.velocity * delta_time
        self.velocity *= pow(self.drag, delta_time * 60.0)
        return True

    def alpha(self) -> int:
        return int(255 * clamp01(self.life / self.max_life))

    def current_radius(self) -> int:
        amount = clamp01(self.life / self.max_life)
        return max(1, round(self.radius * ease_out_cubic(amount)))


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []
        self.random = random.Random(90210)

    def clear(self) -> None:
        self.particles.clear()

    def update(self, delta_time: float) -> None:
        self.particles = [particle for particle in self.particles if particle.update(delta_time)]
        if len(self.particles) > GAMEPLAY.particle_limit:
            self.particles = self.particles[-GAMEPLAY.particle_limit :]

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)) -> None:
        for particle in self.particles:
            radius = particle.current_radius()
            if radius <= 0:
                continue
            alpha = particle.alpha()
            particle_surface = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(
                particle_surface,
                (*particle.color, alpha),
                (radius + 1, radius + 1),
                radius,
            )
            surface.blit(
                particle_surface,
                (
                    particle.position.x - radius + camera_offset[0],
                    particle.position.y - radius + camera_offset[1],
                ),
            )

    def burst(
        self,
        center: tuple[int, int],
        color: tuple[int, int, int],
        count: int = 24,
        speed: tuple[float, float] = (55.0, 170.0),
        radius: tuple[float, float] = (2.0, 5.0),
        life: tuple[float, float] = (0.35, 0.85),
    ) -> None:
        for _ in range(count):
            angle = self.random.random() * math.tau
            velocity_length = self.random.uniform(speed[0], speed[1])
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * velocity_length
            particle_color = color_lerp(color, PALETTE.text, self.random.uniform(0.0, 0.35))
            self.particles.append(
                Particle(
                    position=pygame.Vector2(center),
                    velocity=velocity,
                    color=particle_color,
                    radius=self.random.uniform(radius[0], radius[1]),
                    life=self.random.uniform(life[0], life[1]),
                    max_life=life[1],
                    gravity=self.random.uniform(-10.0, 35.0),
                    drag=0.91,
                )
            )

    def line_sparks(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        count: int = 12,
    ) -> None:
        start_vec = pygame.Vector2(start)
        end_vec = pygame.Vector2(end)
        segment = end_vec - start_vec
        for _ in range(count):
            amount = self.random.random()
            position = start_vec + segment * amount
            angle = self.random.random() * math.tau
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.random.uniform(25, 90)
            self.particles.append(
                Particle(
                    position=position,
                    velocity=velocity,
                    color=color,
                    radius=self.random.uniform(1.5, 3.5),
                    life=self.random.uniform(0.25, 0.55),
                    max_life=0.55,
                    drag=0.88,
                )
            )

    def dust(self, center: tuple[int, int], direction: tuple[int, int] | None = None) -> None:
        base_color = (128, 117, 101)
        direction_vec = pygame.Vector2(0, 0)
        if direction is not None:
            direction_vec = pygame.Vector2(direction[1], direction[0])
        for _ in range(8):
            angle = self.random.random() * math.tau
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.random.uniform(15, 65)
            velocity -= direction_vec * self.random.uniform(30, 80)
            self.particles.append(
                Particle(
                    position=pygame.Vector2(center),
                    velocity=velocity,
                    color=color_lerp(base_color, PALETTE.floor, self.random.random() * 0.35),
                    radius=self.random.uniform(1.0, 3.0),
                    life=self.random.uniform(0.25, 0.6),
                    max_life=0.6,
                    gravity=12,
                    drag=0.83,
                )
            )


class ScreenShake:
    def __init__(self):
        self.timer = 0.0
        self.duration = 0.0
        self.strength = 0.0
        self.random = random.Random(404)

    def start(self, strength: float = 4.0, duration: float = 0.16) -> None:
        self.timer = duration
        self.duration = duration
        self.strength = max(self.strength, strength)

    def update(self, delta_time: float) -> None:
        self.timer = max(0.0, self.timer - delta_time)
        if self.timer == 0:
            self.strength = 0.0

    def offset(self) -> tuple[int, int]:
        if self.timer <= 0 or self.duration <= 0:
            return 0, 0
        amount = self.timer / self.duration
        strength = self.strength * amount * amount
        return (
            round(self.random.uniform(-strength, strength)),
            round(self.random.uniform(-strength, strength)),
        )


class FadeTransition:
    def __init__(self):
        self.alpha = 255
        self.target = 0
        self.speed = 720
        self.active = True
        self.color = (0, 0, 0)

    def fade_in(self, speed: float = 720) -> None:
        self.alpha = 255
        self.target = 0
        self.speed = speed
        self.active = True

    def fade_out(self, speed: float = 720) -> None:
        self.alpha = 0
        self.target = 255
        self.speed = speed
        self.active = True

    def update(self, delta_time: float) -> None:
        if not self.active:
            return
        direction = 1 if self.target > self.alpha else -1
        self.alpha += direction * self.speed * delta_time
        if direction > 0 and self.alpha >= self.target:
            self.alpha = self.target
            self.active = False
        if direction < 0 and self.alpha <= self.target:
            self.alpha = self.target
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        if self.alpha <= 0:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*self.color, int(self.alpha)))
        surface.blit(overlay, (0, 0))


class FloatingText:
    def __init__(
        self,
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int],
        duration: float = 1.0,
    ):
        self.text = text
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(0, -34)
        self.color = color
        self.duration = duration
        self.timer = duration

    def update(self, delta_time: float) -> bool:
        self.timer -= delta_time
        self.position += self.velocity * delta_time
        return self.timer > 0

    def alpha(self) -> int:
        return int(255 * clamp01(self.timer / self.duration))


class FloatingTextLayer:
    def __init__(self):
        self.texts: list[FloatingText] = []

    def add(self, text: str, position: tuple[int, int], color: tuple[int, int, int]) -> None:
        self.texts.append(FloatingText(text, position, color))

    def update(self, delta_time: float) -> None:
        self.texts = [text for text in self.texts if text.update(delta_time)]

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, camera_offset: tuple[int, int]) -> None:
        for floating in self.texts:
            rendered = font.render(floating.text, True, floating.color)
            rendered.set_alpha(floating.alpha())
            rect = rendered.get_rect(
                center=(
                    round(floating.position.x + camera_offset[0]),
                    round(floating.position.y + camera_offset[1]),
                )
            )
            surface.blit(rendered, rect)


class ColorPulse:
    def __init__(self):
        self.timer = 0.0
        self.duration = 0.0
        self.color = PALETTE.text

    def start(self, color: tuple[int, int, int], duration: float = 0.35) -> None:
        self.color = color
        self.timer = duration
        self.duration = duration

    def update(self, delta_time: float) -> None:
        self.timer = max(0.0, self.timer - delta_time)

    def amount(self) -> float:
        if self.duration <= 0:
            return 0.0
        return clamp01(self.timer / self.duration)

    def draw(self, surface: pygame.Surface) -> None:
        amount = self.amount()
        if amount <= 0:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*self.color, int(45 * amount)))
        surface.blit(overlay, (0, 0))
