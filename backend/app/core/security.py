"""Cryptographic security utilities: password hashing (Argon2 / PBKDF2) and JWT handling."""

import os
import hmac
import hashlib
import json
import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from app.core.config import settings

# Attempt Argon2 import; fallback to PBKDF2-HMAC-SHA256 if unavailable or blocked by OS policy
try:
    import argon2
    _hasher = argon2.PasswordHasher(
        time_cost=2,
        memory_cost=65536,
        parallelism=2,
        hash_len=32,
        salt_len=16,
    )
    _USE_ARGON2 = True
except (ImportError, Exception):
    _hasher = None
    _USE_ARGON2 = False


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2id (or high-iteration PBKDF2-SHA256 fallback).
    Never stores plaintext passwords.
    """
    if _USE_ARGON2 and _hasher is not None:
        try:
            return _hasher.hash(password)
        except Exception:
            pass

    # Secure fallback: PBKDF2 with HMAC-SHA256 and 600,000 iterations
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=600000,
    )
    return f"pbkdf2_sha256$600000${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plaintext password matches its hashed representation."""
    if hashed_password.startswith("$argon2"):
        if _USE_ARGON2 and _hasher is not None:
            try:
                return _hasher.verify(hashed_password, plain_password)
            except Exception:
                return False
        return False

    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            parts = hashed_password.split("$")
            if len(parts) != 4:
                return False
            _, iterations_str, salt, expected_hash = parts
            iterations = int(iterations_str)
            computed = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations=iterations,
            )
            return hmac.compare_digest(computed.hex(), expected_hash)
        except Exception:
            return False

    return False


def _b64encode_url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode_url(data: str) -> bytes:
    padding = "=" * (4 - (len(data) % 4)) if len(data) % 4 else ""
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims: Dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "access",
    }
    if extra_claims:
        claims.update(extra_claims)

    # Encode JWT using HMAC-SHA256
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64encode_url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode_url(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64encode_url(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    claims: Dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "refresh",
    }

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64encode_url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode_url(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64encode_url(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_token(token: str) -> Dict[str, Any]:
    """Verify signature and expiration of a JWT, returning payload claims."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT token format")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    expected_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    actual_sig = _b64decode_url(sig_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    payload_bytes = _b64decode_url(payload_b64)
    claims: Dict[str, Any] = json.loads(payload_bytes.decode("utf-8"))

    exp = claims.get("exp")
    if exp and datetime.now(timezone.utc).timestamp() > exp:
        raise ValueError("Token has expired")

    return claims
