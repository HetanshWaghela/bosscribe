# 🎙️ Bosscribe

**Your boss sends voice notes. You need them as text. Done.**

No more replaying 5-minute voice recordings trying to type out what your boss said. No more manually transcribing before you can paste into ChatGPT. Just one command and boom — text on your terminal.

---

## Install

```bash
pip install bosscribe
```

> **Prerequisite:** [FFmpeg](https://ffmpeg.org/) must be installed on your system.
>
> | Platform | Command |
> |----------|---------|
> | **macOS** | `brew install ffmpeg` |
> | **Windows** | `choco install ffmpeg` or `winget install ffmpeg` |
> | **Linux** | `sudo apt install ffmpeg` |

That's it. No config files, no API keys, no accounts. Everything runs **locally** on your machine.

---

## Use

```bash
transcribe voice_note.opus
```

That's the whole thing. The transcription prints right to your terminal. Copy it, paste it into ChatGPT, send it to a colleague — whatever you need.

### Save to file

```bash
# Saves as voice_note.txt (same name, same folder)
transcribe voice_note.opus --save

# Save to a specific file
transcribe voice_note.opus --save -o meeting_notes.txt
```

### Copy to clipboard

```bash
# Auto-copy to clipboard — paste straight into ChatGPT
transcribe voice_note.opus --copy
```

### Specify language

Whisper auto-detects language, but if it's getting confused (Hinglish, code-switching, etc.):

```bash
transcribe voice_note.opus --language hi
transcribe voice_note.opus -l en
```

### Use a different model

```bash
transcribe voice_note.opus --model large-v3   # Most accurate
transcribe voice_note.opus -m tiny            # Fastest
```

### Combine flags

```bash
transcribe voice_note.opus --save --copy --model small -l hi
```

### Pipe it

```bash
# Works with pipes too
transcribe voice_note.opus | pbcopy    # macOS
transcribe voice_note.opus | xclip    # Linux
```

---

## Set Default Save Location

Tired of typing `--save -o ~/notes/` every time? Set it once:

```bash
# Set a default folder for all saved transcriptions
transcribe config --save-to ~/Desktop/transcriptions

# Now this saves to ~/Desktop/transcriptions/voice_note.txt
transcribe voice_note.opus --save

# Clear it (go back to saving next to the audio file)
transcribe config --save-to ""

# View your current settings
transcribe config --show
```

---

## Supported Audio Formats

Anything FFmpeg can handle — which is basically everything:

`.opus` · `.mp3` · `.wav` · `.m4a` · `.ogg` · `.webm` · `.flac` · `.aac` · `.wma` · `.mp4`

WhatsApp voice recordings (`.opus`) work out of the box. No conversion needed.

---

## How It Works

Bosscribe auto-selects the **fastest Whisper backend** for your platform:

| Platform | Backend | Why |
|----------|---------|-----|
| **macOS** (Apple Silicon) | [mlx-whisper](https://github.com/ml-explore/mlx-examples) | Blazing fast — runs on Apple GPU via Metal |
| **Windows / Linux / macOS (Intel)** | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 4-12× faster than vanilla Whisper via CTranslate2 |

Everything runs **100% locally**. No data leaves your machine. No API keys. No internet needed (after first model download).

---

## Models

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| `tiny` | ~39 MB | ⚡⚡⚡⚡⚡ | Quick & dirty, short notes |
| `base` | ~74 MB | ⚡⚡⚡⚡ | **Default** — great balance |
| `small` | ~244 MB | ⚡⚡⚡ | Better accuracy |
| `medium` | ~769 MB | ⚡⚡ | High accuracy |
| `large-v3` | ~1.5 GB | ⚡ | Best accuracy, needs more RAM |
| `large-v3-turbo` | ~809 MB | ⚡⚡ | Near large-v3 quality, much faster |

First run downloads the model automatically. After that, it's cached.

---

## Why Bosscribe?

Because your boss is busy. They send 3-minute voice notes instead of typing. You need that text to:

- 📋 Paste into ChatGPT for context
- 📝 Create action items
- 💬 Forward to colleagues who don't have time for voice notes either
- 📄 Keep a written record

And you shouldn't have to manually transcribe like it's 2005.

---

## License

MIT — do whatever you want with it.
