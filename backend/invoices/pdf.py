"""
Server-side PDF documents for payments, built with ReportLab.

Document type is chosen from the payment + gym:
  - refund payment            -> Credit Note
  - gym has a GSTIN           -> GST Tax Invoice (CGST+SGST, intra-state, @18%, HSN 999723)
  - otherwise                 -> Simple Receipt

GST is back-calculated from the (tax-inclusive) amount, matching the way gyms
price memberships inclusive of tax.
"""
import io

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from common.money import format_paise_inr, rupees_in_words
from payments.models import PaymentKind


def _line_items(payment):
    """(description, amount_paise) rows for the document body."""
    m = payment.membership
    if m is None:
        return [("Payment", abs(payment.amount_paise))]
    rows = [(f"Membership — {m.plan_name} ({m.duration_days} days)", m.plan_price_paise)]
    for a in m.addons.all():
        rows.append((f"Add-on — {a.name}", a.price_paise))
    return rows


def _doc_kind(payment):
    if payment.kind == PaymentKind.REFUND:
        return "Credit Note"
    if payment.gym.gstin:
        return "Tax Invoice"
    return "Receipt"


def build_pdf(payment) -> bytes:
    gym = payment.gym
    kind = _doc_kind(payment)
    is_tax = kind == "Tax Invoice"
    amount = abs(payment.amount_paise)

    styles = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    story = []

    # Header
    story.append(Paragraph(f"<b>{gym.name}</b>", styles["Title"]))
    if gym.gstin:
        story.append(Paragraph(f"GSTIN: {gym.gstin}", styles["Normal"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(f"<b>{kind}</b>", styles["Heading2"]))

    meta = [
        ["Invoice No", payment.invoice_number, "Date", payment.created_at.strftime("%d-%m-%Y")],
        ["Bill To", payment.member.full_name if payment.member else "-",
         "Phone", payment.member.phone if payment.member else "-"],
    ]
    meta_tbl = Table(meta, colWidths=[30 * mm, 60 * mm, 25 * mm, 55 * mm])
    meta_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 6 * mm))

    # Line items
    data = [["Description", "Amount"]]
    for desc, amt in _line_items(payment):
        data.append([desc, format_paise_inr(amt)])
    if payment.discount_paise:
        data.append(["Discount", f"- {format_paise_inr(payment.discount_paise)}"])

    if is_tax:
        taxable = round(amount / (1 + settings.GST_RATE_BPS / 10000))
        tax = amount - taxable
        cgst = tax // 2
        sgst = tax - cgst
        data.append([f"Taxable value (HSN {settings.GST_HSN_CODE})", format_paise_inr(taxable)])
        data.append(["CGST @ 9%", format_paise_inr(cgst)])
        data.append(["SGST @ 9%", format_paise_inr(sgst)])

    total_label = "Total refunded" if payment.kind == PaymentKind.REFUND else "Total"
    data.append([total_label, format_paise_inr(amount)])

    tbl = Table(data, colWidths=[120 * mm, 50 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e2e8f0")),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, colors.HexColor("#0f172a")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(f"<i>Amount in words: {rupees_in_words(amount)}</i>", styles["Normal"]))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("This is a computer-generated document.", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()
