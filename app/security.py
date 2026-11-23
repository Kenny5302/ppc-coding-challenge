"""API-key authentication for write endpoints."""
import hmac
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    key: str | None = Depends(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    valid = settings.api_key_set
    if key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API key", {"WWW-Authenticate": "ApiKey"})
    # constant-time comparison against every configured key
    if not any(hmac.compare_digest(key.encode(), k.encode()) for k in valid):
        logger.warning("auth_failed", extra={"reason": "invalid_api_key"})
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid API key")
