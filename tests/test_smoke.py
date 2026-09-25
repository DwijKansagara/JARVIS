"""Offline checks: no API requests, microphone recording, or desktop actions."""
import asyncio
import importlib
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import main
import config
import or_client
from actions.file_processor import _process_data
from actions import youtube_video
from PyQt6.QtCore import QTimer


class SmokeTests(unittest.TestCase):
    def test_all_modules_import_without_credentials(self):
        base = Path(main.__file__).parent
        for package in ("actions", "agent", "memory"):
            for path in (base / package).glob("*.py"):
                importlib.import_module(f"{package}.{path.stem}")

    def test_missing_config_uses_detected_os(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(config, "_CONFIG_PATH", Path(directory) / "missing.json"):
                self.assertEqual(config.get_config(), {})
                self.assertIn(config.get_os(), {"windows", "mac", "linux"})

    def test_openrouter_loads_credentials_only_when_used(self):
        with patch.object(or_client, "_load_api_key", side_effect=RuntimeError("missing")) as load:
            client = or_client.OpenRouterClient()
            load.assert_not_called()
            with self.assertRaisesRegex(RuntimeError, "missing"):
                _ = client._headers

    def test_csv_info(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_bytes(b"name,value\nalice,1\nbob,2\n")
            self.assertIn("Rows: 2, Columns: 2", _process_data(path, "csv", "info", {}))

    def test_xlsx_info(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.xlsx"
            pd.DataFrame({"value": [1, 2]}).to_excel(path, index=False)
            self.assertIn("Rows: 2, Columns: 1", _process_data(path, "xlsx", "info", {}))

    def test_transcript_current_api(self):
        transcript = Mock()
        transcript.fetch.return_value = [SimpleNamespace(text="hello"), SimpleNamespace(text="world")]
        with patch.object(youtube_video, "YouTubeTranscriptApi") as api:
            api.return_value.list.return_value.find_manually_created_transcript.return_value = transcript
            self.assertEqual(youtube_video._get_transcript("test-id"), "hello world")
            api.return_value.list.assert_called_once_with("test-id")

    def test_microphone_queue_handles_backpressure(self):
        jarvis = main.JarvisLive(Mock())
        jarvis.out_queue = asyncio.Queue(maxsize=1)
        jarvis._enqueue_audio(b"one")
        jarvis._enqueue_audio(b"two")
        self.assertEqual(jarvis.out_queue.qsize(), 1)
        self.assertEqual(jarvis.out_queue.get_nowait()["data"], b"one")

    def test_live_configuration_validates(self):
        configuration = main.JarvisLive(Mock())._build_config()
        self.assertIsNotNone(configuration.input_audio_transcription)
        self.assertIsNotNone(configuration.output_audio_transcription)
        self.assertGreater(len(configuration.tools[0].function_declarations), 0)

    def test_identity_instruction_names_creator_and_owner(self):
        prompt = Path(main.__file__).with_name("core").joinpath("prompt.txt").read_text(encoding="utf-8-sig")
        self.assertIn("created by Dwij Kansagara", prompt)
        self.assertIn("who is also your owner", prompt)
        self.assertIn("Never identify yourself as NVIDIA Nemotron", prompt)

    def test_first_run_ui_event_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("ui.API_FILE", Path(directory) / "missing.json"):
                ui = main.JarvisUI("face.png")
                self.assertFalse(ui._win._ready)
                self.assertIsNotNone(ui._win._overlay)
                QTimer.singleShot(150, ui._app.quit)
                ui.root.mainloop()
                ui._win.close()


if __name__ == "__main__":
    unittest.main()
