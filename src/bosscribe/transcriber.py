"""Core transcription logic for Bosscribe.

Auto-selects the best Whisper backend for the current platform:
  - macOS (Apple Silicon): mlx-whisper  — blazing fast via Metal GPU
  - Windows / Linux:       faster-whisper — optimized via CTranslate2
"""

from __future__ import annotations

import platform
import sys
from typing import Optional

from rich.console import Console

console = Console()

# Model name mappings for each backend
MLX_MODELS = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
}

VALID_MODELS = {
    "tiny", "base", "small", "medium",
    "large-v3", "large-v3-turbo",
}


def transcribe(
    audio_path: str,
    model: str = "base",
    language: Optional[str] = None,
) -> str:
    """Transcribe an audio file to text.

    Automatically selects the best Whisper backend for the current platform.

    Args:
        audio_path: Path to the audio file.
        model: Whisper model size (tiny/base/small/medium/large-v3/large-v3-turbo).
        language: Optional language code (e.g., 'en', 'hi', 'es'). Auto-detects if None.

    Returns:
        The transcribed text as a string.
    """
    if model not in VALID_MODELS:
        console.print(f"[bold red]✗ Unknown model:[/bold red] {model}")
        console.print(f"  Valid models: {', '.join(sorted(VALID_MODELS))}")
        raise SystemExit(1)

    if sys.platform == "darwin" and platform.machine() == "arm64":
        return _transcribe_mlx(audio_path, model, language)
    else:
        return _transcribe_faster_whisper(audio_path, model, language)


def _transcribe_mlx(audio_path: str, model: str, language: Optional[str]) -> str:
    """Transcribe using mlx-whisper (Apple Silicon)."""
    try:
        import mlx_whisper
    except ImportError:
        console.print("[bold red]✗ mlx-whisper is not installed![/bold red]")
        console.print("  Run: [cyan]pip install mlx-whisper[/cyan]")
        raise SystemExit(1) from None

    model_path = MLX_MODELS.get(model, MLX_MODELS["base"])

    kwargs = {"path_or_hf_repo": model_path}
    if language:
        kwargs["language"] = language

    result = mlx_whisper.transcribe(audio_path, **kwargs)
    return result["text"].strip()


def _transcribe_faster_whisper(
    audio_path: str, model: str, language: Optional[str],
) -> str:
    """Transcribe using faster-whisper (Windows/Linux)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        console.print("[bold red]✗ faster-whisper is not installed![/bold red]")
        console.print("  Run: [cyan]pip install faster-whisper[/cyan]")
        raise SystemExit(1) from None

    # Auto-detect best device
    device = "cpu"
    compute_type = "int8"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            compute_type = "float16"
    except ImportError:
        pass  # No torch = CPU mode, which is fine

    # faster-whisper uses the same model names as openai-whisper
    whisper_model = WhisperModel(model, device=device, compute_type=compute_type)

    kwargs: dict[str, object] = {"beam_size": 5}
    if language:
        kwargs["language"] = language

    segments, _info = whisper_model.transcribe(audio_path, **kwargs)

    # Collect all segments into full text
    text_parts = []
    for segment in segments:
        text_parts.append(segment.text)

    return "".join(text_parts).strip()
