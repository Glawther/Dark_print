import os
import shutil
import struct
import tempfile
import unittest
import wave
from unittest.mock import patch

from moviepy import AudioArrayClip, CompositeAudioClip
import numpy as np

from app.models.schema import VideoParams
from app.services import sfx
from app.services import video as vd


class TestSfxEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_default_sfx_creates_all_files(self):
        """Test default synthesizer WAV generation for all four cinematic assets."""
        generated = sfx.generate_default_sfx_if_missing(sfx_dir=self.temp_dir)

        expected_files = ["whoosh.wav", "impact_808.wav", "camera_click.wav", "sub_riser.wav"]
        for fname in expected_files:
            file_path = os.path.join(self.temp_dir, fname)
            self.assertTrue(os.path.exists(file_path), f"Expected {fname} to exist")
            self.assertIn(fname, generated)
            stem = os.path.splitext(fname)[0]
            self.assertIn(stem, generated)

    def test_wave_file_audio_characteristics(self):
        """Test WAV headers, channels, frame rate, and exact durations."""
        sfx.generate_default_sfx_if_missing(sfx_dir=self.temp_dir)

        specs = {
            "whoosh.wav": {"duration": 0.4, "frames": 17640},
            "impact_808.wav": {"duration": 0.8, "frames": 35280},
            "camera_click.wav": {"duration": 0.08, "frames": 3528},
            "sub_riser.wav": {"duration": 1.2, "frames": 52920},
        }

        for fname, spec in specs.items():
            path = os.path.join(self.temp_dir, fname)
            with wave.open(path, "rb") as wf:
                self.assertEqual(wf.getnchannels(), 1, f"{fname} should be mono")
                self.assertEqual(wf.getsampwidth(), 2, f"{fname} should be 16-bit")
                self.assertEqual(wf.getframerate(), 44100, f"{fname} sample rate should be 44100Hz")
                self.assertEqual(wf.getnframes(), spec["frames"], f"{fname} frame count mismatch")
                duration = wf.getnframes() / wf.getframerate()
                self.assertAlmostEqual(duration, spec["duration"], places=3)

                frames = wf.readframes(wf.getnframes())
                unpacked = struct.unpack(f"<{wf.getnframes()}h", frames)
                max_val = max(abs(s) for s in unpacked)
                self.assertGreater(max_val, 1000, f"{fname} should have audible signal")
                self.assertLessEqual(max_val, 32767, f"{fname} should not exceed 16-bit max")

    def test_get_available_sfx(self):
        """Test listing available sound effects."""
        available = sfx.get_available_sfx(sfx_dir=self.temp_dir)
        for key in ["whoosh", "whoosh.wav", "impact_808", "camera_click", "sub_riser"]:
            self.assertIn(key, available)
            self.assertTrue(os.path.isfile(available[key]))

    def test_get_sfx_path_resolution_and_traversal_protection(self):
        """Test path resolution and directory traversal rejection."""
        path1 = sfx.get_sfx_path("whoosh", sfx_dir=self.temp_dir)
        path2 = sfx.get_sfx_path("whoosh.wav", sfx_dir=self.temp_dir)
        self.assertEqual(path1, path2)
        self.assertTrue(os.path.isfile(path1))

        with self.assertRaises(FileNotFoundError):
            sfx.get_sfx_path("non_existent_sfx_file", sfx_dir=self.temp_dir)

        with self.assertRaises((FileNotFoundError, ValueError)):
            sfx.get_sfx_path("../../etc/passwd", sfx_dir=self.temp_dir)

    def test_create_sfx_audio_clip(self):
        """Test AudioFileClip creation and volume adjustment."""
        sfx.generate_default_sfx_if_missing(sfx_dir=self.temp_dir)
        with patch.object(sfx, "get_sfx_dir", return_value=self.temp_dir):
            clip = sfx.create_sfx_audio_clip("whoosh", volume=0.5)
            try:
                self.assertAlmostEqual(clip.duration, 0.4, places=2)
            finally:
                clip.close()

    def test_build_transition_sfx_clips_timing(self):
        """Test transition whoosh clips timing 0.05s before cuts."""
        sfx.generate_default_sfx_if_missing(sfx_dir=self.temp_dir)
        with patch.object(sfx, "get_sfx_dir", return_value=self.temp_dir):
            # 3 scenes: cuts at 3.0 and 7.0 -> whoosh at 2.95 and 6.95
            durations = [3.0, 4.0, 5.0]
            clips = sfx.build_transition_sfx_clips(durations, sfx_type="whoosh", volume=0.4)
            try:
                self.assertEqual(len(clips), 2)
                self.assertAlmostEqual(clips[0].start, 2.95, places=3)
                self.assertAlmostEqual(clips[1].start, 6.95, places=3)
            finally:
                for c in clips:
                    c.close()

            # Boundary cases
            self.assertEqual(sfx.build_transition_sfx_clips([]), [])
            self.assertEqual(sfx.build_transition_sfx_clips([5.0]), [])

            # Very early cut clamped to 0.0
            early_clips = sfx.build_transition_sfx_clips([0.02, 5.0])
            try:
                self.assertEqual(len(early_clips), 1)
                self.assertAlmostEqual(early_clips[0].start, 0.0, places=3)
            finally:
                for c in early_clips:
                    c.close()

    def test_build_hook_sfx_clip(self):
        """Test impact 808 hook placed at 1.0s."""
        sfx.generate_default_sfx_if_missing(sfx_dir=self.temp_dir)
        with patch.object(sfx, "get_sfx_dir", return_value=self.temp_dir):
            hook_clip = sfx.build_hook_sfx_clip(hook_time=1.0, volume=0.6)
            try:
                self.assertAlmostEqual(hook_clip.start, 1.0, places=3)
                self.assertAlmostEqual(hook_clip.duration, 0.8, places=2)
            finally:
                hook_clip.close()

    def test_mix_sfx_into_audio(self):
        """Test mixing speech, BGM, and SFX events into CompositeAudioClip."""
        sfx.generate_default_sfx_if_missing(sfx_dir=self.temp_dir)
        with patch.object(sfx, "get_sfx_dir", return_value=self.temp_dir):
            speech_clip = AudioArrayClip(np.zeros((44100 * 5, 2)), fps=44100)
            bgm_clip = AudioArrayClip(np.zeros((44100 * 5, 2)), fps=44100)
            sfx_events = [
                {"sfx": "whoosh", "time": 2.95, "volume": 0.4},
                (1.0, "impact_808", 0.6),
            ]

            composite = sfx.mix_sfx_into_audio(
                speech_audio_clip=speech_clip,
                sfx_events=sfx_events,
                bgm_audio_clip=bgm_clip,
            )
            try:
                self.assertIsInstance(composite, CompositeAudioClip)
                self.assertEqual(len(composite.clips), 4)  # speech + bgm + 2 sfx
                self.assertAlmostEqual(composite.duration, 5.0, places=2)
            finally:
                speech_clip.close()
                bgm_clip.close()
                for c in composite.clips:
                    if hasattr(c, "close"):
                        c.close()
                composite.close()

    def test_video_generate_video_mixes_sfx_when_requested(self):
        """Test video.generate_video invokes SFX builders when transition_sfx and hook_sfx are enabled."""
        params = VideoParams(
            video_subject="sfx_test",
            subtitle_enabled=False,
            bgm_type="random",
            bgm_volume=0.0,
            transition_sfx=True,
            hook_sfx=True,
            video_clip_duration=5,
        )

        class FakeClip:
            def __init__(self, duration=10.0, fps=44100):
                self.duration = duration
                self.fps = fps
                self.size = (720, 1280)
                self.w = 720
                self.h = 1280
                self.closed = False

            def with_effects(self, effects):
                return self

            def with_audio(self, audio):
                return self

            def close(self):
                self.closed = True

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

        source_video = FakeClip(duration=10.0)
        voice_source = FakeClip(duration=10.0)
        fake_sfx_clip1 = FakeClip(duration=0.4)
        fake_sfx_clip2 = FakeClip(duration=0.8)

        with (
            patch.object(vd, "_open_video_clip_quietly", return_value=source_video),
            patch.object(vd, "AudioFileClip", return_value=voice_source),
            patch.object(vd, "_write_videofile_with_codec_fallback") as mock_writer,
            patch.object(vd, "_get_configured_video_codec", return_value="libx264"),
            patch.object(sfx, "build_transition_sfx_clips", return_value=[fake_sfx_clip1]) as mock_trans,
            patch.object(sfx, "build_hook_sfx_clip", return_value=fake_sfx_clip2) as mock_hook,
            patch.object(vd, "CompositeAudioClip", wraps=CompositeAudioClip),
        ):
            success = vd.generate_video(
                video_path="input.mp4",
                audio_path="voice.mp3",
                subtitle_path="",
                output_file="output.mp4",
                params=params,
                transition_sfx=True,
                hook_sfx=True,
            )
            self.assertTrue(success)
            mock_trans.assert_called_once()
            mock_hook.assert_called_once_with(hook_time=1.0)
            mock_writer.assert_called_once()


if __name__ == "__main__":
    unittest.main()
