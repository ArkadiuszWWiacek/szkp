from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
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

    def test_nieprzypisany_prawnik_dostaje_403(self):
        user2 = User.objects.create_user('obcy_us07', password='pass', is_staff=False)
        self.client.force_login(user2)
        r = self.client.get(self._url_new())
        self.assertEqual(r.status_code, 403)


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

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url_edit())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])

    def test_nieprzypisany_prawnik_dostaje_403(self):
        user2 = User.objects.create_user('obcy_us07_edit', password='pass', is_staff=False)
        self.client.force_login(user2)
        r = self.client.get(self._url_edit())
        self.assertEqual(r.status_code, 403)

    def test_post_status_oplacona_ustawia_paid_at(self):
        self.client.post(self._url_edit(), self._valid_edit_data(status='opłacona'))
        self.faktura.refresh_from_db()
        self.assertIsNotNone(self.faktura.paid_at)


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
            client=cls.klient, case_number='TST-US07-LIST-001',
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
        _make_invoice(self.sprawa, 'FV/US07-L/VW001')
        r = self.client.get(self._url())
        self.assertContains(r, 'FV/US07-L/VW001')

    def test_filtr_po_statusie_oplacona(self):
        _make_invoice(self.sprawa, 'FV/US07-L/VW-WYS', InvoiceStatus.WYSTAWIONA)
        _make_invoice(self.sprawa, 'FV/US07-L/VW-OPL', InvoiceStatus.OPŁACONA)
        r = self.client.get(self._url(status='opłacona'))
        self.assertContains(r, 'FV/US07-L/VW-OPL')
        self.assertNotContains(r, 'FV/US07-L/VW-WYS')

    def test_filtr_po_statusie_przeterminowana(self):
        _make_invoice(self.sprawa, 'FV/US07-L/VW-WYS2', InvoiceStatus.WYSTAWIONA)
        _make_invoice(self.sprawa, 'FV/US07-L/VW-PRZ', InvoiceStatus.PRZETERMINOWANA)
        r = self.client.get(self._url(status='przeterminowana'))
        self.assertContains(r, 'FV/US07-L/VW-PRZ')
        self.assertNotContains(r, 'FV/US07-L/VW-WYS2')

    def test_filtr_nieznany_status_ignorowany(self):
        _make_invoice(self.sprawa, 'FV/US07-L/VW-IGN')
        r = self.client.get(self._url(status='nieznany'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'FV/US07-L/VW-IGN')

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
            client=cls.klient, case_number='TST-US07-MP-001',
            title='Sprawa do testów mark_paid', case_type=CaseType.CYWILNA,
        )

    def setUp(self):
        super().setUp()
        self.faktura = _make_invoice(self.sprawa, 'FV/US07-L/MP001')

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


@tag('integration')
class CaseDetailInvoiceTabLinkTest(StaffLawyerTestCase):
    """case_detail zakładka faktury: pozycja faktury ma link do listy z filtrem."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US07-LINK-001',
            title='Sprawa do testów linku faktury', case_type=CaseType.CYWILNA,
        )
        cls.faktura = _make_invoice(cls.sprawa, 'FV/US07/LINK')

    def _url(self):
        return reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=faktury'

    def test_pozycja_faktury_ma_link_do_listy_z_filtrem(self):
        r = self.client.get(self._url())
        expected_href = reverse('szkp:invoice_list') + '?q=FV/US07/LINK'
        self.assertContains(r, f'href="{expected_href}"')
