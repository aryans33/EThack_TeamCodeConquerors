from fastapi import HTTPException, Header, Depends
from app.config.settings import get_settings

settings = get_settings()


async def verify_internal_api_key(x_api_key: str = Header(None)):
    """
    Middleware to verify internal API key for service-to-service calls.
    Used to protect endpoints that should only be called by the Node.js backend.
    """
    if x_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing internal API key."
        )
    return x_api_key
