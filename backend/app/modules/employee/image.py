"""Preparing a face shot for the access-control terminals.

The terminals are picky about what they will accept into a face library: a
phone photo straight out of the camera roll is too large, often arrives sideways
because the orientation lives in EXIF rather than in the pixels, and may not be
JPEG at all. Carried over from the face_recognation service, which has been
feeding these same six devices for a year.
"""

import logging
import os
from pathlib import Path

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# What the devices take without complaint.
MAX_WIDTH, MAX_HEIGHT = 1920, 1080
TARGET_KB = 200


def compress_image_for_hikvision(
    input_path: str,
    target_kb: int = TARGET_KB,
    step: int = 5,
    resize_step: float = 0.9,
) -> str:
    """Rewrite the shot as a JPEG the terminals will take, and return its path.

    Quality comes down first and the image is only shrunk once quality has run
    out, so the face stays as large as the size budget allows. The original is
    removed: it has no reader once the compressed copy exists.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    img = Image.open(input_path)
    img = ImageOps.exif_transpose(img)  # honour the orientation flag
    img = img.convert("RGB")  # JPEG has no alpha channel

    if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

    output_path = Path(input_path).with_stem(Path(input_path).stem + "_compressed")
    output_path = output_path.with_suffix(".jpg")

    quality = 95
    while True:
        img.save(output_path, "JPEG", optimize=True, quality=quality)
        size_kb = os.path.getsize(output_path) / 1024

        if size_kb <= target_kb:
            logger.info(
                "Face shot compressed to %.1f KB at quality=%d, size=%s",
                size_kb,
                quality,
                img.size,
            )
            break

        if quality > step:
            quality -= step
        else:
            new_size = (int(img.size[0] * resize_step), int(img.size[1] * resize_step))
            if new_size[0] < 1 or new_size[1] < 1:
                raise RuntimeError("Image became too small while compressing")
            img = img.resize(new_size, Image.LANCZOS)
            quality = 95

    if str(output_path) != input_path:
        try:
            os.remove(input_path)
        except OSError as e:
            logger.warning("Could not delete original file %s: %s", input_path, e)

    return str(output_path)
