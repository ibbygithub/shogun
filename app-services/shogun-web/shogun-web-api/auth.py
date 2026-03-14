import os
from fastapi import HTTPException, Request
from pydantic import BaseModel


class User(BaseModel):
    id: int
    email: str
    name: str
    role: str  # "admin" | "edit" | "read"


BYPASS_AUTH = os.getenv("SHOGUN_BYPASS_AUTH", "false").lower() == "true"


def decode_cf_jwt(token: str) -> User:
    # Production path: decode Cloudflare Access JWT
    # CF_ACCESS_CERTS_URL = https://{team}.cloudflareaccess.com/cdn-cgi/access/certs
    raise HTTPException(status_code=501, detail="CF JWT auth not yet implemented")


def get_current_user(request: Request) -> User:
    if BYPASS_AUTH:
        # Internal testing: return Todd as default admin
        return User(id=1, email="todd@ibbytech.com", name="Todd", role="admin")

    cf_jwt = request.headers.get("CF-Authorization")
    if not cf_jwt:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return decode_cf_jwt(cf_jwt)


def require_admin(user: User) -> User:
    if user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def require_edit(user: User) -> User:
    if user.role not in ("admin", "edit"):
        raise HTTPException(status_code=403, detail="Edit role required")
    return user
