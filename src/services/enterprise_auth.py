import json
import base64
import io
from typing import Optional

import pyotp
import qrcode
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc6749.util import scope_to_list

from src.database import get_db
from src.services.auth import create_access_token, hash_password


def get_oauth_provider_config(provider: str) -> Optional[dict]:
    configs = {
        "google": {
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scope": "openid email profile",
        },
        "github": {
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "scope": "read:user user:email",
        },
        "microsoft": {
            "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scope": "User.Read openid profile",
        },
    }
    return configs.get(provider)


def get_oauth_redirect_url(provider: str, redirect_uri: str, client_id: str, client_secret: str) -> str:
    config = get_oauth_provider_config(provider)
    if not config:
        raise ValueError(f"Unsupported OAuth provider: {provider}")

    session = OAuth2Session(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=config["scope"],
    )
    uri, _ = session.create_authorization_url(config["authorize_url"])
    return uri


def handle_oauth_callback(provider: str, code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
    config = get_oauth_provider_config(provider)
    if not config:
        raise ValueError(f"Unsupported OAuth provider: {provider}")

    session = OAuth2Session(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=config["scope"],
    )
    token = session.fetch_token(config["token_url"], authorization_response=f"{redirect_uri}?code={code}")

    userinfo_resp = session.get(config["userinfo_url"])
    userinfo = userinfo_resp.json()

    provider_user_id = str(userinfo.get("id") or userinfo.get("sub"))
    email = userinfo.get("email") or ""
    name = userinfo.get("name") or userinfo.get("login") or email.split("@")[0]

    with get_db() as conn:
        existing = conn.execute(
            "SELECT u.* FROM users u JOIN oauth_accounts o ON u.id = o.user_id WHERE o.provider = ? AND o.provider_user_id = ?",
            (provider, provider_user_id),
        ).fetchone()

        if existing:
            user = dict(existing)
        else:
            email_exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone() if email else None
            if email_exists:
                user_id = email_exists["id"]
                conn.execute("INSERT INTO oauth_accounts (user_id, provider, provider_user_id, provider_email, access_token) VALUES (?, ?, ?, ?, ?)",
                             (user_id, provider, provider_user_id, email, token.get("access_token", "")))
                user = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
            else:
                cur = conn.execute(
                    "INSERT INTO users (username, email, hashed_password, role) VALUES (?, ?, ?, ?)",
                    (name, email, hash_password(provider_user_id), "analyst"),
                )
                user_id = cur.lastrowid
                conn.execute("INSERT INTO oauth_accounts (user_id, provider, provider_user_id, provider_email, access_token) VALUES (?, ?, ?, ?, ?)",
                             (user_id, provider, provider_user_id, email, token.get("access_token", "")))
                user = {"id": user_id, "username": name, "email": email, "role": "analyst", "mfa_enabled": 0}

    access_token = create_access_token(user["id"], user["role"])
    return {"access_token": access_token, "token_type": "bearer", "user": user}


def setup_mfa(user_id: int) -> dict:
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=f"user_{user_id}", issuer_name="Cybersec Assistant")

    buf = io.BytesIO()
    img = qrcode.make(provisioning_uri)
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    with get_db() as conn:
        conn.execute("UPDATE users SET mfa_secret = ? WHERE id = ?", (secret, user_id))

    return {"secret": secret, "qr_code": f"data:image/png;base64,{qr_b64}"}


def verify_mfa(user_id: int, code: str) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT mfa_secret FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row or not row["mfa_secret"]:
        return False
    totp = pyotp.TOTP(row["mfa_secret"])
    return totp.verify(code)


def enable_mfa(user_id: int, code: str) -> bool:
    if not verify_mfa(user_id, code):
        return False
    with get_db() as conn:
        conn.execute("UPDATE users SET mfa_enabled = 1 WHERE id = ?", (user_id,))
    return True


def disable_mfa(user_id: int) -> None:
    with get_db() as conn:
        conn.execute("UPDATE users SET mfa_secret = '', mfa_enabled = 0 WHERE id = ?", (user_id,))


def authenticate_with_ldap(server: str, base_dn: str, username: str, password: str, user_filter: str = "(uid={username})", bind_dn: str = "", bind_password: str = "", attribute_map: str = "{}") -> Optional[dict]:
    try:
        import ldap3

        server_obj = ldap3.Server(server, get_info=ldap3.ALL)
        attrs = json.loads(attribute_map)

        if bind_dn and bind_password:
            conn = ldap3.Connection(server_obj, user=bind_dn, password=bind_password, auto_bind=True)
        else:
            conn = ldap3.Connection(server_obj, auto_bind=True)

        search_filter = user_filter.replace("{username}", username)
        conn.search(search_base=base_dn, search_filter=search_filter, attributes=ldap3.ALL_ATTRIBUTES)

        if len(conn.entries) == 0:
            return None

        entry = conn.entries[0]
        dn = entry.entry_dn

        user_conn = ldap3.Connection(server_obj, user=dn, password=password)
        if not user_conn.bind():
            return None

        username_attr = attrs.get("username", "uid")
        email_attr = attrs.get("email", "mail")

        ldap_username = str(getattr(entry, username_attr, [username])[0]) if hasattr(entry, username_attr) else username
        ldap_email = str(getattr(entry, email_attr, [""])[0]) if hasattr(entry, email_attr) else ""
        ldap_role = attrs.get("role", "")

        with get_db() as conn:
            existing = conn.execute("SELECT * FROM users WHERE username = ?", (ldap_username,)).fetchone()
            if existing:
                user = dict(existing)
            else:
                cur = conn.execute(
                    "INSERT INTO users (username, email, hashed_password, role) VALUES (?, ?, ?, ?)",
                    (ldap_username, ldap_email, hash_password(password), ldap_role or "analyst"),
                )
                user = {"id": cur.lastrowid, "username": ldap_username, "email": ldap_email, "role": ldap_role or "analyst", "mfa_enabled": 0}

        access_token = create_access_token(user["id"], user["role"])
        return {"access_token": access_token, "token_type": "bearer", "user": user}

    except Exception:
        return None
