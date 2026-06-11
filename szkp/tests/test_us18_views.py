from datetime import date, timedelta
from decimal import Decimal

from django.test import tag
from django.urls import reverse

from szkp.models import Case, CaseType, Invoice, InvoiceStatus
from szkp.tests.base import StaffLawyerTestCase


def _make_invoice(case, number, status=InvoiceStatus.WYSTAWIONA):
    return Invoice.objects.create(
        case=case,
        invoice_number=number,
        net_amount=Decimal('500.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=14),
        status=status,
    )


@tag('integration')
class InvoiceListViewTest(StaffLawyerTestCase):
    """invoice_list: dostępność, filtr po statusie, uprawnienia."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US18-001',
            title='Sprawa do testów listy faktur', case_type=CaseType.CYWILNA,
        )

    def _url(self, status=None):
        url = reverse('szkp:invoice_list')
        if status:
            url += f'?status={status}'
        return url

    def test_get_lista_zwraca_200(self):
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_lista_zawiera_faktury(self):
        _make_invoice(self.sprawa, 'FV/US18/VW001')
        r = self.client.get(self._url())
        self.assertContains(r, 'FV/US18/VW001')

    def test_filtr_po_statusie_oplacona(self):
        _make_invoice(self.sprawa, 'FV/US18/VW-WYS', InvoiceStatus.WYSTAWIONA)
        _make_invoice(self.sprawa, 'FV/US18/VW-OPL', InvoiceStatus.OPŁACONA)
        r = self.client.get(self._url(status='opłacona'))
        self.assertContains(r, 'FV/US18/VW-OPL')
        self.assertNotContains(r, 'FV/US18/VW-WYS')

    def test_filtr_po_statusie_przeterminowana(self):
        _make_invoice(self.sprawa, 'FV/US18/VW-WYS2', InvoiceStatus.WYSTAWIONA)
        _make_invoice(self.sprawa, 'FV/US18/VW-PRZ', InvoiceStatus.PRZETERMINOWANA)
        r = self.client.get(self._url(status='przeterminowana'))
        self.assertContains(r, 'FV/US18/VW-PRZ')
        self.assertNotContains(r, 'FV/US18/VW-WYS2')

    def test_filtr_nieznany_status_ignorowany(self):
        _make_invoice(self.sprawa, 'FV/US18/VW-IGN')
        r = self.client.get(self._url(status='nieznany'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'FV/US18/VW-IGN')

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])


@tag('integration')
class InvoiceMarkPaidViewTest(StaffLawyerTestCase):
    """invoice_mark_paid: zmiana statusu na opłacona, auto paid_at, uprawnienia."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US18-MP-001',
            title='Sprawa do testów mark_paid', case_type=CaseType.CYWILNA,
        )

    def setUp(self):
        super().setUp()
        self.faktura = _make_invoice(self.sprawa, 'FV/US18/MP001')

    def _url(self):
        return reverse('szkp:invoice_mark_paid', kwargs={'pk': self.faktura.pk})

    def test_mark_paid_zmienia_status(self):
        self.client.post(self._url())
        self.faktura.refresh_from_db()
        self.assertEqual(self.faktura.status, InvoiceStatus.OPŁACONA)

    def test_mark_paid_ustawia_paid_at(self):
        self.client.post(self._url())
        self.faktura.refresh_from_db()
        self.assertIsNotNone(self.faktura.paid_at)

    def test_mark_paid_przekierowuje_na_liste(self):
        r = self.client.post(self._url())
        self.assertRedirects(r, reverse('szkp:invoice_list'))

    def test_mark_paid_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.post(self._url())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])
