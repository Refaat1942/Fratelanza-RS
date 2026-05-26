from fratelanza.core.security import PasswordPolicy, hash_password, verify_password


def test_password_hash_round_trip() -> None:
    encoded = hash_password("Admin@12345")

    assert verify_password("Admin@12345", encoded)
    assert not verify_password("wrong-password", encoded)


def test_password_policy_reports_missing_requirements() -> None:
    errors = PasswordPolicy().validate("short")

    assert "Password must be at least 8 characters." in errors
    assert "Password must include an uppercase letter." in errors
    assert "Password must include a number." in errors
    assert "Password must include a symbol." in errors
