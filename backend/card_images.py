"""Validate and normalize administrator-supplied card artwork."""
import io
import warnings
from urllib.parse import urlparse

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000


def normalize_card_image(data: bytes) -> bytes:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Choose a PNG, JPEG or WebP image up to 2 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ValueError("Only PNG, JPEG and WebP images are supported.")
                if image.width * image.height > MAX_IMAGE_PIXELS or min(image.size) < 80:
                    raise ValueError("Image dimensions must be at least 80 pixels per side and at most 16 megapixels.")
                if getattr(image, "is_animated", False):
                    raise ValueError("Choose a still image, not an animation.")
                image.load()
                clean = ImageOps.exif_transpose(image).convert("RGBA")
                clean.thumbnail((1200, 1200))
                output = io.BytesIO()
                clean.save(output, "WEBP", quality=90, method=4)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValueError("This file is not a supported, readable card image.") from error


def validate_card_image_url(value):
    value = (value or "").strip()
    if not value:
        return None
    parsed = urlparse(value)
    if (value.startswith("/cards/") and not parsed.netloc and not parsed.query
            and not parsed.fragment and ".." not in parsed.path and "\\" not in value):
        return value
    local = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (parsed.scheme == "https" or local) and parsed.hostname and not parsed.username and not parsed.password and "\\" not in value:
        return value
    raise ValueError("Use an HTTPS image URL or a local /cards/ image path.")
