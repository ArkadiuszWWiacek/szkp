from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError, models as django_models
from django.test import SimpleTestCase, TestCase, tag

from szkp.models.Invoice import Invoice, InvoiceStatus


@tag('unit')
class InvoiceFieldDefaultsTest(SimpleTestCase):
    """Wartości domyślne pól Invoice — bez zapisu do DB."""

    def test_domyslny_status_wystawiona(self):
        """Domyślny status nowej faktury to InvoiceStatus.WYSTAWIONA."""
        self.assertEqual(Invoice().status, InvoiceStatus.WYSTAWIONA)

    def test_domyslna_waluta_PLN(self):
        """Domyślna waluta nowej faktury to 'PLN'."""
        self.assertEqual(Invoice().currency, 'PLN')

    def test_domyslny_vat_rate_23(self):
        """Domyślna stawka VAT to 0.23 (23%)."""
        self.assertEqual(Invoice().vat_rate, Decimal('0.23'))


@tag('integration')
class InvoiceUniquenessTest(TestCase):
    """Unikalność numeru faktury — wymaga DB."""

    def test_unikalny_numer_faktury_blokuje_duplikat(self):
        """Duplikat invoice_number rzuca IntegrityError."""
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


@tag('unit')
class InvoiceStrTest(SimpleTestCase):
    """Invoice.__str__: zwraca numer faktury."""

    def test_str(self):
        """str(Invoice) zwraca invoice_number."""
        invoice = Invoice(invoice_number='FV/2024/001')
        self.assertEqual(str(invoice), 'FV/2024/001')


@tag('unit')
class InvoiceGrossAmountTest(SimpleTestCase):
    """Obliczanie gross_amount w Invoice.save()."""

    def _make(self, net, vat=Decimal('0.23'), **kwargs):
        inv = Invoice(
            net_amount=net,
            vat_rate=vat,
            invoice_number=kwargs.pop('invoice_number', 'FV/TEST/001'),
            issue_date='2024-01-01',
            due_date='2024-01-31',
            **kwargs,
        )
        with patch.object(django_models.Model, 'save'):
            inv.save()
        return inv

    def test_gross_amount_calculation(self):
        """gross_amount = net × 1,23 dla domyślnej stawki VAT 23%."""
        inv = self._make(Decimal('100.00'))
        self.assertEqual(inv.gross_amount, Decimal('123.00'))

    def test_gross_amount_zero_net(self):
        """gross_amount == 0 gdy net_amount == 0."""
        inv = self._make(Decimal('0.00'))
        self.assertEqual(inv.gross_amount, Decimal('0.00'))

    def test_gross_amount_zero_vat(self):
        """gross_amount == net_amount gdy vat_rate == 0."""
        inv = self._make(Decimal('200.00'), vat=Decimal('0.00'))
        self.assertEqual(inv.gross_amount, Decimal('200.00'))

    def test_gross_amount_recalculated_on_update(self):
        """Po zmianie net_amount i wywołaniu save() gross_amount jest przeliczane."""
        inv = self._make(Decimal('100.00'))
        inv.net_amount = Decimal('200.00')
        with patch.object(django_models.Model, 'save'):
            inv.save()
        self.assertEqual(inv.gross_amount, Decimal('246.00'))


@tag('unit')
class InvoicePaidAtTest(SimpleTestCase):
    """Auto-ustawianie paid_at przy zmianie statusu na opłacona."""

    def _make(self, **kwargs):
        inv = Invoice(
            invoice_number=kwargs.pop('invoice_number', 'FV/PAIDAT/001'),
            net_amount=Decimal('100.00'),
            issue_date='2024-01-01',
            due_date='2024-01-31',
            **kwargs,
        )
        with patch.object(django_models.Model, 'save'):
            inv.save()
        return inv

    def test_paid_at_ustawiany_przy_statusie_oplacona(self):
        """paid_at jest ustawiany automatycznie gdy status to OPŁACONA."""
        inv = self._make(status=InvoiceStatus.OPŁACONA)
        self.assertIsNotNone(inv.paid_at)

    def test_paid_at_nie_nadpisywany_jesli_juz_ustawiony(self):
        """Istniejąca wartość paid_at nie jest nadpisywana przez kolejny zapis."""
        original = datetime(2024, 3, 1, 12, 0, tzinfo=dt_timezone.utc)
        inv = self._make(status=InvoiceStatus.OPŁACONA, paid_at=original)
        self.assertEqual(inv.paid_at, original)

    def test_paid_at_nie_ustawiany_przy_statusie_wystawiona(self):
        """paid_at pozostaje None gdy status to WYSTAWIONA."""
        inv = self._make(status=InvoiceStatus.WYSTAWIONA)
        self.assertIsNone(inv.paid_at)

    def test_paid_at_nie_ustawiany_przy_statusie_przeterminowana(self):
        """paid_at pozostaje None gdy status to PRZETERMINOWANA."""
        inv = self._make(status=InvoiceStatus.PRZETERMINOWANA)
        self.assertIsNone(inv.paid_at)
