"""Tests for JWKS-backed JWT verification."""

from __future__ import annotations

import importlib
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture()
def jwks_env(monkeypatch):
    """Provide a mock JWKS endpoint and return signing key and module."""

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(public_key))
    public_jwk["kid"] = "test-kid"

    jwks = {"keys": [public_jwk]}

    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://example.supabase.co/auth/v1/keys")
    monkeypatch.setenv("SUPABASE_JWKS_ISSUER", "https://example.supabase.co/auth/v1")
    monkeypatch.setenv("SUPABASE_JWT_AUD", "authenticated")

    import auth.jwt_verifier as jv

    def mock_get(url, timeout=5):  # noqa: D401
        class Resp:
            status_code = 200

            def json(self):
                return jwks

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setattr(jv.requests, "get", mock_get)
    importlib.reload(jv)

    # reset cache
    jv._JWKS_CACHE.clear()
    jv._JWKS_LAST_FETCH = 0

    return private_key, jv


def _create_token(key, **claims):
    payload = {
        "sub": "user123",
        "iss": "https://example.supabase.co/auth/v1",
        "aud": "authenticated",
        "exp": int(time.time()) + 60,
    }
    payload.update(claims)
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": "test-kid"})


def test_valid_token(jwks_env):
    key, jv = jwks_env
    token = _create_token(key)
    payload = jv.verify_jwt(token)
    assert payload["sub"] == "user123"


def test_expired_token(jwks_env):
    key, jv = jwks_env
    token = _create_token(key, exp=int(time.time()) - 10)
    with pytest.raises(jwt.ExpiredSignatureError):
        jv.verify_jwt(token)


def test_wrong_issuer(jwks_env):
    key, jv = jwks_env
    token = _create_token(key, iss="https://other.example.com")
    with pytest.raises(jwt.InvalidIssuerError):
        jv.verify_jwt(token)


def test_wrong_audience(jwks_env):
    key, jv = jwks_env
    token = _create_token(key, aud="other")
    with pytest.raises(jwt.InvalidAudienceError):
        jv.verify_jwt(token)


def test_forged_token_rejected(jwks_env):
    _, jv = jwks_env
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _create_token(other_key)
    with pytest.raises(jwt.InvalidTokenError):
        jv.verify_jwt(token)

