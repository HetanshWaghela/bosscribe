"""Tests for Bosscribe CLI."""

import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest


class TestUtils:
    """Test utility functions."""

    def test_validate_audio_file_missing(self):
        """Should exit on missing file."""
        from bosscribe.utils import validate_audio_file
        with pytest.raises(SystemExit):
            validate_audio_file("/nonexistent/file.opus")

    def test_validate_audio_file_bad_extension(self, tmp_path):
        """Should exit on unsupported extension."""
        from bosscribe.utils import validate_audio_file
        bad_file = tmp_path / "notes.pdf"
        bad_file.touch()
        with pytest.raises(SystemExit):
            validate_audio_file(str(bad_file))

    def test_validate_audio_file_good(self, tmp_path):
        """Should return resolved path for valid audio file."""
        from bosscribe.utils import validate_audio_file
        good_file = tmp_path / "voice.opus"
        good_file.touch()
        result = validate_audio_file(str(good_file))
        assert result == good_file.resolve()

    def test_validate_audio_file_unreadable(self, tmp_path):
        """Should exit on unreadable file."""
        from bosscribe.utils import validate_audio_file
        unreadable_file = tmp_path / "voice.opus"
        unreadable_file.touch()
        with patch("os.access", return_value=False):
            with pytest.raises(SystemExit):
                validate_audio_file(str(unreadable_file))

    def test_get_output_path_default(self, tmp_path):
        """Should save .txt next to audio file when no default dir."""
        from bosscribe.utils import get_output_path
        audio = tmp_path / "meeting.opus"
        result = get_output_path(audio)
        assert result == tmp_path / "meeting.txt"

    def test_get_output_path_custom_dir(self, tmp_path):
        """Should save .txt in custom dir when set."""
        from bosscribe.utils import get_output_path
        audio = tmp_path / "meeting.opus"
        custom_dir = tmp_path / "transcriptions"
        result = get_output_path(audio, str(custom_dir))
        assert result == custom_dir / "meeting.txt"
        assert custom_dir.exists()  # Should create the dir

    def test_supported_extensions(self):
        """Opus must be in supported extensions."""
        from bosscribe.utils import SUPPORTED_EXTENSIONS
        assert ".opus" in SUPPORTED_EXTENSIONS
        assert ".mp3" in SUPPORTED_EXTENSIONS
        assert ".wav" in SUPPORTED_EXTENSIONS
        assert ".m4a" in SUPPORTED_EXTENSIONS


class TestConfig:
    """Test configuration."""

    def test_load_config_defaults(self, tmp_path):
        """Should return defaults when no config exists."""
        with patch("bosscribe.config.CONFIG_FILE", tmp_path / "nonexistent.json"):
            from bosscribe.config import load_config
            config = load_config()
            assert config["default_save_dir"] == ""
            assert config["default_model"] == "base"

    def test_save_and_load_config(self, tmp_path):
        """Should persist config to disk."""
        config_file = tmp_path / "config.json"
        with patch("bosscribe.config.CONFIG_FILE", config_file), \
             patch("bosscribe.config.CONFIG_DIR", tmp_path):
            from bosscribe.config import save_config, load_config
            save_config({
                "default_save_dir": "/tmp/notes",
                "default_model": "small",
            })
            loaded = load_config()
            assert loaded["default_save_dir"] == "/tmp/notes"
            assert loaded["default_model"] == "small"

    def test_load_config_invalid_model(self, tmp_path):
        """Should fallback to base model if config has invalid model."""
        config_file = tmp_path / "config.json"
        with patch("bosscribe.config.CONFIG_FILE", config_file), \
             patch("bosscribe.config.CONFIG_DIR", tmp_path):
            from bosscribe.config import save_config, load_config
            save_config({"default_model": "super-large-ultra"})
            loaded = load_config()
            assert loaded["default_model"] == "base"

    def test_set_save_dir_unwritable_parent(self, tmp_path):
        """Should raise SystemExit if parent dir is not writable."""
        with patch("bosscribe.config.CONFIG_DIR", tmp_path), \
             patch("bosscribe.config.CONFIG_FILE", tmp_path / "config.json"), \
             patch("os.access", return_value=False):
            from bosscribe.config import set_save_dir
            with pytest.raises(SystemExit):
                set_save_dir(str(tmp_path / "new_subdir"))

    def test_set_default_model_invalid(self, tmp_path):
        """Should exit on invalid model name."""
        with patch("bosscribe.config.CONFIG_DIR", tmp_path), \
             patch("bosscribe.config.CONFIG_FILE", tmp_path / "config.json"):
            from bosscribe.config import set_default_model
            with pytest.raises(SystemExit):
                set_default_model("nonexistent-model")

    def test_set_save_dir_whitespace_clears(self, tmp_path):
        """Whitespace-only string should clear save dir like empty string."""
        config_file = tmp_path / "config.json"
        with patch("bosscribe.config.CONFIG_FILE", config_file), \
             patch("bosscribe.config.CONFIG_DIR", tmp_path):
            from bosscribe.config import (
                save_config, load_config, set_save_dir,
            )
            save_config({"default_save_dir": "/old/path"})
            set_save_dir("   ")
            loaded = load_config()
            assert loaded["default_save_dir"] == ""

    def test_load_config_unknown_keys(self, tmp_path):
        """Should ignore unknown keys in config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            '{"default_model": "small", "unknown_key": "value", '
            '"another": 123}'
        )
        with patch("bosscribe.config.CONFIG_FILE", config_file):
            from bosscribe.config import load_config
            config = load_config()
            assert config["default_model"] == "small"
            assert "unknown_key" not in config
            assert "another" not in config

    def test_load_config_corrupted_json(self, tmp_path):
        """Should return defaults on corrupted JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json content!!!")
        with patch("bosscribe.config.CONFIG_FILE", config_file):
            from bosscribe.config import load_config
            config = load_config()
            assert config["default_save_dir"] == ""
            assert config["default_model"] == "base"

    def test_load_config_non_string_values(self, tmp_path):
        """Should ignore non-string values and use defaults."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            '{"default_save_dir": 123, "default_model": ["tiny"]}'
        )
        with patch("bosscribe.config.CONFIG_FILE", config_file):
            from bosscribe.config import load_config
            config = load_config()
            assert config["default_save_dir"] == ""
            assert config["default_model"] == "base"

    def test_save_to_nonexistent_deep_parent(self, tmp_path):
        """Should accept nested path and persist it in config."""
        config_file = tmp_path / "config.json"
        with patch("bosscribe.config.CONFIG_FILE", config_file), \
             patch("bosscribe.config.CONFIG_DIR", tmp_path):
            from bosscribe.config import set_save_dir, load_config
            deep_path = tmp_path / "a" / "b" / "c"
            set_save_dir(str(deep_path))
            loaded = load_config()
            assert loaded["default_save_dir"] == str(deep_path)


class TestTranscriber:
    """Test transcriber model validation."""

    def test_invalid_model(self):
        """Should exit on invalid model name."""
        from bosscribe.transcriber import transcribe
        with pytest.raises(SystemExit):
            transcribe("dummy.opus", model="nonexistent")

    def test_valid_models(self):
        """All expected models should be valid."""
        from bosscribe.transcriber import VALID_MODELS
        assert "tiny" in VALID_MODELS
        assert "base" in VALID_MODELS
        assert "small" in VALID_MODELS
        assert "medium" in VALID_MODELS
        assert "large-v3" in VALID_MODELS


class TestCLI:
    """Test CLI entry point."""

    def test_help_runs(self):
        """transcribe --help should exit 0."""
        result = subprocess.run(
            [sys.executable, "-m", "bosscribe.cli", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Bosscribe" in result.stdout

    def test_version_runs(self):
        """transcribe --version should print version."""
        result = subprocess.run(
            [sys.executable, "-m", "bosscribe.cli", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_cli_config_filename_collision(self, tmp_path):
        """Should print tip when 'config' file exists."""
        from bosscribe.cli import _handle_config
        args = MagicMock()
        args.save_to = None
        args.model = None
        args.show = False

        with patch("bosscribe.cli.show_config") as mock_show, \
             patch("bosscribe.cli.Path.exists", return_value=True), \
             patch("bosscribe.cli.Path.is_file", return_value=True), \
             patch("bosscribe.cli.console.print") as mock_print:
            _handle_config(args)
            mock_show.assert_called_once()
            printed_texts = [
                call[0][0]
                for call in mock_print.call_args_list
                if call[0]
            ]
            assert any(
                "Note: A file named 'config' exists" in str(txt)
                for txt in printed_texts
            )

    def test_output_overwrites_directory(self, tmp_path):
        """Should exit if --output targets an existing directory."""
        from bosscribe.cli import _handle_transcribe
        audio = tmp_path / "voice.opus"
        audio.touch()
        output_dir = tmp_path / "mydir"
        output_dir.mkdir()

        args = MagicMock()
        args.audio_file = str(audio)
        args.model = None
        args.language = None
        args.save = False
        args.output = str(output_dir)
        args.copy = False

        with patch("bosscribe.cli.check_ffmpeg", return_value=True), \
             patch("bosscribe.cli.get_default_model", return_value="base"):
            with pytest.raises(SystemExit):
                _handle_transcribe(args)

    def test_output_parent_created_automatically(self, tmp_path):
        """Should create parent dir for --output if it doesn't exist."""
        from bosscribe.cli import _handle_transcribe
        audio = tmp_path / "voice.opus"
        audio.touch()
        output_file = tmp_path / "new_dir" / "sub" / "out.txt"

        args = MagicMock()
        args.audio_file = str(audio)
        args.model = None
        args.language = None
        args.save = False
        args.output = str(output_file)
        args.copy = False

        with patch("bosscribe.cli.check_ffmpeg", return_value=True), \
             patch("bosscribe.cli.get_default_model", return_value="base"), \
             patch("bosscribe.cli.transcribe", return_value="hello"):
            _handle_transcribe(args)
            assert output_file.exists()
            assert output_file.read_text() == "hello"

    def test_no_audio_file_shows_help(self):
        """Should show help when no audio file is provided."""
        result = subprocess.run(
            [sys.executable, "-m", "bosscribe.cli"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_invalid_model_flag_rejected(self):
        """Should reject invalid model via argparse choices."""
        result = subprocess.run(
            [
                sys.executable, "-m", "bosscribe.cli",
                "dummy.opus", "-m", "bogus",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()
