from fratelanza.application.barcode_service import BarcodeService


def test_ean13_generation_returns_valid_check_digit() -> None:
    service = BarcodeService(prefix="220")
    barcode = service.generate_ean13(42)

    assert len(barcode) == 13
    assert barcode.isdigit()
    assert barcode[-1] == service._calculate_ean13_check_digit(barcode[:12])


def test_product_code_is_readable_and_padded() -> None:
    service = BarcodeService()

    assert service.generate_product_code("cosmetics", 7) == "COSMET-000007"
