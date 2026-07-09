from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.config import settings
from src.database import get_db
from src.schemas.auth import (
    LdapLoginRequest, LoginRequest, MfaLoginRequest, MfaSetupResponse,
    MfaVerifyRequest, OAuthLoginRequest, OAuthRedirectResponse,
    RegisterRequest, TokenResponse, UserResponse,
)
from src.services.auth import (
    create_access_token, get_current_user, hash_password,
    require_role, verify_password,
)
from src.services.enterprise_auth import (
    authenticate_with_ldap, disable_mfa, enable_mfa,
    get_oauth_redirect_url, handle_oauth_callback, setup_mfa, verify_mfa,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (body.username,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        email = body.email or f"{body.username}@cybersec.local"
        email_exists = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if email_exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        hashed = hash_password(body.password)
        cur = conn.execute(
            "INSERT INTO users (username, email, hashed_password, role) VALUES (?, ?, ?, ?)",
            (body.username, email, hashed, "analyst"),
        )
        token = create_access_token(cur.lastrowid, "analyst")
        return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (body.username,)).fetchone()
    if row is None or not verify_password(body.password, row["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if row["mfa_enabled"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MFA code required")
    token = create_access_token(row["id"], row["role"])
    return TokenResponse(access_token=token)


@router.post("/login/mfa", response_model=TokenResponse)
def login_with_mfa(body: MfaLoginRequest):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (body.username,)).fetchone()
    if row is None or not verify_password(body.password, row["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not row["mfa_enabled"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not enabled")
    if not verify_mfa(row["id"], body.mfa_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")
    token = create_access_token(row["id"], row["role"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"], username=user["username"], email=user["email"],
        role=user["role"], mfa_enabled=bool(user.get("mfa_enabled", 0)),
    )


@router.get("/admin-only")
def admin_only(user: dict = Depends(require_role("admin"))):
    return {"message": "Welcome admin", "user": user["username"]}


# ── OAuth 2.0 ──

@router.get("/oauth/{provider}/url", response_model=OAuthRedirectResponse)
def oauth_authorize_url(provider: str, redirect_uri: str = Query("")):
    client_id = getattr(settings, f"{provider}_client_id", "")
    client_secret = getattr(settings, f"{provider}_client_secret", "")
    if not client_id:
        # Use env vars with provider prefix
        import os
        client_id = os.getenv(f"{provider.upper()}_CLIENT_ID", "")
        client_secret = os.getenv(f"{provider.upper()}_CLIENT_SECRET", "")
    if not client_id:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"{provider} OAuth not configured")
    url = get_oauth_redirect_url(provider, redirect_uri or f"http://localhost:5173/auth/{provider}/callback", client_id, client_secret)
    return OAuthRedirectResponse(authorization_url=url)


@router.post("/oauth/{provider}/callback", response_model=TokenResponse)
def oauth_callback(provider: str, body: OAuthLoginRequest):
    import os
    client_id = getattr(settings, f"{provider}_client_id", "") or os.getenv(f"{provider.upper()}_CLIENT_ID", "")
    client_secret = getattr(settings, f"{provider}_client_secret", "") or os.getenv(f"{provider.upper()}_CLIENT_SECRET", "")
    if not client_id:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"{provider} OAuth not configured")
    result = handle_oauth_callback(provider, body.code, body.redirect_uri or f"http://localhost:5173/auth/{provider}/callback", client_id, client_secret)
    return TokenResponse(access_token=result["access_token"])


# ── MFA / TOTP ──

@router.post("/mfa/setup", response_model=MfaSetupResponse)
def setup_mfa_endpoint(user: dict = Depends(get_current_user)):
    return setup_mfa(user["id"])


@router.post("/mfa/verify")
def verify_mfa_endpoint(body: MfaVerifyRequest, user: dict = Depends(get_current_user)):
    if not verify_mfa(user["id"], body.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    return {"verified": True}


@router.post("/mfa/enable")
def enable_mfa_endpoint(body: MfaVerifyRequest, user: dict = Depends(get_current_user)):
    if not enable_mfa(user["id"], body.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    return {"mfa_enabled": True}


@router.post("/mfa/disable")
def disable_mfa_endpoint(user: dict = Depends(get_current_user)):
    disable_mfa(user["id"])
    return {"mfa_enabled": False}


# ── LDAP ──

@router.post("/ldap/login", response_model=TokenResponse)
def ldap_login(body: LdapLoginRequest):
    result = authenticate_with_ldap(
        server=body.server,
        base_dn=body.base_dn,
        username=body.username,
        password=body.password,
        user_filter=body.user_filter,
        bind_dn=body.bind_dn,
        bind_password=body.bind_password,
        attribute_map=body.attribute_map,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="LDAP authentication failed")
    return TokenResponse(access_token=result["access_token"])
