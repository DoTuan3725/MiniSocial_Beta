"""Xử lý ảnh bằng Pillow: xoay theo EXIF, thu nhỏ <= 1920px, nén WebP, cắt thumbnail vuông 150x150."""

import io

from PIL import Image, ImageOps

MAX_DIMENSION = 1920
THUMB_SIZE = (150, 150)
WEBP_QUALITY = 80


def _prepare(img):
    img = ImageOps.exif_transpose(img)
    if img.mode in ("P", "LA"):
        img = img.convert("RGBA")
    elif img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img


def to_webp(data, max_dimension=MAX_DIMENSION):
    with Image.open(io.BytesIO(data)) as img:
        img = _prepare(img)
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, "WEBP", quality=WEBP_QUALITY, method=4)
        return out.getvalue()


def make_thumbnail(data, size=THUMB_SIZE):
    with Image.open(io.BytesIO(data)) as img:
        img = _prepare(img)
        thumb = ImageOps.fit(img, size, Image.LANCZOS)
        out = io.BytesIO()
        thumb.save(out, "WEBP", quality=75, method=4)
        return out.getvalue()
