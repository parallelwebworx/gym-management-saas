"""Multi-sheet Excel export of a gym's data (owner-only)."""
import io

from django.http import HttpResponse
from openpyxl import Workbook

from audit.models import AuditLog
from catalogue.models import AddOn, Plan
from members.models import Member
from memberships.models import Freeze, Membership
from notifications.models import Notification
from payments.models import Payment


def _sheet(wb, title, headers, rows, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = title
    ws.append(headers)
    for r in rows:
        ws.append(list(r))


def build_export(gym) -> bytes:
    wb = Workbook()

    _sheet(wb, "Members",
           ["ID", "Name", "Phone", "Email", "Gender", "Branch", "Created"],
           ((m.id, m.full_name, m.phone, m.email, m.gender,
             m.branch.name if m.branch else "", m.created_at.isoformat())
            for m in Member.objects.filter(gym=gym).select_related("branch").iterator()),
           first=True)

    _sheet(wb, "Memberships",
           ["ID", "Member", "Plan", "Start", "End", "Original end", "Corrections", "Cancelled on"],
           ((m.id, m.member.full_name, m.plan_name, m.start_date.isoformat(),
             m.end_date.isoformat(), m.original_end_date.isoformat(), m.correction_count,
             m.cancel_effective_date.isoformat() if m.cancel_effective_date else "")
            for m in Membership.objects.filter(gym=gym).select_related("member").iterator()))

    _sheet(wb, "Payments",
           ["Invoice", "Member", "Kind", "Method", "Amount (paise)", "Discount (paise)", "Date"],
           ((p.invoice_number, p.member.full_name if p.member else "", p.kind, p.method,
             p.amount_paise, p.discount_paise, p.created_at.isoformat())
            for p in Payment.objects.filter(gym=gym).select_related("member").iterator()))

    _sheet(wb, "Freezes",
           ["ID", "Membership", "Start", "End", "Days added"],
           ((f.id, f.membership_id, f.freeze_start_date.isoformat(),
             f.freeze_end_date.isoformat() if f.freeze_end_date else "", f.days_added)
            for f in Freeze.objects.filter(gym=gym).iterator()))

    _sheet(wb, "Plans",
           ["ID", "Name", "Type", "Duration", "Price (paise)", "Active"],
           ((p.id, p.name, p.plan_type, p.duration_days, p.price_paise, p.is_active)
            for p in Plan.objects.filter(gym=gym).iterator()))

    _sheet(wb, "AddOns",
           ["ID", "Name", "Type", "Price (paise)", "Auto-apply", "Active"],
           ((a.id, a.name, a.addon_type, a.price_paise, a.auto_apply_on_first_enrollment, a.is_active)
            for a in AddOn.objects.filter(gym=gym).iterator()))

    _sheet(wb, "AuditLog",
           ["Timestamp", "Action", "Entity", "Entity ID", "Actor", "Summary"],
           ((a.created_at.isoformat(), a.action, a.entity_type, a.entity_id,
             a.actor.email if a.actor else "", a.summary)
            for a in AuditLog.objects.filter(gym=gym).select_related("actor").iterator()))

    _sheet(wb, "Notifications",
           ["ID", "Event", "Channel", "To", "Status", "Attempts", "Created"],
           ((n.id, n.event, n.channel, n.to_phone, n.status, n.attempts, n.created_at.isoformat())
            for n in Notification.objects.filter(gym=gym).iterator()))

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def export_response(gym) -> HttpResponse:
    resp = HttpResponse(
        build_export(gym),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="gym_export.xlsx"'
    return resp
