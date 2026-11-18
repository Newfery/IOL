import hashlib
import hmac

from passlib.context import CryptContext

from src.config.env import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def password_fingerprint(plain: str) -> str:
    secret = settings.PASSWORD_FINGERPRINT_SECRET or settings.JWT_SECRET
    key = hmac.new(
        secret.encode("utf-8"),
        b"IOL/inversor-password-fingerprint/v1",
        hashlib.sha256,
    ).digest()
    return hmac.new(key, plain.encode("utf-8"), hashlib.sha256).hexdigest()
