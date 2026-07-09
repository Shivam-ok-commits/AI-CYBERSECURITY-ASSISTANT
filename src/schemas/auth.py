from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    mfa_enabled: bool = False


class OAuthLoginRequest(BaseModel):
    provider: str
    code: str
    redirect_uri: str = ""


class OAuthRedirectResponse(BaseModel):
    authorization_url: str


class MfaSetupResponse(BaseModel):
    secret: str
    qr_code: str


class MfaVerifyRequest(BaseModel):
    code: str


class MfaLoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: str


class LdapLoginRequest(BaseModel):
    server: str
    base_dn: str
    bind_dn: str = ""
    bind_password: str = ""
    user_filter: str = "(uid={username})"
    attribute_map: str = '{"username": "uid", "email": "mail", "role": ""}'
    username: str
    password: str
