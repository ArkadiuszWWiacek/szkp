from django.test import TestCase, tag
from szkp.models.Invoice import Invoice
from decimal import Decimal

@tag('unit')
class InvoiceModelTest(TestCase):
    def test_invoice_gross_amount_calculation(self):
        invoice = Invoice(net_amount=100, vat_rate=Decimal('0.23'), issue_date='2024-01-01', due_date='2024-01-31')
        invoice.save()
        self.assertEqual(invoice.gross_amount, Decimal('123.00'))

    def test_gross_amount_zero_net(self):
        invoice = Invoice(net_amount=0, vat_rate=Decimal('0.23'), issue_date='2024-01-01', due_date='2024-01-31')
        invoice.save()
        self.assertEqual(invoice.gross_amount, Decimal('0.00'))

    def test_gross_amount_zero_vat(self):
        invoice = Invoice(net_amount=Decimal('200.00'), vat_rate=Decimal('0.00'), issue_date='2024-01-01', due_date='2024-01-31')
        invoice.save()
        self.assertEqual(invoice.gross_amount, Decimal('200.00'))

    def test_gross_amount_recalculated_on_update(self):
        invoice = Invoice(net_amount=Decimal('100.00'), vat_rate=Decimal('0.23'), issue_date='2024-01-01', due_date='2024-01-31')
        invoice.save()
        invoice.net_amount = Decimal('200.00')
        invoice.save()
        self.assertEqual(invoice.gross_amount, Decimal('246.00'))