from django.urls import path

from reports.views import DiscountsReport, OverviewReport, PlansReport, RevenueReport

urlpatterns = [
    path("reports/overview/", OverviewReport.as_view(), name="report-overview"),
    path("reports/revenue/", RevenueReport.as_view(), name="report-revenue"),
    path("reports/plans/", PlansReport.as_view(), name="report-plans"),
    path("reports/discounts/", DiscountsReport.as_view(), name="report-discounts"),
]
