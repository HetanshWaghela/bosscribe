# 🎙️ Bosscribe

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/bosscribe.svg)](https://pypi.org/project/bosscribe/)

Your boss just sent another 4-minute voice note. You're not listening to that. 🙅

```bash
transcribe voice_note.opus
```

Boom. Text. Paste it into ChatGPT, reply, get on with your life. Runs 100% on your machine — no API keys, no accounts, nobody snooping on what your boss rambled about.

## Install

```bash
pip install bosscribe
```

That's it. You also need [FFmpeg](https://ffmpeg.org/) (it does the audio heavy lifting) — but don't sweat it: if it's missing, Bosscribe spots it on first run and offers to install it for you. 🪄

```
✗ FFmpeg isn't installed.
  Bosscribe can install it for you via Homebrew:
    brew install ffmpeg
  Install FFmpeg now? [Y/n]
```

Prefer doing it yourself? `brew install ffmpeg` · `choco install ffmpeg` · `sudo apt install ffmpeg`

## Use

```bash
transcribe note.opus            # spit it to the terminal
transcribe note.opus --save     # stash it as note.txt
transcribe note.opus --copy     # straight to your clipboard 📋
transcribe note.opus -l hi      # boss switched to Hindi mid-sentence? cool.
transcribe note.opus -m small   # want it sharper? bigger model. (tiny→large-v3-turbo)
transcribe note.opus | pbcopy   # pipe it wherever you want
```

Sick of typing the same flags? Set defaults once and forget:

```bash
transcribe config --save-to ~/notes   # always save here
transcribe config --model small       # always use this model
transcribe config --show              # what did I set again?
```

Throw any format at it — `.opus`, `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, whatever. WhatsApp `.opus` notes? Works out of the box, no fiddling.

First run grabs the model (~74 MB for the default), then it's cached forever. Apple Silicon flexes [mlx-whisper](https://github.com/ml-explore/mlx-examples); everyone else rides [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Either way it's fast and it's offline.

## Why though?

Because it's 2026 and you still shouldn't have to *manually transcribe a voice note like a court stenographer.* Your boss is busy. So are you. Let the robot listen.

## License

[MIT](LICENSE) — do whatever you want with it. © 2026 Hetansh Waghela.
