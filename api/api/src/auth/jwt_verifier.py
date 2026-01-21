from __future__ import annotations
import os, base64, logging, jwt
from jwt import PyJWKClient
from fastapi import HTTPException

log = logging.getLogger("uvicorn.error")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
JWT_AUD = os.getenv("SUPABASE_JWT_AUD", "authenticated")
RAW_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# JWKS client for ES256/RS256 tokens (cached)
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient | None:
    """Get or create JWKS client for asymmetric key verification."""
    global _jwks_client
    if _jwks_client is None and SUPABASE_URL:
        jwks_url = f"{SUPABASE_URL}/auth/v1/keys"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        log.info("AUTH: Initialized JWKS client for %s", jwks_url)
    return _jwks_client


def _decode_symmetric(token: str, secret: bytes | str) -> dict:
    """Decode token using symmetric HS256 algorithm."""
    return jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience=JWT_AUD,
        options={"verify_exp": True},
    )


def _decode_asymmetric(token: str) -> dict:
    """Decode token using asymmetric ES256/RS256 with JWKS."""
    jwks_client = _get_jwks_client()
    if not jwks_client:
        raise ValueError("JWKS client not available")

    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience=JWT_AUD,
        options={"verify_exp": True},
    )


def verify_jwt(token: str) -> dict:
    # Debug: log the token header to see what algorithm is being used
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        log.info("AUTH: Token header alg=%s typ=%s", alg, header.get("typ"))
    except Exception as e:
        log.error("AUTH: Failed to decode token header: %s", e)
        raise HTTPException(401, "Invalid token format")

    expected_iss = f"{SUPABASE_URL}/auth/v1" if SUPABASE_URL else None
    errors = []

    # 1) Try asymmetric verification for ES256/RS256 tokens
    if alg in ("ES256", "RS256"):
        try:
            claims = _decode_asymmetric(token)
            _post_checks(claims, expected_iss)
            log.info("AUTH: verified with JWKS (%s)", alg)
            return claims
        except Exception as e:
            errors.append(f"jwks:{type(e).__name__}:{e}")

    # 2) Try symmetric HS256 with raw secret
    if RAW_SECRET:
        try:
            claims = _decode_symmetric(token, RAW_SECRET)
            _post_checks(claims, expected_iss)
            log.info("AUTH: verified with RAW secret")
            return claims
        except Exception as e:
            errors.append(f"raw:{type(e).__name__}:{e}")

        # 3) Try base64-decoded secret as fallback
        try:
            claims = _decode_symmetric(token, base64.b64decode(RAW_SECRET))
            _post_checks(claims, expected_iss)
            log.info("AUTH: verified with BASE64-decoded secret")
            return claims
        except Exception as e:
            errors.append(f"b64:{type(e).__name__}:{e}")

    log.error("AUTH: JWT verification failed (%s)", " ; ".join(errors))
    raise HTTPException(401, "Invalid authentication token")


def _post_checks(claims: dict, expected_iss: str | None):
    iss = claims.get("iss")
    aud = claims.get("aud")
    sub = claims.get("sub")
    if expected_iss and iss != expected_iss:
        log.warning("AUTH: iss mismatch token=%s expected=%s", iss, expected_iss)
    if aud != JWT_AUD:
        # PyJWT already verifies aud; this log is just clarity
        log.warning("AUTH: aud mismatch token=%s expected=%s", aud, JWT_AUD)
    if not sub:
        raise HTTPException(401, "Token missing subject")


__all__ = ["verify_jwt"]

