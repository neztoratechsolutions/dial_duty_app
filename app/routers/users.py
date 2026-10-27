import os
import uuid
import smtplib
import secrets
import hashlib

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import jwt,JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_db
from app.models.user import User
from app.models.role import Role


load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

security = HTTPBearer()
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

ALGORITHM = "HS256"
OTP_EXPIRY_MINUTES = 5
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_OTP_ATTEMPTS = 5

ALLOWED_ROLES = {"customer", "delivery boy", "vendor"}

# Development use only.
# For production, use Redis or database storage.
login_otps = {}


# -------------------- SCHEMAS --------------------

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    role: str = Field(..., min_length=1, max_length=50)


class LoginRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r"^\d{6}$")


# -------------------- HELPERS --------------------

def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_role(role: str) -> str:
    return " ".join(role.strip().lower().split())


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def send_email_otp(email: str, otp: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="Email SMTP configuration is missing"
        )

    message = EmailMessage()
    message["Subject"] = "Dial Duty - Login OTP"
    message["From"] = SMTP_EMAIL
    message["To"] = email

    message.set_content(
        f"Hello,\n\n"
        f"Your Dial Duty login OTP is: {otp}\n\n"
        f"This OTP expires in {OTP_EXPIRY_MINUTES} minutes.\n"
        f"You can use this OTP to complete your login.\n\n"
        f"If you did not request this OTP, please ignore this email."
    )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(message)

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to send OTP email. Please try again."
        )


def generate_referral_code(db: Session) -> str:
    for _ in range(10):
        code = uuid.uuid4().hex[:10].upper()

        exists = (
            db.query(User.id)
            .filter(User.referral_code == code)
            .first()
        )

        if not exists:
            return code

    raise HTTPException(
        status_code=500,
        detail="Unable to generate referral code"
    )


def generate_placeholder_mobile(db: Session) -> str:
    # Current User model requires a unique mobile_number.
    # Replace this with a real mobile-number flow if needed.
    for _ in range(10):
        mobile = "PENDING" + uuid.uuid4().hex[:13].upper()

        exists = (
            db.query(User.id)
            .filter(User.mobile_number == mobile)
            .first()
        )

        if not exists:
            return mobile

    raise HTTPException(
        status_code=500,
        detail="Unable to generate internal mobile placeholder"
    )


def get_active_role(db: Session, role_name: str):
    return (
        db.query(Role)
        .filter(
            func.lower(func.trim(Role.name)) == role_name,
            Role.status.is_(True)
        )
        .first()
    )


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role_id,
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# -------------------- REGISTER --------------------

@router.post("/register", status_code=201)
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    name = request.name.strip()
    email = normalize_email(str(request.email))
    role_name = normalize_role(request.role)

    if len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Full name must contain at least 2 characters"
        )

    if role_name not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Allowed roles: Customer, Delivery Boy, Vendor"
        )

    existing_user = (
        db.query(User)
        .filter(func.lower(User.email) == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered. Please login."
        )

    role = get_active_role(db, role_name)

    if not role:
        existing_role = (
            db.query(Role)
            .filter(
                func.lower(func.trim(Role.name)) == role_name
            )
            .first()
        )

        if existing_role:
            raise HTTPException(
                status_code=400,
                detail=f"Role '{existing_role.name}' is inactive"
            )

        raise HTTPException(
            status_code=400,
            detail=f"Role '{request.role}' not found in roles table"
        )

    user = User(
        name=name,
        email=email,
        # Placeholder because the current model requires a password.
        # This flow does not authenticate users using this value.
        password=hash_value(secrets.token_urlsafe(32)),
        mobile_number=generate_placeholder_mobile(db),
        address=None,
        role_id=role.id,
        referral_code=generate_referral_code(db),
        referred_by=None,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create user account"
        )

    # No OTP is sent during registration.
    return {
        "message": "Registration successful. Please login to receive OTP.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": role.name,
            "role_id": user.role_id,
            "referral_code": user.referral_code
        }
    }


# -------------------- LOGIN: SEND OTP --------------------

@router.post("/login", status_code=200)
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    name = request.name.strip()
    email = normalize_email(str(request.email))

    user = (
        db.query(User)
        .filter(
            func.lower(User.name) == name.lower(),
            func.lower(User.email) == email
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid name or email"
        )

    otp = f"{secrets.randbelow(1000000):06d}"

    # Send OTP only during login.
    send_email_otp(email, otp)

    login_otps[email] = {
        "user_id": user.id,
        "otp_hash": hash_value(otp),
        "expires_at": (
            datetime.now(timezone.utc)
            + timedelta(minutes=OTP_EXPIRY_MINUTES)
        ),
        "attempts": 0,
    }

    return {
        "message": "Login OTP sent to your email.",
        "email": email,
        "expires_in_minutes": OTP_EXPIRY_MINUTES
    }


# -------------------- VERIFY LOGIN OTP --------------------

@router.post("/verify-otp", status_code=200)
def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    email = normalize_email(str(request.email))
    otp = request.otp

    pending = login_otps.get(email)

    if not pending:
        raise HTTPException(
            status_code=400,
            detail="No pending login OTP found. Please login again."
        )

    now = datetime.now(timezone.utc)

    if now >= pending["expires_at"]:
        login_otps.pop(email, None)

        raise HTTPException(
            status_code=400,
            detail="OTP expired. Please login again."
        )

    if pending["attempts"] >= MAX_OTP_ATTEMPTS:
        login_otps.pop(email, None)

        raise HTTPException(
            status_code=429,
            detail="Too many incorrect OTP attempts. Please login again."
        )

    submitted_hash = hash_value(otp)

    if not secrets.compare_digest(
        submitted_hash,
        pending["otp_hash"]
    ):
        pending["attempts"] += 1

        if pending["attempts"] >= MAX_OTP_ATTEMPTS:
            login_otps.pop(email, None)

            raise HTTPException(
                status_code=429,
                detail="Too many incorrect OTP attempts. Please login again."
            )

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    user = (
        db.query(User)
        .filter(
            User.id == pending["user_id"],
            func.lower(User.email) == email
        )
        .first()
    )

    if not user:
        login_otps.pop(email, None)

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    access_token = create_access_token(user)

    # OTP can be used only once.
    login_otps.pop(email, None)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role_id": user.role_id
        }
    }


# -------------------- GET LOGGED-IN USER PROFILE --------------------

@router.get("/me",status_code = 200)
def get_logged_in_user(
    credentials : HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token , 
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user