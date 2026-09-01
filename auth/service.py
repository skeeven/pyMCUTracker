"""Authentication and account creation services."""

import re

import bcrypt

from database.users import create_user, get_user_by_email

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for a plaintext password."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a plaintext password matches a bcrypt hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def validate_signup(
    name: str,
    email: str,
    password: str,
    confirm_password: str,
) -> list[str]:
    """Return validation messages for signup input."""
    errors = []

    if len(name.strip()) < 2:
        errors.append("Enter a display name with at least 2 characters.")

    if not EMAIL_PATTERN.match(email.strip()):
        errors.append("Enter a valid email address.")

    if len(password) < 8:
        errors.append("Password must contain at least 8 characters.")

    if password != confirm_password:
        errors.append("Passwords do not match.")

    return errors


def register_user(
    name: str,
    email: str,
    password: str,
    confirm_password: str,
):
    """Validate and create a new user account."""
    errors = validate_signup(name, email, password, confirm_password)
    if errors:
        return None, errors

    if get_user_by_email(email) is not None:
        return None, ["An account already exists for that email address."]

    password_hash = hash_password(password)
    user = create_user(name, email, password_hash)
    return user, []


def authenticate_user(email: str, password: str):
    """Return a verified active user, or None for invalid credentials."""
    user = get_user_by_email(email)
    if user is None:
        return None

    _, _, _, password_hash, is_active, _ = user
    if not is_active:
        return None

    if not verify_password(password, password_hash):
        return None

    return user
