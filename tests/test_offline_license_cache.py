from datetime import datetime, timedelta, timezone

from fratelanza.application.license import LicenseState
from fratelanza.application.offline_license_cache import CachedLicensePolicy, OfflineLicenseCache


def test_offline_license_cache_round_trip(tmp_path) -> None:
    cache = OfflineLicenseCache(tmp_path / "license.json")
    policy = CachedLicensePolicy(
        state=LicenseState.ACTIVE,
        client_id="CUST-001",
        installation_id="INSTALL-001",
        database_key="fratelanza_cust_001",
        allow_until=datetime.now(timezone.utc) + timedelta(hours=1),
        message="ok",
    )

    cache.save(policy)
    loaded = cache.load()

    assert loaded is not None
    assert loaded.client_id == "CUST-001"
    assert loaded.database_key == "fratelanza_cust_001"
    assert loaded.can_run_now
