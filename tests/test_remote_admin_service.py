from fratelanza.application.remote_admin_service import LicenseState, RemoteAdminService
from fratelanza.core.config import RemoteAdminSettings


class FakeClient:
    def heartbeat(self, payload: dict[str, object]) -> dict[str, object]:
        assert payload["installation_id"] == "install-1"
        return {"state": "active", "message": "ok"}


def test_remote_admin_not_configured_allows_local_use() -> None:
    service = RemoteAdminService(
        RemoteAdminSettings(
            enabled=False,
            api_base_url="",
            api_key="",
            client_id="",
            installation_id="",
            allow_remote_support=False,
            allow_remote_disable=True,
        )
    )

    status = service.sync_installation(app_version="0.1.0", machine_name="test")

    assert status.state == LicenseState.NOT_CONFIGURED
    assert status.can_run


def test_remote_admin_heartbeat_updates_status() -> None:
    service = RemoteAdminService(
        RemoteAdminSettings(
            enabled=True,
            api_base_url="https://vps.example.com/api",
            api_key="secret",
            client_id="client-1",
            installation_id="install-1",
            allow_remote_support=True,
            allow_remote_disable=True,
        ),
        client=FakeClient(),
    )

    status = service.sync_installation(app_version="0.1.0", machine_name="test")

    assert status.state == LicenseState.ACTIVE
    assert status.client_id == "client-1"
    assert status.allow_remote_support
