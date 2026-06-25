import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GridMetrics:
    tile_size: int
    offset_x: int
    offset_y: int

    def top_left(self, cell: tuple[int, int]) -> tuple[int, int]:
        row, column = cell
        return self.offset_x + column * self.tile_size, self.offset_y + row * self.tile_size

    def center(self, cell: tuple[int, int]) -> tuple[int, int]:
        x, y = self.top_left(cell)
        half = self.tile_size // 2
        return x + half, y + half

    def cell_from_pixel(self, position: tuple[int, int]) -> tuple[int, int]:
        x, y = position
        column = (x - self.offset_x) // self.tile_size
        row = (y - self.offset_y) // self.tile_size
        return int(row), int(column)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def clamp01(value: float) -> float:
    return clamp(value, 0.0, 1.0)


def lerp(start: float, end: float, amount: float) -> float:
    return start + (end - start) * amount


def smoothstep(value: float) -> float:
    value = clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def ease_out_cubic(value: float) -> float:
    value = clamp01(value)
    value -= 1.0
    return value * value * value + 1.0


def ease_in_out_quad(value: float) -> float:
    value = clamp01(value)
    if value < 0.5:
        return 2.0 * value * value
    return 1.0 - pow(-2.0 * value + 2.0, 2.0) / 2.0


def pulse(time_value: float, speed: float = 1.0, low: float = 0.0, high: float = 1.0) -> float:
    wave = (math.sin(time_value * speed) + 1.0) / 2.0
    return lerp(low, high, wave)


def color_lerp(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:
    amount = clamp01(amount)
    return (
        int(lerp(first[0], second[0], amount)),
        int(lerp(first[1], second[1], amount)),
        int(lerp(first[2], second[2], amount)),
    )


def color_add(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    amount: float = 1.0,
) -> tuple[int, int, int]:
    return (
        int(clamp(first[0] + second[0] * amount, 0, 255)),
        int(clamp(first[1] + second[1] * amount, 0, 255)),
        int(clamp(first[2] + second[2] * amount, 0, 255)),
    )


def color_mul(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return (
        int(clamp(color[0] * amount, 0, 255)),
        int(clamp(color[1] * amount, 0, 255)),
        int(clamp(color[2] * amount, 0, 255)),
    )


def distance_squared(first: tuple[float, float], second: tuple[float, float]) -> float:
    dx = first[0] - second[0]
    dy = first[1] - second[1]
    return dx * dx + dy * dy


def distance(first: tuple[float, float], second: tuple[float, float]) -> float:
    return math.sqrt(distance_squared(first, second))


def vector_from_angle(angle: float, length: float) -> tuple[float, float]:
    return math.cos(angle) * length, math.sin(angle) * length


def angle_from_points(center: tuple[float, float], point: tuple[float, float]) -> float:
    angle = math.atan2(point[1] - center[1], point[0] - center[0])
    if angle < 0:
        angle += math.tau
    return angle


def sector_index(angle: float, count: int, offset: float = 0.0) -> int:
    if count <= 0:
        return 0
    return int(((angle + offset) % math.tau) / (math.tau / count))


def sector_points(
    center: tuple[int, int],
    radius: float,
    start_angle: float,
    end_angle: float,
    steps: int = 18,
) -> list[tuple[int, int]]:
    points = [center]
    for step in range(steps + 1):
        amount = step / steps
        angle = lerp(start_angle, end_angle, amount)
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        points.append((round(x), round(y)))
    return points


def move_cell(cell: tuple[int, int], direction: tuple[int, int]) -> tuple[int, int]:
    return cell[0] + direction[0], cell[1] + direction[1]


def rect_center_from_cell(
    cell: tuple[int, int],
    tile_size: int,
    offset: tuple[int, int],
) -> tuple[int, int]:
    row, column = cell
    return (
        offset[0] + column * tile_size + tile_size // 2,
        offset[1] + row * tile_size + tile_size // 2,
    )


def interpolate_cell(
    start: tuple[int, int],
    end: tuple[int, int],
    amount: float,
) -> tuple[float, float]:
    amount = smoothstep(amount)
    return (
        lerp(start[0], end[0], amount),
        lerp(start[1], end[1], amount),
    )


def centered_rect_tuple(center: tuple[int, int], size: int) -> tuple[int, int, int, int]:
    half = size // 2
    return center[0] - half, center[1] - half, size, size


def calculate_level_offset(
    window_width: int,
    window_height: int,
    columns: int,
    rows: int,
    tile_size: int,
    top_margin: int,
) -> tuple[int, int]:
    level_width = columns * tile_size
    level_height = rows * tile_size
    offset_x = (window_width - level_width) // 2
    extra_height = max(0, window_height - top_margin - level_height)
    offset_y = top_margin + extra_height // 2
    return offset_x, offset_y


def direction_name(direction: tuple[int, int] | None) -> str:
    if direction == (-1, 0):
        return "up"
    if direction == (1, 0):
        return "down"
    if direction == (0, -1):
        return "left"
    if direction == (0, 1):
        return "right"
    return "none"


def normalize_vector(vector: tuple[float, float]) -> tuple[float, float]:
    length = math.hypot(vector[0], vector[1])
    if length == 0:
        return 0.0, 0.0
    return vector[0] / length, vector[1] / length


def scale_vector(vector: tuple[float, float], amount: float) -> tuple[float, float]:
    return vector[0] * amount, vector[1] * amount


def add_vectors(first: tuple[float, float], second: tuple[float, float]) -> tuple[float, float]:
    return first[0] + second[0], first[1] + second[1]


def subtract_vectors(first: tuple[float, float], second: tuple[float, float]) -> tuple[float, float]:
    return first[0] - second[0], first[1] - second[1]


def int_point(point: tuple[float, float]) -> tuple[int, int]:
    return round(point[0]), round(point[1])
