from app.core.rbac import Permission, SystemRole, role_has_permission


def test_super_admin_has_platform_control() -> None:
    assert role_has_permission(SystemRole.SUPER_ADMIN, Permission.PLATFORM_ALL)


def test_customer_cannot_write_finance() -> None:
    assert not role_has_permission(SystemRole.CUSTOMER, Permission.FINANCE_WRITE)
