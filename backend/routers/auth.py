from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LoginRequest, RegisterRequest, ResyCredentialsIn, TokenResponse, UserOut
from services.security import (
    create_access_token,
    decode_token,
    encrypt,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer()


# ── Dependency ────────────────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        has_resy_credentials=bool(current_user.resy_email_enc),
        created_at=current_user.created_at,
    )


@router.put("/credentials", response_model=UserOut)
def update_credentials(
    payload: ResyCredentialsIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.resy_email_enc = encrypt(payload.resy_email)
    current_user.resy_password_enc = encrypt(payload.resy_password)
    current_user.resy_api_key_enc = encrypt(payload.resy_api_key)
    db.commit()
    db.refresh(current_user)

    return UserOut(
        id=current_user.id,
        email=current_user.email,
        has_resy_credentials=True,
        created_at=current_user.created_at,
    )
