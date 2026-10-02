from rest_framework.views import APIView

from common.permissions import IsOwnerOrManager
from common.responses import ok
from common.xlsx import xlsx_response
from reports import services


class _BaseReportView(APIView):
    permission_classes = [IsOwnerOrManager]

    def bounds(self, request):
        return services.period_bounds(request)


class OverviewReport(_BaseReportView):
    def get(self, request):
        f, t = self.bounds(request)
        return ok({
            "overview": services.overview(request.user, f, t),
            "anomalies": services.anomalies(request.user, f, t),
            "trend": services.revenue_series(request.user, f, t),
        })


class RevenueReport(_BaseReportView):
    def get(self, request):
        f, t = self.bounds(request)
        series = services.revenue_series(request.user, f, t)
        if request.query_params.get("export") == "xlsx":
            rows = ((r["date"], r["revenue_paise"] / 100, r["cumulative_paise"] / 100) for r in series)
            return xlsx_response("revenue.xlsx", ["Date", "Revenue (₹)", "Cumulative (₹)"], rows, "Revenue")
        return ok({"series": series})


class PlansReport(_BaseReportView):
    def get(self, request):
        f, t = self.bounds(request)
        data = services.plan_sales(request.user, f, t)
        if request.query_params.get("export") == "xlsx":
            rows = ((r["plan_name"], r["count"], r["revenue_paise"] / 100) for r in data)
            return xlsx_response("plan_sales.xlsx", ["Plan", "Sales", "Revenue (₹)"], rows, "Plans")
        return ok({"plans": data})


class DiscountsReport(_BaseReportView):
    def get(self, request):
        f, t = self.bounds(request)
        data = services.discount_leakage(request.user, f, t)
        if request.query_params.get("export") == "xlsx":
            rows = (
                (r["staff_name"], r["sales"], r["total_discount_paise"] / 100,
                 r["avg_discount_paise"] / 100, r["gross_paise"] / 100)
                for r in data
            )
            return xlsx_response(
                "discount_leakage.xlsx",
                ["Staff", "Sales", "Total discount (₹)", "Avg discount (₹)", "Gross (₹)"],
                rows, "Discounts",
            )
        return ok({"staff": data})
