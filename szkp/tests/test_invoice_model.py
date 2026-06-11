from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase, tag

from szkp.models.Invoice import Invoice, InvoiceStatus


@tag('unit')
class InvoiceGrossAmountTest(TestCase):
    """Obliczanie gross_amount w Invoice.save()."""

    def _make(self, net, vat=Decimal('0.23'), **kwargs):
        return Invoice.objects.create(
            net_amount=net, vat_rate=vat,
            issue_date='2024-01-01', due_date='2024-01-31',
            invoice_number=kwargs.pop('invoice_number', 'FV/TEST/001'),
            **kwargs,
        )

    def test_gross_amount_calculation(self):
        inv = self._make(Decimal('100.00'))
        self.assertEqual(inv.gross_amount, Decimal('123.00'))

    def test_gross_amount_zero_net(self):
        inv = self._make(Decimal('0.00'))
        self.assertEqual(inv.gross_amount, Decimal('0.00'))

    def test_gross_amount_zero_vat(self):
        inv = self._make(Decimal('200.00'), vat=Decimal('0.00'))
        self.assertEqual(inv.gross_amount, Decimal('200.00'))

    def test_gross_amount_recalculated_on_update(self):
        inv = self._make(Decimal('100.00'))
        inv.net_amount = Decimal('200.00')
        inv.save()
        self.assertEqual(inv.gross_amount, Decimal('246.00'))


@tag('unit')
class InvoiceDefaultsTest(TestCase):
    """Wartości domyślne pól Invoice."""

    def test_domyslny_status_wystawiona(self):
        inv = Invoice()
        self.assertEqual(inv.status, InvoiceStatus.WYSTAWIONA)

    def test_domyslna_waluta_PLN(self):
        inv = Invoice()
        self.assertEqual(inv.currency, 'PLN')

    def test_domyslny_vat_rate_23(self):
        inv = Invoice()
        self.assertEqual(inv.vat_rate, Decimal('0.23'))

    def test_unikalny_numer_faktury_blokuje_duplikat(self):
        Invoice.objects.create(
            invoice_number='FV/DUP/001',
            net_amount=Decimal('0.00'),
            issue_date='2024-01-01',
            due_date='2024-01-31',
        )
        with self.assertRaises(IntegrityError):
            Invoice.objects.create(
                invoice_number='FV/DUP/001',
                net_amount=Decimal('0.00'),
                issue_date='2024-01-01',
                due_date='2024-01-31',
            )