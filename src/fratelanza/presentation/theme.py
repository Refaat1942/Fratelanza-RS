"""Reusable Qt style sheets and theme tokens."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    background: str
    surface: str
    surface_alt: str
    text: str
    muted_text: str
    border: str
    primary: str
    primary_hover: str
    danger: str


DARK_THEME = Theme(
    name="dark",
    background="#10131a",
    surface="#171b25",
    surface_alt="#202637",
    text="#f4f7fb",
    muted_text="#9aa6ba",
    border="#2a3145",
    primary="#55d6be",
    primary_hover="#70ead5",
    danger="#ff6f91",
)

LIGHT_THEME = Theme(
    name="light",
    background="#f4f7fb",
    surface="#ffffff",
    surface_alt="#edf2f7",
    text="#172033",
    muted_text="#667085",
    border="#d9e2ec",
    primary="#0f9f8f",
    primary_hover="#12b8a6",
    danger="#d92d20",
)


def get_theme(name: str) -> Theme:
    """Return a theme by name."""
    return LIGHT_THEME if name.lower() == "light" else DARK_THEME


def build_stylesheet(theme: Theme, *, primary_color: str | None = None) -> str:
    """Build the global Qt style sheet."""
    primary = primary_color or theme.primary
    return f"""
    QWidget {{
        background-color: {theme.background};
        color: {theme.text};
        font-family: "Segoe UI", "Inter", "Arial";
        font-size: 14px;
    }}
    QFrame#Sidebar, QFrame#Card, QFrame#TopBar, QDialog#LoginDialog {{
        background-color: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 18px;
    }}
    QLabel#Muted {{
        color: {theme.muted_text};
    }}
    QLabel#Title {{
        font-size: 26px;
        font-weight: 700;
    }}
    QLabel#SectionTitle {{
        font-size: 18px;
        font-weight: 650;
    }}
    QPushButton {{
        background-color: transparent;
        border: 1px solid {theme.border};
        border-radius: 12px;
        padding: 10px 14px;
        text-align: left;
    }}
    QPushButton:hover {{
        background-color: {theme.surface_alt};
        border-color: {primary};
    }}
    QPushButton#PrimaryButton {{
        background-color: {primary};
        color: #07120f;
        border: none;
        font-weight: 700;
        text-align: center;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {theme.primary_hover};
    }}
    QLineEdit, QComboBox, QTextEdit {{
        background-color: {theme.surface_alt};
        border: 1px solid {theme.border};
        border-radius: 12px;
        padding: 11px 12px;
        selection-background-color: {primary};
    }}
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
        border-color: {primary};
    }}
    QStackedWidget {{
        background-color: transparent;
        border: none;
    }}
    """
