from django.urls import path

from invoices.views import InvoicePDFView

urlpatterns = [
    path("invoices/<int:payment_id>/pdf/", InvoicePDFView.as_view(), name="invoice-pdf"),
]
