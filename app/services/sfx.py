import math
import os
import random
import struct
import wave
from typing import Any, Dict, List, Optional

from moviepy import AudioClip, AudioFileClip, CompositeAudioClip, afx

from app.utils import file_security, utils

DEFAULT_SFX_FILES = {
    "whoosh.wav": "whoosh",
    "impact_808.wav": "impact_808",
    "camera_click.wav": "camera_click",
    "sub_riser.wav": "sub_riser",
}


def get_sfx_dir(sub_dir: str = "") -> str:
    """Return the filesystem directory for sound effects, creating it if needed."""
    d = utils.resource_dir("sfx")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    os.makedirs(d, exist_ok=True)
    return d


def _write_pcm_wav(
    path: str,
    samples: List[float],
    sample_rate: int = 44100,
    peak_level: float = 0.90,
) -> None:
    """Write normalized 16-bit mono PCM samples to a WAV file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    max_abs = max((abs(s) for s in samples), default=1.0)
    if max_abs < 1e-6:
        max_abs = 1.0
    scale = peak_level / max_abs

    raw = bytearray()
    for s in samples:
        v = int(s * scale * 32767.0)
        v = max(-32768, min(32767, v))
        raw.extend(struct.pack("<h", v))

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw)


def _generate_whoosh(output_path: str, sample_rate: int = 44100) -> None:
    """400ms white noise sweep with low-pass/band-pass filter effect."""
    duration = 0.4
    num_samples = int(sample_rate * duration)
    samples: List[float] = []
    low = 0.0
    band = 0.0
    rng = random.Random(1001)

    for i in range(num_samples):
        t = i / sample_rate
        u = t / duration
        fc = 250.0 + 2600.0 * (math.sin(math.pi * u) ** 2)
        f_calc = min(0.99, max(0.001, 2.0 * math.sin(math.pi * fc / sample_rate)))
        x = rng.uniform(-1.0, 1.0)
        low += f_calc * band
        band += f_calc * (x - low - 0.5 * band)
        env = math.sin(math.pi * u) ** 1.5
        samples.append((band * 0.85 + low * 0.25) * env)

    _write_pcm_wav(output_path, samples, sample_rate=sample_rate, peak_level=0.88)


def _generate_impact_808(output_path: str, sample_rate: int = 44100) -> None:
    """800ms sine sub-bass wave decaying from 80Hz down to 35Hz with exponential decay."""
    duration = 0.8
    num_samples = int(sample_rate * duration)
    samples: List[float] = []
    phase = 0.0

    for i in range(num_samples):
        t = i / sample_rate
        freq = 35.0 + 45.0 * math.exp(-t / 0.18)
        phase += 2.0 * math.pi * freq / sample_rate
        sub = math.sin(phase) + 0.18 * math.sin(2.0 * phase) + 0.05 * math.sin(3.0 * phase)
        transient = math.exp(-t / 0.003) * math.sin(2.0 * math.pi * 220.0 * t) if t < 0.02 else 0.0
        amp = math.exp(-3.5 * t / duration) * (1.0 - math.exp(-max(0.0, t) / 0.003))
        if t > duration - 0.02:
            amp *= (duration - t) / 0.02
        samples.append(sub * amp + transient * 0.25)

    _write_pcm_wav(output_path, samples, sample_rate=sample_rate, peak_level=0.92)


def _generate_camera_click(output_path: str, sample_rate: int = 44100) -> None:
    """80ms sharp transient mechanical snap."""
    duration = 0.08
    num_samples = int(sample_rate * duration)
    samples: List[float] = []
    rng = random.Random(2002)

    for i in range(num_samples):
        t = i / sample_rate
        snap = (
            rng.uniform(-0.7, 0.7)
            + 0.5 * math.sin(2.0 * math.pi * 3400.0 * t)
            + 0.3 * math.sin(2.0 * math.pi * 1700.0 * t)
        ) * math.exp(-t / 0.006)

        if t >= 0.028:
            t2 = t - 0.028
            latch = (
                rng.uniform(-0.5, 0.5)
                + 0.4 * math.sin(2.0 * math.pi * 2500.0 * t2)
            ) * math.exp(-t2 / 0.008)
        else:
            latch = 0.0

        fade = 1.0 if t <= duration - 0.005 else (duration - t) / 0.005
        samples.append((snap + 0.65 * latch) * fade)

    _write_pcm_wav(output_path, samples, sample_rate=sample_rate, peak_level=0.85)


def _generate_sub_riser(output_path: str, sample_rate: int = 44100) -> None:
    """1200ms rising pitch tension sweep from 45Hz to 180Hz."""
    duration = 1.2
    num_samples = int(sample_rate * duration)
    samples: List[float] = []
    phase = 0.0
    f0 = 45.0
    f1 = 180.0
    rng = random.Random(3003)
    low_noise = 0.0

    for i in range(num_samples):
        t = i / sample_rate
        u = t / duration
        freq = f0 * ((f1 / f0) ** u)
        phase += 2.0 * math.pi * freq / sample_rate
        x = rng.uniform(-1.0, 1.0)
        alpha = min(0.9, 2.0 * math.pi * freq / sample_rate)
        low_noise += alpha * (x - low_noise)
        tone = (
            math.sin(phase)
            + 0.25 * math.sin(2.0 * phase)
            + 0.1 * math.sin(3.0 * phase)
            + 0.15 * low_noise
        )
        amp = 0.15 + 0.85 * (u ** 1.8)
        if t > duration - 0.03:
            amp *= (duration - t) / 0.03
        samples.append(tone * amp)

    _write_pcm_wav(output_path, samples, sample_rate=sample_rate, peak_level=0.90)


GENERATORS = {
    "whoosh.wav": _generate_whoosh,
    "impact_808.wav": _generate_impact_808,
    "camera_click.wav": _generate_camera_click,
    "sub_riser.wav": _generate_sub_riser,
}


def generate_default_sfx_if_missing(
    sfx_dir: Optional[str] = None, force: bool = False
) -> Dict[str, str]:
    """
    Generate clean, crisp synthesizer WAV files if missing.
    Ensures out-of-the-box operation without external audio asset downloads.
    """
    target_dir = sfx_dir or get_sfx_dir()
    os.makedirs(target_dir, exist_ok=True)
    generated: Dict[str, str] = {}

    for filename, generator_func in GENERATORS.items():
        file_path = os.path.join(target_dir, filename)
        if force or not os.path.exists(file_path):
            generator_func(file_path)
        stem = os.path.splitext(filename)[0]
        generated[filename] = file_path
        generated[stem] = file_path

    return generated


def get_available_sfx(sfx_dir: Optional[str] = None) -> Dict[str, str]:
    """List available SFX types and paths."""
    target_dir = sfx_dir or get_sfx_dir()
    generate_default_sfx_if_missing(target_dir)

    available: Dict[str, str] = {}
    if os.path.exists(target_dir):
        for fname in sorted(os.listdir(target_dir)):
            if fname.lower().endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac")):
                full_path = os.path.join(target_dir, fname)
                stem = os.path.splitext(fname)[0]
                available[stem] = full_path
                available[fname] = full_path

    return available


def get_sfx_path(sfx_name: str, sfx_dir: Optional[str] = None) -> str:
    """Return the absolute path of a sound effect, generating default assets if missing."""
    target_dir = sfx_dir or get_sfx_dir()
    base_name = os.path.basename(sfx_name.strip())
    if not base_name.lower().endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac")):
        filename = f"{base_name}.wav"
    else:
        filename = base_name

    candidate_path = os.path.join(target_dir, filename)
    if not os.path.exists(candidate_path):
        generate_default_sfx_if_missing(target_dir)

    try:
        return file_security.resolve_path_within_directory(
            target_dir, filename, require_file=True
        )
    except ValueError as exc:
        raise FileNotFoundError(f"Sound effect '{sfx_name}' not found: {exc}") from exc


def create_sfx_audio_clip(sfx_name: str, volume: float = 0.5) -> AudioFileClip:
    """Load an SFX AudioFileClip with volume scaling applied."""
    path = get_sfx_path(sfx_name)
    clip = AudioFileClip(path)
    if volume is not None and volume != 1.0:
        vol = max(0.0, float(volume))
        clip = clip.with_effects([afx.MultiplyVolume(vol)])
    return clip


def build_transition_sfx_clips(
    scene_durations: List[float],
    sfx_type: str = "whoosh",
    volume: float = 0.4,
) -> List[AudioClip]:
    """
    Generate audio clips timed precisely 0.05s before each scene cut.
    For N scene durations, cuts occur at cumulative boundaries 0..N-2.
    """
    if not scene_durations or len(scene_durations) < 2:
        return []

    clips: List[AudioClip] = []
    cumulative_time = 0.0
    for duration in scene_durations[:-1]:
        cumulative_time += max(0.0, float(duration))
        start_time = max(0.0, round(cumulative_time - 0.05, 4))
        clip = create_sfx_audio_clip(sfx_type, volume=volume).with_start(start_time)
        clips.append(clip)

    return clips


def build_hook_sfx_clip(hook_time: float = 1.0, volume: float = 0.6) -> AudioClip:
    """Place impact_808 sub-bass hit at the hook time (default 1.0s)."""
    start_time = max(0.0, float(hook_time))
    clip = create_sfx_audio_clip("impact_808", volume=volume)
    return clip.with_start(start_time)


def mix_sfx_into_audio(
    speech_audio_clip: AudioClip,
    sfx_events: Optional[List[Any]] = None,
    bgm_audio_clip: Optional[AudioClip] = None,
) -> CompositeAudioClip:
    """
    Composite speech, optional BGM, and sound effect events with balanced levels.
    sfx_events can contain AudioClip instances, (time, name) tuples, or event dictionaries.
    """
    clips: List[AudioClip] = [speech_audio_clip]

    if bgm_audio_clip is not None:
        clips.append(bgm_audio_clip)

    if sfx_events:
        for item in sfx_events:
            if isinstance(item, AudioClip):
                clips.append(item)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("sfx") or item.get("type", "whoosh")
                vol = float(item.get("volume", item.get("vol", 0.5)))
                time_pos = float(item.get("time", item.get("start", 0.0)))
                clip = create_sfx_audio_clip(name, volume=vol).with_start(time_pos)
                clips.append(clip)
            elif isinstance(item, (tuple, list)):
                if len(item) == 2:
                    time_pos, name = item
                    vol = 0.5
                elif len(item) >= 3:
                    time_pos, name, vol = item[0], item[1], item[2]
                else:
                    continue
                clip = create_sfx_audio_clip(str(name), volume=float(vol)).with_start(float(time_pos))
                clips.append(clip)

    composite = CompositeAudioClip(clips)
    ref_duration = getattr(speech_audio_clip, "duration", None)
    if ref_duration is not None:
        composite = composite.with_duration(ref_duration)

    return composite
