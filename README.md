# 🎙️ Bosscribe

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/bosscribe.svg)](https://pypi.org/project/bosscribe/)

**Your boss sends voice notes. You need them as text. One command. Done.**

Runs 100% locally — no API keys, no accounts, no data leaves your machine.

## Install

```bash
pip install bosscribe
```

Requires [FFmpeg](https://ffmpeg.org/): `brew install ffmpeg` (macOS) · `choco install ffmpeg` (Windows) · `sudo apt install ffmpeg` (Linux)

## Use

```bash
transcribe voice_note.opus            # print to terminal
transcribe voice_note.opus --save     # save as voice_note.txt
transcribe voice_note.opus --copy     # copy to clipboard
transcribe voice_note.opus -l hi      # force a language
transcribe voice_note.opus -m small   # pick a model (tiny/base/small/medium/large-v3/large-v3-turbo)
transcribe voice_note.opus | pbcopy   # pipe it anywhere
```

Set defaults once:

```bash
transcribe config --save-to ~/notes   # default save folder
transcribe config --model small       # default model
transcribe config --show              # view settings
```

Works with any format FFmpeg reads — `.opus`, `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, and more. WhatsApp `.opus` notes work out of the box.

First run downloads the model (~74 MB for `base`), then it's cached. Apple Silicon uses [mlx-whisper](https://github.com/ml-explore/mlx-examples); everything else uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## License

Released under the [MIT License](LICENSE). © 2025 Hetansh Waghela.
