import uuid
from pathlib import Path

from fastapi import UploadFile

BASE_DIR = Path(__file__).resolve().parent
STATIC_ROOT = BASE_DIR / "static"
STATIC_ROOT.mkdir(exist_ok=True)
UPLOAD_ROOT = STATIC_ROOT / "uploads"
UPLOAD_ROOT.mkdir(exist_ok=True)


def save_upload_file(upload_file: UploadFile, subdir: str = "media") -> str:
    target_dir = UPLOAD_ROOT / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    file_suffix = Path(upload_file.filename or "").suffix or ".bin"
    file_name = f"{uuid.uuid4().hex}{file_suffix}"
    destination = target_dir / file_name

    with destination.open("wb") as out_file:
        content = upload_file.file.read()
        out_file.write(content)

    relative_path = destination.relative_to(STATIC_ROOT)
    return f"/static/{relative_path.as_posix()}"

