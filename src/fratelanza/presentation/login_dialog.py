"""Login dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from fratelanza.application.auth_service import AuthService
from fratelanza.application.branding_service import BrandingProfile
from fratelanza.application.session import UserSession
from fratelanza.core.exceptions import AuthenticationError, FratelanzaError
from fratelanza.core.i18n import Localizer, SUPPORTED_LOCALES


class LoginDialog(QDialog):
    """Modern login screen for multi-user authentication."""

    def __init__(
        self,
        auth_service: AuthService,
        localizer: Localizer,
        branding: BrandingProfile,
    ) -> None:
        super().__init__()
        self._auth_service = auth_service
        self._localizer = localizer
        self._branding = branding
        self.session: UserSession | None = None
        self.setObjectName("LoginDialog")
        self.setWindowTitle(f"{branding.product_name} - Login")
        self.setMinimumSize(460, 520)
        self._build()
        self._apply_translations()

    def _build(self) -> None:
        self._brand = QLabel(self._branding.display_name.upper())
        self._brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._brand.setStyleSheet("font-size: 30px; font-weight: 900; letter-spacing: 2px;")

        self._title = QLabel(self._branding.product_name)
        self._title.setObjectName("Muted")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self._branding.has_logo:
            pixmap = QPixmap(str(self._branding.logo_path))
            logo.setPixmap(
                pixmap.scaled(
                    150,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        self._username = QLineEdit()
        self._username.setText("admin")

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.returnPressed.connect(self._login)

        self._language = QComboBox()
        for code, name in SUPPORTED_LOCALES.items():
            self._language.addItem(name, code)
        self._language.setCurrentIndex(
            max(0, self._language.findData(self._localizer.locale.code))
        )
        self._language.currentIndexChanged.connect(self._switch_language)

        self._login_button = QPushButton()
        self._login_button.setObjectName("PrimaryButton")
        self._login_button.clicked.connect(self._login)

        self._hint = QLabel()
        self._hint.setObjectName("Muted")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form = QVBoxLayout()
        form.setSpacing(14)
        form.addWidget(self._language)
        form.addWidget(self._username)
        form.addWidget(self._password)
        form.addWidget(self._login_button)
        form.addWidget(self._hint)

        frame = QVBoxLayout(self)
        frame.setContentsMargins(42, 42, 42, 42)
        frame.setSpacing(18)
        frame.addStretch()
        if self._branding.has_logo:
            frame.addWidget(logo)
        frame.addWidget(self._brand)
        frame.addWidget(self._title)
        frame.addSpacing(24)
        frame.addLayout(form)
        frame.addStretch()

        footer = QHBoxLayout()
        footer.addStretch()
        self._footer_label = QLabel()
        self._footer_label.setObjectName("Muted")
        footer.addWidget(self._footer_label)
        footer.addStretch()
        frame.addLayout(footer)

    def _apply_translations(self) -> None:
        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self._localizer.locale.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )
        self._username.setPlaceholderText(self._localizer.gettext("auth.username"))
        self._password.setPlaceholderText(self._localizer.gettext("auth.password"))
        self._login_button.setText(self._localizer.gettext("auth.sign_in"))
        self._hint.setText(self._localizer.gettext("auth.default_hint"))
        self._footer_label.setText(self._localizer.gettext("app.secure_login"))

    def _switch_language(self) -> None:
        locale = self._language.currentData()
        if isinstance(locale, str):
            self._localizer.switch(locale)
            self._apply_translations()

    def _login(self) -> None:
        try:
            self.session = self._auth_service.login(self._username.text(), self._password.text())
        except AuthenticationError as exc:
            QMessageBox.warning(self, self._localizer.gettext("auth.login_failed"), str(exc))
            return
        except FratelanzaError as exc:
            QMessageBox.critical(self, self._localizer.gettext("auth.system_error"), str(exc))
            return
        self.accept()
