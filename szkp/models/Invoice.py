from decimal import Decimal

from django.db import models
from django.utils import timezone

from .Case import Case

## Model Invoice
class InvoiceStatus(models.TextChoices):
    WYSTAWIONA = 'wystawiona', 'Wystawiona'
    OPŁACONA = 'opłacona', 'Opłacona'
    PRZETERMINOWANA = 'przeterminowana', 'Przeterminowana'

class Invoice(models.Model):
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, blank=True, null=True, db_column='caseid')
    invoice_number = models.CharField(max_length=50, unique=True, null=False)
    currency = models.CharField(max_length=3, default='PLN')
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.23'))
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.WYSTAWIONA)
    issue_date = models.DateField(null=False)
    due_date = models.DateField(null=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.gross_amount = self.net_amount * (1 + self.vat_rate)
        if self.status == InvoiceStatus.OPŁACONA and not self.paid_at:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'INVOICES'