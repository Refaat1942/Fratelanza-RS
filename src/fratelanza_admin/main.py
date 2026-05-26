"""Admin desktop console entry point."""

from __future__ import annotations

import secrets
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fratelanza_admin.client import AdminApiClient, load_admin_settings


class AdminConsole(QWidget):
    """Laptop admin EXE for managing customers on the VPS."""

    def __init__(self, client: AdminApiClient) -> None:
        super().__init__()
        self._client = client
        self.setWindowTitle("Fratelanza Admin Console")
        self.resize(1100, 720)
        self._build()
        self.refresh()

    def _build(self) -> None:
        title = QLabel("Fratelanza VPS Admin Console")
        title.setStyleSheet("font-size: 24px; font-weight: 800;")
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Customer ID", "Name", "Database", "State", "Grace Hours", "API Key"]
        )

        self._customer_id = QLineEdit()
        self._display_name = QLineEdit()
        self._database_key = QLineEdit()
        self._api_key = QLineEdit()
        self._state_customer_id = QLineEdit()
        self._state = QComboBox()
        self._state.addItems(["active", "suspended", "expired"])

        generate_key = QPushButton("Generate API Key")
        generate_key.clicked.connect(self._generate_key)
        create = QPushButton("Create Customer")
        create.clicked.connect(self._create_customer)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        update_state = QPushButton("Update License State")
        update_state.clicked.connect(self._update_state)
        database_info = QPushButton("Show Customer Database Path")
        database_info.clicked.connect(self._database_info)

        form = QFormLayout()
        form.addRow("Customer ID", self._customer_id)
        form.addRow("Display Name", self._display_name)
        form.addRow("Database Key", self._database_key)
        form.addRow("Customer API Key", self._api_key)
        form.addRow(generate_key)
        form.addRow(create)
        form.addRow(refresh)
        form.addRow("State Customer ID", self._state_customer_id)
        form.addRow("State", self._state)
        form.addRow(update_state)
        form.addRow(database_info)

        layout = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(title)
        left.addWidget(self._table)
        layout.addLayout(left, stretch=3)
        layout.addLayout(form, stretch=1)
        self.setLayout(layout)

    def refresh(self) -> None:
        try:
            customers = self._client.list_customers()
        except Exception as exc:
            QMessageBox.critical(self, "VPS error", str(exc))
            return
        self._table.setRowCount(len(customers))
        for row_index, customer in enumerate(customers):
            values = [
                customer.get("customer_id", ""),
                customer.get("display_name", ""),
                customer.get("database_key", ""),
                customer.get("license_state", ""),
                customer.get("offline_grace_hours", ""),
                customer.get("api_key", ""),
            ]
            for column_index, value in enumerate(values):
                self._table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
        self._table.resizeColumnsToContents()

    def _generate_key(self) -> None:
        self._api_key.setText(secrets.token_urlsafe(32))

    def _create_customer(self) -> None:
        try:
            self._client.create_customer(
                customer_id=self._customer_id.text().strip(),
                display_name=self._display_name.text().strip(),
                database_key=self._database_key.text().strip(),
                api_key=self._api_key.text().strip(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Create failed", str(exc))
            return
        self.refresh()
        QMessageBox.information(self, "Created", "Customer created on VPS.")

    def _update_state(self) -> None:
        try:
            self._client.update_state(self._state_customer_id.text().strip(), self._state.currentText())
        except Exception as exc:
            QMessageBox.critical(self, "Update failed", str(exc))
            return
        self.refresh()

    def _database_info(self) -> None:
        try:
            payload = self._client.database_info(self._state_customer_id.text().strip())
        except Exception as exc:
            QMessageBox.critical(self, "Lookup failed", str(exc))
            return
        QMessageBox.information(self, "Database", str(payload))


def main() -> int:
    app = QApplication(sys.argv)
    console = AdminConsole(AdminApiClient(load_admin_settings()))
    console.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
