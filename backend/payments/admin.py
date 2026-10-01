from django.contrib import admin

from payments.models import InvoiceSequence, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "invoice_number", "member", "kind", "amount_paise", "discount_paise", "created_at"]
    list_filter = ["kind", "method"]
    search_fields = ["invoice_number", "member__full_name"]


@admin.register(InvoiceSequence)
class InvoiceSequenceAdmin(admin.ModelAdmin):
    list_display = ["id", "gym", "year", "last_value"]
