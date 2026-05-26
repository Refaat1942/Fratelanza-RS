from decimal import Decimal

from fratelanza.infrastructure.repositories.cloud_business_repository import CloudBusinessRepository


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def request(self, method, path, payload=None, query=None):
        self.calls.append((method, path, payload, query))
        if path == "/business/products/next-sequence":
            return {"next_sequence": 7}
        if path == "/business/invoices":
            return {"invoice_id": 3}
        if path == "/business/reports/summary":
            return {"SalesTotal": 0, "TodaySales": 0, "TodayInvoices": 0, "LowStockCount": 0}
        return []


def test_cloud_repository_converts_decimal_payloads() -> None:
    client = FakeClient()
    repository = CloudBusinessRepository(client)

    repository.add_expense(
        category_id=1,
        cashbox_id=1,
        amount=Decimal("25.50"),
        expense_date="2026-05-26",
        description="Test",
        user_id=1,
    )

    assert client.calls[0][2]["amount"] == "25.50"


def test_cloud_repository_reads_next_product_sequence() -> None:
    repository = CloudBusinessRepository(FakeClient())

    assert repository.next_product_sequence() == 7
