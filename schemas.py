from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, constr


class EmailCaptureRequest(BaseModel):
    email: EmailStr


class EmailCaptureResponse(BaseModel):
    message: str


class RequestCodePayload(BaseModel):
    email: EmailStr


class VerifyCodePayload(BaseModel):
    email: EmailStr
    code: constr(min_length=4, max_length=10)
    password: Optional[constr(min_length=6)] = None


class LoginPayload(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MediaBase(BaseModel):
    id: int
    media_type: str
    url: str
    title: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class CreatorBase(BaseModel):
    id: int
    display_name: Optional[str]
    nickname: Optional[str]
    bio: Optional[str]
    instagram_url: Optional[HttpUrl]
    spotify_url: Optional[HttpUrl]
    other_links: Optional[List[str]]
    barcode_slug: Optional[str]
    barcode_image_url: Optional[str]
    profile_image_url: Optional[str]
    is_published: bool
    media_items: List[MediaBase] = Field(default_factory=list)

    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    creator: Optional[CreatorBase]

    class Config:
        orm_mode = True


class CreatorUpdatePayload(BaseModel):
    display_name: Optional[str]
    nickname: Optional[str]
    bio: Optional[str]
    instagram_url: Optional[HttpUrl]
    spotify_url: Optional[HttpUrl]
    other_links: Optional[List[str]]
    profile_image_url: Optional[str]


class MediaCreatePayload(BaseModel):
    media_type: constr(regex="^(image|audio|video)$")
    title: Optional[str]
    description: Optional[str]


class PublishResponse(BaseModel):
    message: str
    is_published: bool


class BarcodeResponse(BaseModel):
    slug: str
    barcode_url: str


def token_expiry_seconds(minutes: int) -> int:
    return int(timedelta(minutes=minutes).total_seconds())

