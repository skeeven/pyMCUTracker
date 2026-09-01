"""Tests for authentication validation and password hashing."""

from auth.service import (
    hash_password,
    validate_password_reset,
    validate_signup,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    """A generated bcrypt hash should verify only the original password."""
    password_hash = hash_password("assemble123")

    assert verify_password("assemble123", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_validate_signup_accepts_valid_input() -> None:
    """Valid signup data should return no validation errors."""
    errors = validate_signup(
        "Steve",
        "steve@example.com",
        "assemble123",
        "assemble123",
    )

    assert errors == []


def test_validate_signup_reports_all_common_errors() -> None:
    """Signup validation should report name, email, length, and match errors."""
    errors = validate_signup(
        "S",
        "not-an-email",
        "short",
        "different",
    )

    assert len(errors) == 4
    assert any("display name" in error.lower() for error in errors)
    assert any("valid email" in error.lower() for error in errors)
    assert any("at least 8" in error.lower() for error in errors)
    assert any("do not match" in error.lower() for error in errors)


def test_validate_password_reset_enforces_length_and_match() -> None:
    """Password resets should use the same minimum safety rules as signup."""
    errors = validate_password_reset("short", "other")

    assert len(errors) == 2
    assert any("at least 8" in error.lower() for error in errors)
    assert any("do not match" in error.lower() for error in errors)
