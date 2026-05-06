from fastapi import Request, HTTPException, status
from app.core.security import decode_and_validate_token

async def tenant_middleware(request: Request, call_next):
    tenant_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = decode_and_validate_token(token, expected_type="access")
            tenant_id = payload.get("tenant_id")
        except Exception:
            pass
    request.state.tenant_id = tenant_id
    response = await call_next(request)
    return response