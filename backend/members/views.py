from django.db import connection
from django.http import HttpResponse
from rest_framework.decorators import action

from common.permissions import MemberPermission
from common.phone import normalize_phone_in
from common.responses import err, ok
from common.viewsets import TenantScopedViewSet
from members import io as member_io
from members.models import Member
from members.serializers import MemberSerializer

SORT_FIELDS = {
    "name": "full_name",
    "-name": "-full_name",
    "created": "created_at",
    "-created": "-created_at",
}


class MemberViewSet(TenantScopedViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [MemberPermission]
    branch_scoped = True

    def get_queryset(self):
        qs = super().get_queryset()

        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = self._apply_search(qs, search)

        gender = self.request.query_params.get("gender")
        if gender:
            qs = qs.filter(gender=gender)

        sort = self.request.query_params.get("sort", "name")
        if not search:  # search already orders by relevance
            qs = qs.order_by(SORT_FIELDS.get(sort, "full_name"))
        return qs

    def _apply_search(self, qs, search):
        """Trigram fuzzy search on Postgres; icontains fallback elsewhere."""
        if connection.vendor == "postgresql":
            from django.contrib.postgres.search import TrigramSimilarity
            from django.db.models import F, Q

            digits = "".join(ch for ch in search if ch.isdigit())
            name_sim = TrigramSimilarity("full_name", search)
            qs = qs.annotate(similarity=name_sim)
            cond = Q(similarity__gt=0.2) | Q(full_name__icontains=search)
            if digits:
                cond |= Q(phone__icontains=digits)
            return qs.filter(cond).order_by(F("similarity").desc(nulls_last=True), "full_name")

        digits = "".join(ch for ch in search if ch.isdigit())
        from django.db.models import Q

        cond = Q(full_name__icontains=search)
        if digits:
            cond |= Q(phone__icontains=digits)
        return qs.filter(cond).order_by("full_name")

    # -- duplicate phone live check ---------------------------------------
    @action(detail=False, methods=["get"], url_path="check-phone")
    def check_phone(self, request):
        raw = request.query_params.get("phone", "")
        try:
            phone = normalize_phone_in(raw)
        except ValueError as exc:
            return err(str(exc), code="invalid_phone")
        qs = Member.objects.filter(gym_id=request.user.gym_id, phone=phone)
        exclude_id = request.query_params.get("exclude")
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        match = qs.first()
        return ok({
            "phone": phone,
            "exists": match is not None,
            "member": {"id": match.id, "full_name": match.full_name} if match else None,
        })

    # -- restore a soft-deleted member ------------------------------------
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        member = Member.all_objects.filter(
            gym_id=request.user.gym_id, pk=pk, deleted_at__isnull=False
        ).first()
        if not member:
            return err("No soft-deleted member with that id.", code="not_found", status=404)
        # Block restore if the phone was since taken by a live member.
        if Member.objects.filter(gym_id=member.gym_id, phone=member.phone).exists():
            return err(
                "Cannot restore: the phone number is now used by another member.",
                code="phone_conflict", status=409,
            )
        member.restore()
        return ok(MemberSerializer(member, context={"request": request}).data)

    # -- CSV import -------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="import-template")
    def import_template(self, request):
        resp = HttpResponse(member_io.build_template_csv(), content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="members_import_template.csv"'
        return resp

    @action(detail=False, methods=["post"], url_path="import")
    def import_csv(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return err("Upload a CSV file in the 'file' field.", code="no_file")
        commit = str(request.query_params.get("commit", "false")).lower() == "true"
        try:
            valid_rows, report = member_io.parse_and_validate(
                upload.read(), request.user.gym_id, request.user.branch_id
            )
        except ValueError as exc:
            return err(str(exc), code="bad_csv")

        summary = {
            "total": len(report),
            "valid": len(valid_rows),
            "errors": sum(1 for r in report if r["status"] == "error"),
            "duplicates": sum(1 for r in report if r["status"].startswith("duplicate")),
        }
        inserted = 0
        if commit and valid_rows:
            inserted = member_io.commit_rows(valid_rows)
        return ok({"committed": commit, "inserted": inserted, "summary": summary, "rows": report})

    # -- Excel export ----------------------------------------------------
    @action(detail=False, methods=["get"], url_path="export")
    def export_excel(self, request):
        content = member_io.export_workbook(self.get_queryset())
        resp = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = 'attachment; filename="members.xlsx"'
        return resp
