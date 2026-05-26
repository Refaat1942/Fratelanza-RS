"""Admin panel view for VPS control and client branding."""

from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from fratelanza.application.branding_service import BrandingProfile
from fratelanza.application.remote_admin_service import RemoteAdminService
from fratelanza.core.i18n import Localizer


class AdminPanelView(QWidget):
    """Display remote-admin, licensing, support, and branding state."""

    def __init__(
        self,
        *,
        localizer: Localizer,
        branding: BrandingProfile,
        remote_admin_service: RemoteAdminService,
    ) -> None:
        super().__init__()
        self._localizer = localizer
        self._branding = branding
        self._remote_admin_service = remote_admin_service
        self._build()

    def _build(self) -> None:
        status = self._remote_admin_service.current_status()

        title = QLabel(self._localizer.gettext("remote.title"))
        title.setObjectName("Title")

        warning = QLabel(self._localizer.gettext("remote.warning"))
        warning.setObjectName("Muted")
        warning.setWordWrap(True)

        card = QFrame()
        card.setObjectName("Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(24, 24, 24, 24)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(12)

        rows = [
            (self._localizer.gettext("remote.api_base"), status.api_base_url or "-"),
            (self._localizer.gettext("remote.client_id"), status.client_id or "-"),
            (self._localizer.gettext("remote.installation_id"), status.installation_id or "-"),
            (self._localizer.gettext("remote.license_state"), status.state.value),
            (
                self._localizer.gettext("remote.allow_remote_support"),
                self._localizer.gettext("common.yes")
                if status.allow_remote_support
                else self._localizer.gettext("common.no"),
            ),
            (
                self._localizer.gettext("remote.last_heartbeat"),
                status.last_heartbeat_at.isoformat() if status.last_heartbeat_at else "-",
            ),
            ("Brand", self._branding.display_name),
            ("Logo", str(self._branding.logo_path) if self._branding.logo_path else "-"),
        ]

        for row_index, (label, value) in enumerate(rows):
            label_widget = QLabel(label)
            label_widget.setObjectName("Muted")
            value_widget = QLabel(value)
            value_widget.setWordWrap(True)
            grid.addWidget(label_widget, row_index, 0)
            grid.addWidget(value_widget, row_index, 1)

        if status.message:
            message = QLabel(status.message)
            message.setObjectName("Muted")
            message.setWordWrap(True)
            grid.addWidget(message, len(rows), 0, 1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(warning)
        layout.addWidget(card)
        layout.addStretch()
