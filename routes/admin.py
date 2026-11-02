
import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.dependencies import get_db
from models.admin import Admin
from schemas.auth import AdminLogin
from core.security import verify_password, create_access_token
from core.dependencies import (
    ACCESS_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    get_current_admin,
    verify_csrf_token,
)


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Authentication"],
)

COOKIE_SECURE = os.getenv(
    "COOKIE_SECURE", "false"
).lower() == "true"

COOKIE_SAMESITE = os.getenv(
    "COOKIE_SAMESITE", "lax"
).lower()

if COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise ValueError("Invalid COOKIE_SAMESITE setting")

if COOKIE_SAMESITE == "none" and not COOKIE_SECURE:
    raise ValueError("SameSite=None requires Secure cookies")


@router.get("/csrf")
def get_csrf_token(response: Response):
    csrf_token = secrets.token_urlsafe(32)

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=1800,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )

    return {"csrf_token": csrf_token}


@router.post("/login")
def admin_login(
    login_data: AdminLogin,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(verify_csrf_token),
):
    statement = select(Admin).where(
        Admin.username == login_data.username
    )

    admin = db.scalars(statement).one_or_none()

    if not admin or not verify_password(
        login_data.password,
        admin.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    access_token = create_access_token(
        {"sub": str(admin.id)}
    )

    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=1800,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )

    return {
        "message": "Login successful",
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
        },
    }


@router.get("/me")
def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin),
):
    return {
        "id": current_admin.id,
        "username": current_admin.username,
        "email": current_admin.email,
        "is_active": current_admin.is_active,
    }


@router.post("/logout")
def admin_logout(
    response: Response,
    _: None = Depends(verify_csrf_token),
):
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite=COOKIE_SAMESITE,
    )

    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite=COOKIE_SAMESITE,
    )

    return {"message": "Logged out successfully"}
