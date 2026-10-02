"""Tiny helper to turn (headers, rows) into an .xlsx HttpResponse."""
import io

from django.http import HttpResponse
from openpyxl import Workbook


def xlsx_response(filename: str, headers: list[str], rows, sheet_title="Sheet1") -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(headers)
    for row in rows:
        ws.append(list(row))
    out = io.BytesIO()
    wb.save(out)
    resp = HttpResponse(
        out.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
