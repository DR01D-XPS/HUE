import math
from array import array
from dataclasses import dataclass

import pygame

from .resources import music_asset
from .settings import AUDIO
from .storage import load_audio_settings, save_audio_settings


TRACK_HUE_THEME = "hue_theme"


@dataclass(frozen=True)
class MusicTrack:
    key: str
    title: str
    file_name: str | None = None


MUSIC_TRACKS = [
    MusicTrack(TRACK_HUE_THEME, "HUE Theme"),
    MusicTrack("stay_at_your_house", "I Really Want To Stay At Your House", "i_really_want_to_stay_at_your_house.mp3"),
    MusicTrack("spiral", "Spiral", "spiral.mp3"),
    MusicTrack("cruel_angels_thesis", "Cruel Angel's Thesis", "cruel_angels_thesis.mp3"),
]


@dataclass
class AudioState:
    music_volume: float = AUDIO.default_music_volume
    sfx_volume: float = AUDIO.default_sfx_volume
    muted: bool = False
    music_track: str = TRACK_HUE_THEME


class AudioManager:
    def __init__(self):
        self.state = AudioState()
        self._load_state()
        self.available = pygame.mixer.get_init() is not None
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_loop: pygame.mixer.Sound | None = None
        self.music_channel: pygame.mixer.Channel | None = None
        self.sfx_channels: list[pygame.mixer.Channel] = []
        self.next_channel_index = 0

        if self.available:
            pygame.mixer.set_num_channels(16)
            self.music_channel = pygame.mixer.Channel(0)
            self.sfx_channels = [pygame.mixer.Channel(index) for index in range(1, 16)]
            self._build_bank()
            self.start_music()

    @staticmethod
    def pre_init() -> None:
        pygame.mixer.pre_init(
            frequency=AUDIO.sample_rate,
            size=AUDIO.bit_depth,
            channels=AUDIO.channels,
            buffer=AUDIO.buffer_size,
        )

    def _build_bank(self) -> None:
        self.music_loop = build_music_loop()
        self.sounds = {
            "menu_move": build_tone([(420, 0.05), (540, 0.05)], volume=0.35, wave="triangle"),
            "menu_confirm": build_tone([(520, 0.06), (720, 0.08), (920, 0.05)], volume=0.42, wave="triangle"),
            "step": build_noise_hit(duration=0.055, volume=0.17, tone=150, decay=9.0),
            "blocked": build_noise_hit(duration=0.16, volume=0.52, tone=78, decay=7.0),
            "switch": build_sweep(180, 760, duration=0.32, volume=0.48),
            "switch_blocked": build_tone([(170, 0.08), (130, 0.08)], volume=0.42, wave="square"),
            "crate": build_noise_hit(duration=0.18, volume=0.42, tone=115, decay=5.2),
            "plate": build_tone([(360, 0.08), (540, 0.08), (720, 0.08)], volume=0.4, wave="triangle"),
            "door_open": build_sweep(190, 520, duration=0.42, volume=0.42),
            "door_close": build_sweep(420, 140, duration=0.32, volume=0.38),
            "finish": build_tone([(523, 0.10), (659, 0.10), (784, 0.12), (1046, 0.22)], volume=0.48, wave="sine"),
            "restart": build_tone([(260, 0.06), (210, 0.06), (160, 0.08)], volume=0.38, wave="triangle"),
        }
        self.apply_volumes()

    def start_music(self) -> None:
        if not self.available:
            return
        track = self.current_track()
        if track.file_name is None:
            self._start_procedural_music()
        else:
            self._start_file_music(track)
        self.apply_volumes()

    def _start_procedural_music(self) -> None:
        pygame.mixer.music.fadeout(250)
        if self.music_loop is None or self.music_channel is None:
            return
        if self.music_channel.get_busy():
            return
        self.music_channel.play(self.music_loop, loops=-1, fade_ms=AUDIO.music_fade_ms)

    def _start_file_music(self, track: MusicTrack) -> None:
        if self.music_channel is not None:
            self.music_channel.fadeout(250)
        if track.file_name is None:
            return
        try:
            pygame.mixer.music.load(str(music_asset(track.file_name)))
            pygame.mixer.music.play(loops=-1, fade_ms=AUDIO.music_fade_ms)
        except pygame.error:
            self.state.music_track = TRACK_HUE_THEME
            self._start_procedural_music()

    def stop_music(self) -> None:
        if self.music_channel is not None:
            self.music_channel.fadeout(450)
        if self.available:
            pygame.mixer.music.fadeout(450)

    def play(self, name: str) -> None:
        if not self.available or self.state.muted:
            return
        sound = self.sounds.get(name)
        if sound is None or not self.sfx_channels:
            return

        channel = self._next_free_channel()
        channel.set_volume(self.state.sfx_volume)
        channel.play(sound)

    def _next_free_channel(self) -> pygame.mixer.Channel:
        for channel in self.sfx_channels:
            if not channel.get_busy():
                return channel
        channel = self.sfx_channels[self.next_channel_index]
        self.next_channel_index = (self.next_channel_index + 1) % len(self.sfx_channels)
        return channel

    def set_music_volume(self, value: float) -> None:
        self.state.music_volume = clamp01(value)
        self.apply_volumes()
        self._save_state()

    def set_sfx_volume(self, value: float) -> None:
        self.state.sfx_volume = clamp01(value)
        self.apply_volumes()
        self._save_state()

    def set_music_track(self, key: str) -> None:
        if key not in self.track_keys():
            key = TRACK_HUE_THEME
        if key == self.state.music_track:
            return
        self.state.music_track = key
        self.start_music()
        self._save_state()

    def change_music_track(self, amount: int) -> None:
        tracks = MUSIC_TRACKS
        current_index = self.music_track_index()
        next_index = (current_index + amount) % len(tracks)
        self.set_music_track(tracks[next_index].key)

    def adjust_music_volume(self, amount: float) -> None:
        self.set_music_volume(self.state.music_volume + amount)

    def adjust_sfx_volume(self, amount: float) -> None:
        self.set_sfx_volume(self.state.sfx_volume + amount)

    def toggle_mute(self) -> None:
        self.state.muted = not self.state.muted
        self.apply_volumes()
        self._save_state()

    def apply_volumes(self) -> None:
        music_volume = 0.0 if self.state.muted else self.state.music_volume
        sfx_volume = 0.0 if self.state.muted else self.state.sfx_volume
        if self.music_channel is not None:
            self.music_channel.set_volume(music_volume)
        if self.available:
            pygame.mixer.music.set_volume(music_volume)
        for sound in self.sounds.values():
            sound.set_volume(sfx_volume)
        for channel in self.sfx_channels:
            channel.set_volume(sfx_volume)

    def music_percent(self) -> int:
        return round(self.state.music_volume * 100)

    def sfx_percent(self) -> int:
        return round(self.state.sfx_volume * 100)

    def status_text(self) -> str:
        if not self.available:
            return "Аудио недоступно"
        if self.state.muted:
            return "Звук выключен"
        return f"Музыка {self.music_percent()}%   Эффекты {self.sfx_percent()}%"

    def current_track(self) -> MusicTrack:
        for track in MUSIC_TRACKS:
            if track.key == self.state.music_track:
                return track
        return MUSIC_TRACKS[0]

    def current_track_title(self) -> str:
        return self.current_track().title

    def music_track_index(self) -> int:
        for index, track in enumerate(MUSIC_TRACKS):
            if track.key == self.state.music_track:
                return index
        return 0

    def track_keys(self) -> set[str]:
        return {track.key for track in MUSIC_TRACKS}

    def _load_state(self) -> None:
        stored = load_audio_settings()
        if stored is None:
            return
        self.state.music_volume = stored.music_volume
        self.state.sfx_volume = stored.sfx_volume
        self.state.muted = stored.muted
        self.state.music_track = stored.music_track if stored.music_track in self.track_keys() else TRACK_HUE_THEME

    def _save_state(self) -> None:
        save_audio_settings(
            music_volume=self.state.music_volume,
            sfx_volume=self.state.sfx_volume,
            muted=self.state.muted,
            music_track=self.state.music_track,
        )


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def build_music_loop() -> pygame.mixer.Sound:
    bpm = 92
    beat = 60 / bpm
    progression = [
        (220.0, 277.18, 329.63),
        (246.94, 293.66, 369.99),
        (196.0, 246.94, 329.63),
        (174.61, 220.0, 261.63),
    ]
    duration = beat * 16
    frames = int(AUDIO.sample_rate * duration)
    samples = array("h")

    for frame in range(frames):
        t = frame / AUDIO.sample_rate
        beat_index = int(t / beat)
        chord = progression[(beat_index // 4) % len(progression)]
        local = (t % beat) / beat
        envelope = 0.42 + 0.58 * math.exp(-local * 4.2)

        bass = soft_square(chord[0] / 2, t) * 0.34
        pad = sum(math.sin(math.tau * freq * t) for freq in chord) * 0.09
        arp_freq = chord[(beat_index + int(local * 4)) % len(chord)] * 2
        arp = math.sin(math.tau * arp_freq * t) * 0.12 * envelope
        shimmer = math.sin(math.tau * (arp_freq * 2.01) * t) * 0.035 * envelope

        value = (bass + pad + arp + shimmer) * 0.52
        write_stereo_sample(samples, value, pan=0.54)

    return pygame.mixer.Sound(buffer=samples.tobytes())


def build_tone(
    notes: list[tuple[float, float]],
    volume: float = 0.5,
    wave: str = "sine",
) -> pygame.mixer.Sound:
    samples = array("h")
    for frequency, duration in notes:
        frame_count = int(AUDIO.sample_rate * duration)
        for frame in range(frame_count):
            t = frame / AUDIO.sample_rate
            progress = frame / max(1, frame_count - 1)
            envelope = attack_decay(progress, attack=0.12, decay=0.75)
            value = waveform(frequency, t, wave) * envelope * volume
            write_stereo_sample(samples, value)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def build_sweep(start_freq: float, end_freq: float, duration: float, volume: float = 0.45) -> pygame.mixer.Sound:
    samples = array("h")
    frame_count = int(AUDIO.sample_rate * duration)
    phase = 0.0
    for frame in range(frame_count):
        progress = frame / max(1, frame_count - 1)
        freq = start_freq + (end_freq - start_freq) * smoothstep(progress)
        phase += math.tau * freq / AUDIO.sample_rate
        envelope = attack_decay(progress, attack=0.08, decay=0.88)
        value = math.sin(phase) * envelope * volume
        write_stereo_sample(samples, value)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def build_noise_hit(duration: float, volume: float, tone: float, decay: float) -> pygame.mixer.Sound:
    samples = array("h")
    frame_count = int(AUDIO.sample_rate * duration)
    seed = 0x1234ABCD
    phase = 0.0
    for frame in range(frame_count):
        progress = frame / max(1, frame_count - 1)
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        noise = ((seed / 0x7FFFFFFF) * 2.0) - 1.0
        phase += math.tau * tone / AUDIO.sample_rate
        thump = math.sin(phase) * 0.7
        envelope = math.exp(-progress * decay)
        value = (noise * 0.42 + thump * 0.58) * envelope * volume
        write_stereo_sample(samples, value)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def write_stereo_sample(samples: array, value: float, pan: float = 0.5) -> None:
    value = max(-1.0, min(1.0, value))
    pan = clamp01(pan)
    left_gain = math.cos(pan * math.pi / 2)
    right_gain = math.sin(pan * math.pi / 2)
    samples.append(int(value * left_gain * 32767))
    samples.append(int(value * right_gain * 32767))


def waveform(frequency: float, t: float, wave: str) -> float:
    phase = (frequency * t) % 1.0
    if wave == "square":
        return 1.0 if phase < 0.5 else -1.0
    if wave == "triangle":
        return 4.0 * abs(phase - 0.5) - 1.0
    return math.sin(math.tau * frequency * t)


def soft_square(frequency: float, t: float) -> float:
    return (
        math.sin(math.tau * frequency * t)
        + math.sin(math.tau * frequency * 3 * t) * 0.32
        + math.sin(math.tau * frequency * 5 * t) * 0.16
    ) / 1.48


def attack_decay(progress: float, attack: float, decay: float) -> float:
    if progress < attack:
        return progress / max(0.001, attack)
    release = (progress - attack) / max(0.001, 1.0 - attack)
    return max(0.0, (1.0 - release) ** (1.0 + decay))


def smoothstep(value: float) -> float:
    value = clamp01(value)
    return value * value * (3.0 - 2.0 * value)
