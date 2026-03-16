from django.test import TestCase
from szkp.models.Invoice import Invoice
from decimal import Decimal
        
class InvoiceModelTest(TestCase):
    def test_invoice_gross_amount_calculation(self):
        invoice = Invoice(net_amount=100, vat_rate=Decimal('0.23'), issue_date='2024-01-01', due_date='2024-01-31')
        
        invoice.save()
        
        self.assertEqual(invoice.gross_amount, Decimal('123.00'))