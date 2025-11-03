"""Image generation helpers for creating AI-inspired character portraits."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Optional

DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512


class ImageGenerationError(RuntimeError):
    """Raised when an avatar cannot be generated."""


def generate_character_portrait(
    prompt: str,
    output_dir: str | Path,
    *,
    filename: Optional[str] = None,
) -> Path:
    """Generate a placeholder AI-style portrait for the given prompt.

    The function uses the `diffusers` Stable Diffusion pipeline when available.
    If the library is not installed, it falls back to creating a stylised
    textual badge with Pillow so that the game always has artwork to display.
    """

    output_directory = Path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_name = filename or _slugify(prompt) or "portrait"
    output_path = output_directory / f"{output_name}.png"

    if importlib.util.find_spec("diffusers") and importlib.util.find_spec("torch"):
        return _generate_with_diffusers(prompt, output_path)

    return _generate_with_pillow(prompt, output_path)


def _generate_with_diffusers(prompt: str, output_path: Path) -> Path:
    from diffusers import StableDiffusionPipeline
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    pipeline = pipeline.to(device)
    image = pipeline(prompt, num_inference_steps=25).images[0]
    image.save(output_path)
    return output_path


def _generate_with_pillow(prompt: str, output_path: Path) -> Path:
    if importlib.util.find_spec("PIL") is None:
        raise ImageGenerationError(
            "Pillow is required for placeholder portrait generation. Install it with `pip install pillow`."
        )
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (DEFAULT_WIDTH, DEFAULT_HEIGHT), color=(24, 24, 48))
    draw = ImageDraw.Draw(image)

    title = "AI HERO"
    subtitle = prompt[:80] + ("…" if len(prompt) > 80 else "")

    font = _load_font(ImageFont, 36)
    subtitle_font = _load_font(ImageFont, 20)

    draw.text((20, 20), title, fill=(255, 215, 0), font=font)
    draw.multiline_text((20, 120), subtitle, fill=(200, 200, 200), font=subtitle_font, spacing=8)

    image.save(output_path)
    return output_path


def _slugify(text: str) -> str:
    cleaned = [character.lower() for character in text if character.isalnum() or character in {"-", "_"}]
    slug = "".join(cleaned)
    return slug[:40]


def _load_font(image_font_module, size: int):
    try:
        return image_font_module.truetype("DejaVuSans.ttf", size)
    except OSError as exc:  # Pillow raises OSError when the font is missing
        raise ImageGenerationError("DejaVuSans.ttf font is required for placeholder generation.") from exc


__all__ = ["generate_character_portrait", "ImageGenerationError"]
