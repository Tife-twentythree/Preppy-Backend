import uuid
from pathlib import Path

import qrcode

from config import settings
from storage import STATIC_ROOT

BARCODE_DIR = STATIC_ROOT / "barcodes"
BARCODE_DIR.mkdir(parents=True, exist_ok=True)


def generate_unique_slug(base: str) -> str:
    slug = (
        base.lower()
        .replace(" ", "-")
        .replace("_", "-")
        .strip("-")
    )
    if not slug:
        slug = uuid.uuid4().hex[:8]
    return f"{slug}-{uuid.uuid4().hex[:4]}"


def generate_barcode(slug: str) -> str:
    target_url = f"{settings.barcode_base_url}/{slug}"
    img = qrcode.make(target_url)
    file_path = BARCODE_DIR / f"{slug}.png"
    img.save(file_path)
    relative_path = file_path.relative_to(STATIC_ROOT)
    return f"/static/{relative_path.as_posix()}"

