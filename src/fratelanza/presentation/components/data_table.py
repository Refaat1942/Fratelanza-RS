"""Reusable table helpers for module views."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FieldSpec:
    """Input field definition for reusable forms."""

    key: str
    label: str
    placeholder: str = ""
    field_type: str = "text"


class DataTable(QWidget):
    """Simple database-backed table with refresh and optional search."""

    def __init__(
        self,
        *,
        title: str,
        columns: list[tuple[str, str]],
        load_rows: Callable[[str], list[dict[str, object]]],
        searchable: bool = True,
    ) -> None:
        super().__init__()
        self._columns = columns
        self._load_rows = load_rows
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search...")
        self._table = QTableWidget()
        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels([label for _, label in columns])
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)

        toolbar = QHBoxLayout()
        toolbar.addWidget(title_label)
        toolbar.addStretch()
        if searchable:
            toolbar.addWidget(self._search, stretch=1)
            self._search.returnPressed.connect(self.refresh)
        toolbar.addWidget(refresh_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(toolbar)
        layout.addWidget(self._table)
        self.refresh()

    def refresh(self) -> None:
        """Reload table rows."""
        try:
            rows = self._load_rows(self._search.text().strip())
        except Exception as exc:
            logger.exception("Failed to refresh table.")
            QMessageBox.critical(self, "Database error", str(exc))
            return
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, (key, _) in enumerate(self._columns):
                value = row.get(key)
                item = QTableWidgetItem("" if value is None else str(value))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_index, column_index, item)
        self._table.resizeColumnsToContents()
        self._table.setSortingEnabled(True)


class DataEntryPanel(QFrame):
    """Reusable add-record form."""

    def __init__(
        self,
        *,
        title: str,
        fields: list[FieldSpec],
        submit_label: str,
        on_submit: Callable[[dict[str, object]], None],
        on_success: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("Card")
        self._fields = fields
        self._on_submit = on_submit
        self._on_success = on_success
        self._widgets: dict[str, QLineEdit | QCheckBox] = {}

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        form = QFormLayout()
        for field in fields:
            if field.field_type == "bool":
                widget = QCheckBox()
            else:
                widget = QLineEdit()
                widget.setPlaceholderText(field.placeholder)
            self._widgets[field.key] = widget
            form.addRow(field.label, widget)

        submit = QPushButton(submit_label)
        submit.setObjectName("PrimaryButton")
        submit.clicked.connect(self._submit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(title_label)
        layout.addLayout(form)
        layout.addWidget(submit)

    def _submit(self) -> None:
        values: dict[str, object] = {}
        for key, widget in self._widgets.items():
            if isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            else:
                values[key] = widget.text().strip()
        try:
            self._on_submit(values)
        except Exception as exc:
            logger.exception("Failed to submit form.")
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        for widget in self._widgets.values():
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)
            else:
                widget.clear()
        if self._on_success is not None:
            self._on_success()
        QMessageBox.information(self, "Saved", "Record saved successfully.")
