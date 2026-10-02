from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.permissions import IsAuthenticatedInGym
from invoices.pdf import build_pdf
from payments.models import Payment
from tenants.models import Role


class InvoicePDFView(APIView):
    permission_classes = [IsAuthenticated, IsAuthenticatedInGym]

    def get(self, request, payment_id):
        user = request.user
        qs = Payment.objects.filter(gym_id=user.gym_id).select_related("member", "membership", "gym")
        if user.role != Role.OWNER and user.branch_id:
            qs = qs.filter(branch_id=user.branch_id)
        payment = qs.filter(pk=payment_id).first()
        if not payment:
            return HttpResponse(status=404)

        pdf = build_pdf(payment)
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{payment.invoice_number}.pdf"'
        return resp
