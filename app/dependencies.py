
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if not SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET_KEY is missing",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = int(payload.get("sub"))

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.role or not user.role.status:
        raise HTTPException(status_code=403, detail="User role is inactive")

    return user


def require_vendor_or_admin(
    current_user: User = Depends(get_current_user),
):
    role_name = current_user.role.name.strip().lower()

    if role_name not in ("vendor", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only Vendor and Admin can access Product APIs",
        )

    return current_user


def require_super_admin(
    current_user: User = Depends(get_current_user),
):
    role_name = (
        current_user.role.name.strip().lower()
        .replace("_", " ")
        .replace("-", " ")
    ) if current_user.role else ""

    if role_name not in ("super admin", "superadmin"):
        raise HTTPException(
            status_code=403,
            detail="Only Super Admin can approve or reject products"
        )

    return current_user
