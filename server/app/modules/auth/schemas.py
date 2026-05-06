from typing import Optional

from pydantic import BaseModel, EmailStr

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_domain: str | None = None
    mfa_code: Optional[str] = None
    keep_logged_in: bool = False
    
class MFASetupResponse(BaseModel):
    secret: str
    qr_code_uri: str

class MFAVerifyRequest(BaseModel):
    code: str

class RefreshRequest(BaseModel):
    refresh_token: str