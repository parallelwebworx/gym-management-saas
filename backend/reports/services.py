"""
Reporting aggregations + rule-based anomaly detection.

All revenue is derived from the signed Payment ledger (net = Sum(amount_paise)).
Days are grouped in IST (TruncDate with tzinfo) over UTC-stored timestamps.
"""
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate

from common.dates import IST, ist_day_bounds_utc, ist_today
from payments.models import Payment, PaymentKind
from tenants.models import Role


def period_bounds(request):
    """Return (from_date, to_date) in IST. Defaults to the last 30 days."""
    from datetime import date

    p = request.query_params
    today = ist_today()
    try:
        to_date = date.fromisoformat(p["to"]) if p.get("to") else today
    except ValueError:
        to_date = today
    try:
        from_date = date.fromisoformat(p["from"]) if p.get("from") else to_date - timedelta(days=29)
    except ValueError:
        from_date = to_date - timedelta(days=29)
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    return from_date, to_date


def scope_payments(user, from_date, to_date):
    start_utc, _ = ist_day_bounds_utc(from_date)
    _, end_utc = ist_day_bounds_utc(to_date)
    qs = Payment.objects.filter(
        gym_id=user.gym_id, created_at__gte=start_utc, created_at__lt=end_utc
    )
    if user.role != Role.OWNER and user.branch_id:
        qs = qs.filter(branch_id=user.branch_id)
    return qs


def _totals(qs):
    agg = qs.aggregate(
        gross=Sum("amount_paise", filter=Q(amount_paise__gt=0)),
        refunds=Sum("amount_paise", filter=Q(amount_paise__lt=0)),
        net=Sum("amount_paise"),
        discount=Sum("discount_paise"),
        txns=Count("id"),
        enrollments=Count("id", filter=Q(kind=PaymentKind.ENROLLMENT)),
        renewals=Count("id", filter=Q(kind=PaymentKind.RENEWAL)),
    )
    return {k: (v or 0) for k, v in agg.items()}


def overview(user, from_date, to_date):
    cur = scope_payments(user, from_date, to_date)
    t = _totals(cur)

    # Previous equal-length period for comparison.
    length = (to_date - from_date).days + 1
    prev_to = from_date - timedelta(days=1)
    prev_from = prev_to - timedelta(days=length - 1)
    prev_net = scope_payments(user, prev_from, prev_to).aggregate(net=Sum("amount_paise"))["net"] or 0

    revenue_change_pct = None
    if prev_net:
        revenue_change_pct = round((t["net"] - prev_net) * 100.0 / abs(prev_net), 1)

    list_total = t["gross"] + t["discount"]  # gross is already net of discount
    discount_rate = round(t["discount"] * 100.0 / list_total, 1) if list_total else 0.0

    return {
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "gross_paise": t["gross"],
        "refunds_paise": -t["refunds"],
        "net_paise": t["net"],
        "discount_paise": t["discount"],
        "discount_rate_pct": discount_rate,
        "transactions": t["txns"],
        "enrollments": t["enrollments"],
        "renewals": t["renewals"],
        "prev_net_paise": prev_net,
        "revenue_change_pct": revenue_change_pct,
    }


def revenue_series(user, from_date, to_date):
    rows = (
        scope_payments(user, from_date, to_date)
        .annotate(day=TruncDate("created_at", tzinfo=IST))
        .values("day")
        .annotate(revenue=Sum("amount_paise"))
    )
    by_day = {r["day"]: (r["revenue"] or 0) for r in rows}
    out = []
    cumulative = 0
    d = from_date
    while d <= to_date:
        rev = by_day.get(d, 0)
        cumulative += rev
        out.append({"date": d.isoformat(), "revenue_paise": rev, "cumulative_paise": cumulative})
        d += timedelta(days=1)
    return out


def plan_sales(user, from_date, to_date):
    rows = (
        scope_payments(user, from_date, to_date)
        .filter(amount_paise__gt=0, membership__isnull=False)
        .values("membership__plan_name")
        .annotate(count=Count("id"), revenue=Sum("amount_paise"))
        .order_by("-revenue")
    )
    return [
        {"plan_name": r["membership__plan_name"] or "—",
         "count": r["count"], "revenue_paise": r["revenue"] or 0}
        for r in rows
    ]


def discount_leakage(user, from_date, to_date):
    rows = (
        scope_payments(user, from_date, to_date)
        .filter(amount_paise__gt=0)
        .values("created_by", "created_by__full_name", "created_by__email")
        .annotate(
            sales=Count("id"),
            total_discount=Sum("discount_paise"),
            gross=Sum("amount_paise"),
        )
        .order_by("-total_discount")
    )
    out = []
    for r in rows:
        sales = r["sales"] or 0
        discount = r["total_discount"] or 0
        out.append({
            "staff_id": r["created_by"],
            "staff_name": r["created_by__full_name"] or r["created_by__email"] or "—",
            "sales": sales,
            "total_discount_paise": discount,
            "gross_paise": r["gross"] or 0,
            "avg_discount_paise": round(discount / sales) if sales else 0,
        })
    return out


def anomalies(user, from_date, to_date):
    ov = overview(user, from_date, to_date)
    found = []

    def add(severity, code, title, detail):
        found.append({"severity": severity, "code": code, "title": title, "detail": detail})

    # 1. High overall discount rate.
    if ov["discount_rate_pct"] >= 15:
        add("warning", "high_discount_rate", "High discount rate",
            f"{ov['discount_rate_pct']}% of list value was discounted this period.")

    # 2. Elevated refunds.
    if ov["gross_paise"] and ov["refunds_paise"] > 0.10 * ov["gross_paise"]:
        pct = round(ov["refunds_paise"] * 100.0 / ov["gross_paise"], 1)
        add("warning", "elevated_refunds", "Elevated refunds",
            f"Refunds were {pct}% of gross revenue.")

    # 3. Revenue down vs previous period.
    if ov["revenue_change_pct"] is not None and ov["revenue_change_pct"] <= -20:
        add("warning", "revenue_drop", "Revenue down vs previous period",
            f"Net revenue fell {abs(ov['revenue_change_pct'])}% vs the previous period.")

    # 4. Staff discount outlier.
    leakage = discount_leakage(user, from_date, to_date)
    staff_with_sales = [s for s in leakage if s["sales"] >= 3]
    if staff_with_sales:
        gym_avg = sum(s["avg_discount_paise"] for s in staff_with_sales) / len(staff_with_sales)
        for s in staff_with_sales:
            if gym_avg > 0 and s["avg_discount_paise"] > 2 * gym_avg:
                add("warning", "staff_discount_outlier", "Staff discount outlier",
                    f"{s['staff_name']} averages far higher discounts than peers.")

    # 5. Many edited payments.
    edited = scope_payments(user, from_date, to_date).filter(edited=True).count()
    if edited >= 3:
        add("info", "many_edits", "Several payments edited",
            f"{edited} payments were edited this period.")

    # 6. Large single discount (>50% of its own list price).
    big = (
        scope_payments(user, from_date, to_date)
        .filter(amount_paise__gt=0, discount_paise__gt=0)
    )
    for p in big.only("invoice_number", "amount_paise", "discount_paise")[:500]:
        list_price = p.amount_paise + p.discount_paise
        if list_price and p.discount_paise > 0.5 * list_price:
            add("warning", "large_discount", "Large single discount",
                f"Invoice {p.invoice_number} was discounted over 50%.")
            break

    return found
