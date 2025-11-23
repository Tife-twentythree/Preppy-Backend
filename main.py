from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import barcode as barcode_utils
import storage
from auth import (
    create_access_token,
    create_verification_code,
    get_current_user,
    get_password_hash,
    verify_password,
)
from config import settings
from database import Base, engine, get_db
from models import Creator, EmailCapture, Media, User
from schemas import (
    BarcodeResponse,
    CreatorBase,
    CreatorUpdatePayload,
    EmailCaptureRequest,
    EmailCaptureResponse,
    LoginPayload,
    MediaBase,
    PublishResponse,
    RequestCodePayload,
    TokenResponse,
    UserResponse,
    VerifyCodePayload,
    token_expiry_seconds,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Preppy Nigga API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=storage.STATIC_ROOT), name="static")


@app.post("/api/email-capture", response_model=EmailCaptureResponse)
def email_capture(payload: EmailCaptureRequest, db: Session = Depends(get_db)):
    existing = db.query(EmailCapture).filter(EmailCapture.email == payload.email).first()
    if existing:
        return EmailCaptureResponse(message="Already on the 23 List")

    capture = EmailCapture(email=payload.email, created_at=datetime.utcnow())
    db.add(capture)
    db.commit()
    return EmailCaptureResponse(message="Welcome to the 23 List")


@app.post("/auth/request-code")
def request_code(payload: RequestCodePayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user = User(email=payload.email)
        db.add(user)
        db.flush()

    code = create_verification_code()
    user.verification_code = code
    db.commit()

    print(f"[DEBUG] Verification code for {payload.email}: {code}")
    return {"message": "Verification code sent"}


@app.post("/auth/verify-code", response_model=TokenResponse)
def verify_code(payload: VerifyCodePayload, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == payload.email).first()
        if not user or user.verification_code != payload.code:
            print(f"[ERROR] Invalid code for {payload.email}. User: {user}")
            raise HTTPException(status_code=400, detail="Invalid code")

        user.is_verified = True
        user.verification_code = None
        if payload.password:
            # Truncate password to 72 bytes for bcrypt, ensuring valid utf-8
            pw_bytes = payload.password.encode('utf-8')[:72]
            truncated_pw = pw_bytes.decode('utf-8', 'ignore')
            user.password_hash = get_password_hash(truncated_pw)
        db.commit()

        token = create_access_token(str(user.id))
        return TokenResponse(
            access_token=token, expires_in=token_expiry_seconds(settings.jwt_exp_minutes)
        )
    except Exception as e:
        print(f"[ERROR] Exception in verify_code: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    return TokenResponse(
        access_token=token, expires_in=token_expiry_seconds(settings.jwt_exp_minutes)
    )


@app.get("/api/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/api/creator", response_model=UserResponse)
def upsert_creator(
    payload: CreatorUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creator = current_user.creator
    if not creator:
        creator = Creator(user_id=current_user.id)
        db.add(creator)
        db.flush()

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(creator, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@app.post("/api/media", response_model=List[MediaBase])
def upload_media(
    media_type: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    creator = current_user.creator
    if not creator:
        raise HTTPException(status_code=400, detail="Create a profile first")

    if media_type not in {"image", "audio", "video"}:
        raise HTTPException(status_code=400, detail="Invalid media type")

    url = storage.save_upload_file(file, subdir="media")
    media_item = Media(
        creator_id=creator.id,
        media_type=media_type,
        url=url,
        title=title,
        description=description,
    )
    db.add(media_item)
    db.commit()
    db.refresh(creator)
    return creator.media_items


@app.post("/api/generate-barcode", response_model=BarcodeResponse)
def generate_barcode_endpoint(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    creator = current_user.creator
    if not creator or not creator.display_name:
        raise HTTPException(status_code=400, detail="Complete profile before generating")

    slug = creator.barcode_slug
    if not slug:
        slug = barcode_utils.generate_unique_slug(creator.display_name)
        while db.query(Creator).filter(Creator.barcode_slug == slug).first():
            slug = barcode_utils.generate_unique_slug(creator.display_name)
    barcode_url = barcode_utils.generate_barcode(slug)
    creator.barcode_slug = slug
    creator.barcode_image_url = barcode_url
    db.commit()

    return BarcodeResponse(slug=slug, barcode_url=barcode_url)


@app.put("/api/creator/publish", response_model=PublishResponse)
def publish_creator(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    creator = current_user.creator
    if not creator or not creator.barcode_slug:
        raise HTTPException(status_code=400, detail="Generate barcode first")

    creator.is_published = True
    db.commit()
    return PublishResponse(message="Creator is live", is_published=True)


@app.get("/creator/{slug}", response_model=CreatorBase)
def public_creator(slug: str, db: Session = Depends(get_db)):
    creator = db.query(Creator).filter(Creator.barcode_slug == slug).first()
    if not creator or not creator.is_published:
        raise HTTPException(status_code=404, detail="Creator not found")
    return creator

