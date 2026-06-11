from datetime import date, timedelta
from decimal import Decimal

from django.test import tag
from django.urls import reverse

from szkp.models import Case, CaseType, Invoice, InvoiceStatus
from szkp.tests.base import StaffLawyerTestCase


def _jutro():
    return (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')


def _za_30_dni():
    return (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')


@tag('integration')
class InvoiceCreateViewTest(StaffLawyerTestCase):
    """invoice_form (nowa faktura): walidacja POST, tworzenie, domyślne wartości."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US07-001',
            title='Sprawa do testów faktur', case_type=CaseType.CYWILNA,
        )

    def _url_new(self):
        return reverse('szkp:invoice_new', kwargs={'case_pk': self.sprawa.pk})

    def _valid_data(self, **overrides):
        data = {
            'invoice_number': 'FV/2025/001',
            'issue_date': _jutro(),
            'due_date': _za_30_dni(),
            'net_amount': '1000.00',
            'vat_rate': '0.23',
            'currency': 'PLN',
            'status': InvoiceStatus.WYSTAWIONA,
        }
        data.update(overrides)
        return data

    def test_get_formularz_zwraca_200(self):
        r = self.client.get(self._url_new())
        self.assertEqual(r.status_code, 200)

    def test_domyslny_status_w_formularzu(self):
        r = self.client.get(self._url_new())
        self.assertEqual(r.context['form_data'].get('status'), InvoiceStatus.WYSTAWIONA)

    def test_domyslna_waluta_w_formularzu(self):
        r = self.client.get(self._url_new())
        self.assertEqual(r.context['form_data'].get('currency'), 'PLN')

    def test_post_tworzy_fakture(self):
        self.client.post(self._url_new(), self._valid_data())
        self.assertTrue(
            Invoice.objects.filter(
                case=self.sprawa, invoice_number='FV/2025/001',
            ).exists()
        )

    def test_gross_amount_wyliczany_przy_zapisie(self):
        self.client.post(self._url_new(), self._valid_data(
            invoice_number='FV/2025/VAT', net_amount='1000.00', vat_rate='0.23',
        ))
        inv = Invoice.objects.get(invoice_number='FV/2025/VAT')
        self.assertEqual(inv.gross_amount, Decimal('1230.00'))

    def test_duplikat_invoice_number_zwraca_blad(self):
        Invoice.objects.create(
            case=self.sprawa, invoice_number='FV/2025/DUP',
            net_amount=Decimal('100.00'),
            issue_date=date.today(), due_date=date.today() + timedelta(days=14),
        )
        r = self.client.post(self._url_new(), self._valid_data(invoice_number='FV/2025/DUP'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('invoice_number', r.context['errors'])

    def test_brak_wymaganych_pol_zwraca_blad(self):
        r = self.client.post(self._url_new(), {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['errors'])

    def test_po_zapisie_redirect_do_faktury_tab(self):
        r = self.client.post(self._url_new(), self._valid_data())
        self.assertRedirects(
            r,
            reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=faktury',
        )

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url_new())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])


@tag('integration')
class InvoiceEditViewTest(StaffLawyerTestCase):
    """invoice_form (edycja faktury): zmiana statusu, pre-fill formularza."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US07-EDIT-001',
            title='Sprawa do edycji faktur', case_type=CaseType.CYWILNA,
        )
        cls.faktura = Invoice.objects.create(
            case=cls.sprawa,
            invoice_number='FV/2025/EDIT',
            net_amount=Decimal('800.00'),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status=InvoiceStatus.WYSTAWIONA,
        )

    def _url_edit(self):
        return reverse(
            'szkp:invoice_edit',
            kwargs={'case_pk': self.sprawa.pk, 'pk': self.faktura.pk},
        )

    def _valid_edit_data(self, **overrides):
        data = {
            'invoice_number': self.faktura.invoice_number,
            'issue_date': self.faktura.issue_date.strftime('%Y-%m-%d'),
            'due_date': self.faktura.due_date.strftime('%Y-%m-%d'),
            'net_amount': str(self.faktura.net_amount),
            'vat_rate': str(self.faktura.vat_rate),
            'currency': self.faktura.currency,
            'status': self.faktura.status,
        }
        data.update(overrides)
        return data

    def test_get_formularz_edycji_zwraca_200(self):
        r = self.client.get(self._url_edit())
        self.assertEqual(r.status_code, 200)

    def test_get_formularz_zawiera_dane_faktury(self):
        r = self.client.get(self._url_edit())
        self.assertEqual(r.context['form_data']['invoice_number'], self.faktura.invoice_number)

    def test_post_zmienia_status_na_oplacona(self):
        self.client.post(self._url_edit(), self._valid_edit_data(status='opłacona'))
        self.faktura.refresh_from_db()
        self.assertEqual(self.faktura.status, InvoiceStatus.OPŁACONA)

    def test_post_zmienia_status_na_przeterminowana(self):
        self.client.post(self._url_edit(), self._valid_edit_data(status='przeterminowana'))
        self.faktura.refresh_from_db()
        self.assertEqual(self.faktura.status, InvoiceStatus.PRZETERMINOWANA)

    def test_po_edycji_redirect_do_faktury_tab(self):
        r = self.client.post(self._url_edit(), self._valid_edit_data())
        self.assertRedirects(
            r,
            reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=faktury',
        )
