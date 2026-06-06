import csv
import io
from typing import Any

from openpyxl import Workbook


class ExportService:
    @staticmethod
    def to_csv(rows: list[dict[str, Any]], filename: str = "export.csv") -> tuple[bytes, str]:
        if not rows:
            rows = [{"message": "no data"}]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue().encode("utf-8-sig"), filename

    @staticmethod
    def to_excel(rows: list[dict[str, Any]], filename: str = "export.xlsx") -> tuple[bytes, str]:
        wb = Workbook()
        ws = wb.active
        ws.title = "Export"
        if not rows:
            rows = [{"message": "no data"}]
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])
        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue(), filename
