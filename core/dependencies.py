
import hmac
import jwt

from fastapi import Depends, HTTPException, Request, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.dependencies import get_db
from models.admin import Admin
from core.security import SECRET_KEY, ALGORITHM


ACCESS_COOKIE_NAME = "admin_access_token"
CSRF_COOKIE_NAME = "admin_csrf_token"


def verify_csrf_token(request: Request) -> None:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")

    if (
        not cookie_token
        or not header_token
        or not hmac.compare_digest(cookie_token, header_token)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )


def get_current_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> Admin:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )

    # Validate CSRF for state-changing admin requests.
    verify_csrf_token(request)

    token = request.cookies.get(ACCESS_COOKIE_NAME)

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]},
        )

        admin_id = payload.get("sub")

        if not isinstance(admin_id, str) or not admin_id.isdigit():
            raise credentials_exception

        admin_id = int(admin_id)

    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    statement = select(Admin).where(Admin.id == admin_id)
    admin = db.scalars(statement).one_or_none()

    if admin is None or not admin.is_active:
        raise credentials_exception

    return admin
