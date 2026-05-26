"""Barcode generation helpers."""

from __future__ import annotations

from datetime import datetime


class BarcodeService:
    """Generate deterministic product codes and EAN-13 compatible barcodes."""

    def __init__(self, prefix: str = "220") -> None:
        self._prefix = "".join(ch for ch in prefix if ch.isdigit())[:3].ljust(3, "0")

    def generate_product_code(self, category_code: str, sequence: int) -> str:
        """Create a readable product coding-system value."""
        clean_category = "".join(ch for ch in category_code.upper() if ch.isalnum())[:6]
        return f"{clean_category}-{sequence:06d}"

    def generate_ean13(self, product_id: int) -> str:
        """Generate an EAN-13 barcode from an internal product id."""
        date_part = datetime.utcnow().strftime("%y")
        body = f"{self._prefix}{date_part}{product_id:07d}"[-12:]
        return body + self._calculate_ean13_check_digit(body)

    @staticmethod
    def _calculate_ean13_check_digit(first_12_digits: str) -> str:
        if len(first_12_digits) != 12 or not first_12_digits.isdigit():
            raise ValueError("EAN-13 body must contain exactly 12 digits.")
        total = 0
        for index, digit in enumerate(first_12_digits):
            multiplier = 1 if index % 2 == 0 else 3
            total += int(digit) * multiplier
        return str((10 - (total % 10)) % 10)
