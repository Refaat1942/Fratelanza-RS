"""Localization support for English and Arabic."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json


SUPPORTED_LOCALES = {"en": "English", "ar": "العربية"}
RTL_LOCALES = {"ar"}
DEFAULT_LOCALE = "en"


@dataclass(frozen=True)
class LocaleInfo:
    code: str
    name: str
    is_rtl: bool


class Localizer:
    """Translate application keys and expose text-direction metadata."""

    def __init__(self, locale: str = DEFAULT_LOCALE) -> None:
        self._fallback = _load_catalog(DEFAULT_LOCALE)
        self._locale = normalize_locale(locale)
        self._catalog = _load_catalog(self._locale)

    @property
    def locale(self) -> LocaleInfo:
        return LocaleInfo(
            code=self._locale,
            name=SUPPORTED_LOCALES[self._locale],
            is_rtl=self._locale in RTL_LOCALES,
        )

    def gettext(self, key: str, **kwargs: object) -> str:
        """Return a translated string for ``key``."""
        value = self._catalog.get(key, self._fallback.get(key, key))
        return value.format(**kwargs) if kwargs else value

    def switch(self, locale: str) -> None:
        """Switch the active language at runtime."""
        self._locale = normalize_locale(locale)
        self._catalog = _load_catalog(self._locale)


def normalize_locale(locale: str) -> str:
    """Normalize and validate a locale code."""
    normalized = (locale or DEFAULT_LOCALE).split("_", 1)[0].split("-", 1)[0].lower()
    return normalized if normalized in SUPPORTED_LOCALES else DEFAULT_LOCALE


def _load_catalog(locale: str) -> dict[str, str]:
    resource = files("fratelanza.resources.i18n").joinpath(f"{locale}.json")
    with resource.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {str(key): str(value) for key, value in data.items()}
