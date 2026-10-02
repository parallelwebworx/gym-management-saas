"""
Server-side CSV import + Excel export for members.

Import: parse an uploaded CSV, validate + normalize each row (phone to E.164),
detect duplicates (within the file and against existing gym members), and batch-
insert the valid rows inside a transaction. Returns a per-row report so the UI can
render a preview / result.

Export: stream an .xlsx of the gym's members via openpyxl.
"""
import csv
import io

from django.db import transaction
from openpyxl import Workbook

from common.phone import normalize_phone_in
from members.models import Member

IMPORT_COLUMNS = ["full_name", "phone", "email", "gender", "date_of_birth", "address", "notes"]
REQUIRED_COLUMNS = ["full_name", "phone"]
_VALID_GENDERS = {"male", "female", "other", "unspecified"}


def build_template_csv() -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(IMPORT_COLUMNS)
    writer.writerow(
        ["Asha Rao", "+919876543210", "asha@example.com", "female", "1995-04-12", "MG Road", ""]
    )
    return buf.getvalue()


def parse_and_validate(file_bytes: bytes, gym_id: int, branch_id):
    """Return (valid_rows, report). ``report`` is a list of per-row dicts."""
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    header = [h.strip() for h in (reader.fieldnames or [])]
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    existing = set(
        Member.objects.filter(gym_id=gym_id).values_list("phone", flat=True)
    )
    seen_in_file: set[str] = set()
    valid_rows = []
    report = []

    for i, raw in enumerate(reader, start=2):  # row 1 is the header
        name = (raw.get("full_name") or "").strip()
        phone_raw = (raw.get("phone") or "").strip()
        row_errors = []

        if not name:
            row_errors.append("full_name is required")
        phone = None
        if not phone_raw:
            row_errors.append("phone is required")
        else:
            try:
                phone = normalize_phone_in(phone_raw)
            except ValueError as exc:
                row_errors.append(str(exc))

        gender = (raw.get("gender") or "unspecified").strip().lower() or "unspecified"
        if gender not in _VALID_GENDERS:
            gender = "unspecified"

        status = "ok"
        if row_errors:
            status = "error"
        elif phone in seen_in_file:
            status = "duplicate_in_file"
            row_errors.append("duplicate phone within file")
        elif phone in existing:
            status = "duplicate_existing"
            row_errors.append("phone already exists for this gym")

        if status == "ok":
            seen_in_file.add(phone)
            valid_rows.append(
                Member(
                    gym_id=gym_id,
                    branch_id=branch_id,
                    full_name=name,
                    phone=phone,
                    email=(raw.get("email") or "").strip(),
                    gender=gender,
                    address=(raw.get("address") or "").strip(),
                    notes=(raw.get("notes") or "").strip(),
                )
            )

        report.append(
            {"row": i, "full_name": name, "phone": phone or phone_raw,
             "status": status, "errors": row_errors}
        )

    return valid_rows, report


@transaction.atomic
def commit_rows(valid_rows, batch_size=500):
    Member.objects.bulk_create(valid_rows, batch_size=batch_size)
    return len(valid_rows)


def export_workbook(members_qs) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Members"
    headers = ["ID", "Full name", "Phone", "Email", "Gender", "Date of birth",
               "Address", "Notes", "Created"]
    ws.append(headers)
    for m in members_qs.iterator():
        ws.append([
            m.id, m.full_name, m.phone, m.email, m.gender,
            m.date_of_birth.isoformat() if m.date_of_birth else "",
            m.address, m.notes,
            m.created_at.isoformat(),
        ])
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
