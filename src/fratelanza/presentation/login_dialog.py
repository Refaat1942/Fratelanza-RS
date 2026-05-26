"""Login dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from fratelanza.application.auth_service import AuthService
from fratelanza.application.session import UserSession
from fratelanza.core.exceptions import AuthenticationError, FratelanzaError


class LoginDialog(QDialog):
    """Modern login screen for multi-user authentication."""

    def __init__(self, auth_service: AuthService, product_name: str, brand_name: str) -> None:
        super().__init__()
        self._auth_service = auth_service
        self.session: UserSession | None = None
        self.setObjectName("LoginDialog")
        self.setWindowTitle(f"{product_name} - Login")
        self.setMinimumSize(460, 520)
        self._build(brand_name, product_name)

    def _build(self, brand_name: str, product_name: str) -> None:
        brand = QLabel(brand_name.upper())
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet("font-size: 30px; font-weight: 900; letter-spacing: 2px;")

        title = QLabel(product_name)
        title.setObjectName("Muted")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._username = QLineEdit()
        self._username.setPlaceholderText("Username")
        self._username.setText("admin")

        self._password = QLineEdit()
        self._password.setPlaceholderText("Password")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.returnPressed.connect(self._login)

        login_button = QPushButton("Sign in")
        login_button.setObjectName("PrimaryButton")
        login_button.clicked.connect(self._login)

        hint = QLabel("Default first-run user: admin / Admin@12345")
        hint.setObjectName("Muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form = QVBoxLayout()
        form.setSpacing(14)
        form.addWidget(self._username)
        form.addWidget(self._password)
        form.addWidget(login_button)
        form.addWidget(hint)

        frame = QVBoxLayout(self)
        frame.setContentsMargins(42, 42, 42, 42)
        frame.setSpacing(18)
        frame.addStretch()
        frame.addWidget(brand)
        frame.addWidget(title)
        frame.addSpacing(24)
        frame.addLayout(form)
        frame.addStretch()

        footer = QHBoxLayout()
        footer.addStretch()
        footer_label = QLabel("Secure SQL Server login")
        footer_label.setObjectName("Muted")
        footer.addWidget(footer_label)
        footer.addStretch()
        frame.addLayout(footer)

    def _login(self) -> None:
        try:
            self.session = self._auth_service.login(self._username.text(), self._password.text())
        except AuthenticationError as exc:
            QMessageBox.warning(self, "Login failed", str(exc))
            return
        except FratelanzaError as exc:
            QMessageBox.critical(self, "System error", str(exc))
            return
        self.accept()
