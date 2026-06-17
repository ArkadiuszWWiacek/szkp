"""
Testy integracyjne R-07: Widoki z ModelForm.

IDs: TI-R07-01 … TI-R07-14

Testowane zachowania widoku po stronie serwera (odpowiedź HTTP + DB):
  – GET edit endpoint musi zwracać 'form' (ModelForm) w kontekście
  – form.instance musi odpowiadać edytowanemu obiektowi
  – POST edit musi zapisywać przez form.save() (nie tworzy nowego rekordu)
  – Logika biznesowa (closed_at, gross_amount) musi być zachowana

"""

from datetime import date, timedelta
from decimal import Decimal

from django import forms
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseStatus, CaseType,
    Client, ClientType,
    CourtHearing, HearingType,
    Document, DocumentType,
    Invoice, InvoiceStatus,
    Lawyer,
)
from szkp.tests.base import StaffLawyerTestCase


# ===========================================================================
# TI-R07-01 … TI-R07-05  GET edit — kontekst musi zawierać 'form'
# ===========================================================================

@tag('integration')
class R07ViewContextFormKeyTest(StaffLawyerTestCase):
    """GET na formularz edycji musi zwracać 'form' (ModelForm) w kontekście."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-R07-CTX-001',
            title='Sprawa integracyjna R-07', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=cls.sprawa, lawyer=cls.lawyer, role=CaseLawyerRole.PROWADZACY,
        )
        cls.firma = Client.objects.create(
            type=ClientType.FIRMA,
            company_name='Firma Integracyjna', nip='5250012340',
        )
        cls.faktura = Invoice.objects.create(
            case=cls.sprawa, invoice_number='FV/R07/CTX/001',
            net_amount=Decimal('500.00'),
            issue_date=date.today(), due_date=date.today() + timedelta(days=14),
        )
        cls.termin = CourtHearing.objects.create(
            case=cls.sprawa,
            court_name='Sąd Integracyjny', hearing_type=HearingType.ROZPRAWA,
            scheduled_at=timezone.now() + timedelta(days=30),
        )
        cls.dokument = Document.objects.create(
            case=cls.sprawa, title='Dokument integracyjny',
            document_type=DocumentType.NOTATKA,
        )

    # TI-R07-01
    def test_get_client_edit_kontekst_zawiera_klucz_form(self):
        """GET /klienci/<pk>/edytuj/ musi zwracać 'form' w kontekście szablonu."""
        resp = self.client.get(
            reverse('szkp:client_edit', kwargs={'pk': self.firma.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            'form', resp.context,
            "Widok client_form (edycja) musi przekazywać 'form' (ModelForm) do kontekstu",
        )

    # TI-R07-02
    def test_get_case_edit_kontekst_zawiera_klucz_form(self):
        """GET /sprawy/<pk>/edytuj/ musi zwracać 'form' w kontekście szablonu."""
        resp = self.client.get(
            reverse('szkp:case_edit', kwargs={'pk': self.sprawa.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            'form', resp.context,
            "Widok case_form (edycja) musi przekazywać 'form' (ModelForm) do kontekstu",
        )

    # TI-R07-03
    def test_get_invoice_edit_kontekst_zawiera_klucz_form(self):
        """GET /sprawy/<cpk>/faktury/<pk>/edytuj/ musi zwracać 'form' w kontekście."""
        resp = self.client.get(
            reverse('szkp:invoice_edit',
                    kwargs={'case_pk': self.sprawa.pk, 'pk': self.faktura.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            'form', resp.context,
            "Widok invoice_form (edycja) musi przekazywać 'form' (ModelForm) do kontekstu",
        )

    # TI-R07-04
    def test_get_court_hearing_edit_kontekst_zawiera_klucz_form(self):
        """GET /sprawy/<cpk>/terminy/<pk>/edytuj/ musi zwracać 'form' w kontekście."""
        resp = self.client.get(
            reverse('szkp:court_hearing_edit',
                    kwargs={'case_pk': self.sprawa.pk, 'pk': self.termin.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            'form', resp.context,
            "Widok court_hearing_form (edycja) musi przekazywać 'form' (ModelForm) do kontekstu",
        )

    # TI-R07-05
    def test_get_document_edit_kontekst_zawiera_klucz_form(self):
        """GET /sprawy/<cpk>/dokumenty/<pk>/edytuj/ musi zwracać 'form' w kontekście."""
        resp = self.client.get(
            reverse('szkp:document_edit',
                    kwargs={'case_pk': self.sprawa.pk, 'pk': self.dokument.pk})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            'form', resp.context,
            "Widok document_form (edycja) musi przekazywać 'form' (ModelForm) do kontekstu",
        )


# ===========================================================================
# TI-R07-06 … TI-R07-08  GET edit — 'form' musi być instancją ModelForm
# ===========================================================================

@tag('integration')
class R07ViewContextFormTypeTest(StaffLawyerTestCase):
    """Klucz 'form' w kontekście musi być instancją forms.ModelForm."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-R07-TYPE-001',
            title='Sprawa typ R-07', case_type=CaseType.CYWILNA,
        )
        cls.firma = Client.objects.create(
            type=ClientType.FIRMA,
            company_name='Firma Typ', nip='5250012341',
        )
        cls.faktura = Invoice.objects.create(
            case=cls.sprawa, invoice_number='FV/R07/TYPE/001',
            net_amount=Decimal('100.00'),
            issue_date=date.today(), due_date=date.today() + timedelta(days=14),
        )

    # TI-R07-06
    def test_client_edit_form_jest_instancja_modelform(self):
        """Kontekst client_form (edycja): form musi być instancją forms.ModelForm."""
        resp = self.client.get(
            reverse('szkp:client_edit', kwargs={'pk': self.firma.pk})
        )
        self.assertIn('form', resp.context)
        self.assertIsInstance(
            resp.context['form'], forms.ModelForm,
            "context['form'] musi być instancją forms.ModelForm",
        )

    # TI-R07-07
    def test_case_edit_form_jest_instancja_modelform(self):
        """Kontekst case_form (edycja): form musi być instancją forms.ModelForm."""
        resp = self.client.get(
            reverse('szkp:case_edit', kwargs={'pk': self.sprawa.pk})
        )
        self.assertIn('form', resp.context)
        self.assertIsInstance(
            resp.context['form'], forms.ModelForm,
            "context['form'] musi być instancją forms.ModelForm",
        )

    # TI-R07-08
    def test_invoice_edit_form_jest_instancja_modelform(self):
        """Kontekst invoice_form (edycja): form musi być instancją forms.ModelForm."""
        resp = self.client.get(
            reverse('szkp:invoice_edit',
                    kwargs={'case_pk': self.sprawa.pk, 'pk': self.faktura.pk})
        )
        self.assertIn('form', resp.context)
        self.assertIsInstance(
            resp.context['form'], forms.ModelForm,
            "context['form'] musi być instancją forms.ModelForm",
        )


# ===========================================================================
# TI-R07-09 … TI-R07-10  GET edit — form.instance to edytowany obiekt
# ===========================================================================

@tag('integration')
class R07ViewFormInstanceTest(StaffLawyerTestCase):
    """form.instance musi odpowiadać edytowanemu obiektowi z bazy."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-R07-INST-001',
            title='Sprawa instance R-07', case_type=CaseType.CYWILNA,
        )
        cls.firma = Client.objects.create(
            type=ClientType.FIRMA,
            company_name='Firma Instance', nip='5250012342',
        )

    # TI-R07-09
    def test_client_edit_form_instance_to_edytowany_klient(self):
        """context['form'].instance.pk musi być równe pk edytowanego klienta."""
        resp = self.client.get(
            reverse('szkp:client_edit', kwargs={'pk': self.firma.pk})
        )
        self.assertIn('form', resp.context)
        self.assertEqual(
            resp.context['form'].instance.pk, self.firma.pk,
            "form.instance.pk musi odpowiadać pk edytowanego klienta",
        )

    # TI-R07-10
    def test_case_edit_form_instance_to_edytowana_sprawa(self):
        """context['form'].instance.pk musi być równe pk edytowanej sprawy."""
        resp = self.client.get(
            reverse('szkp:case_edit', kwargs={'pk': self.sprawa.pk})
        )
        self.assertIn('form', resp.context)
        self.assertEqual(
            resp.context['form'].instance.pk, self.sprawa.pk,
            "form.instance.pk musi odpowiadać pk edytowanej sprawy",
        )


# ===========================================================================
# TI-R07-11 … TI-R07-14  Logika biznesowa
# ===========================================================================

@tag('integration')
class R07ViewBusinessLogicTest(StaffLawyerTestCase):
    """Logika biznesowa w widokach musi być zachowana po przejściu na form.save()."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-R07-BIZ-001',
            title='Sprawa logika biznesowa R-07', case_type=CaseType.CYWILNA,
            status=CaseStatus.NOWA,
        )
        CaseLawyer.objects.create(
            case=cls.sprawa, lawyer=cls.lawyer, role=CaseLawyerRole.PROWADZACY,
        )

    # TI-R07-11
    def test_post_client_edit_nie_tworzy_nowego_rekordu(self):
        """POST edycji klienta aktualizuje istniejący rekord — nie tworzy nowego."""
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Do', last_name='Edycji', pesel='89010199999',
        )
        liczba_przed = Client.objects.count()
        resp = self.client.post(
            reverse('szkp:client_edit', kwargs={'pk': klient.pk}),
            data={
                'type': ClientType.OSOBA_FIZYCZNA,
                'first_name': 'Po',
                'last_name': 'Edycji',
                'pesel': '89010199999',
            },
        )
        self.assertEqual(
            Client.objects.count(), liczba_przed,
            'Edycja klienta nie może tworzyć nowego rekordu w bazie',
        )

    # TI-R07-12
    def test_post_case_edit_zakonczona_ustawia_closed_at(self):
        """POST edycji sprawy ze statusem ZAKOŃCZONA musi ustawić pole closed_at."""
        self.assertIsNone(self.sprawa.closed_at)
        self.client.post(
            reverse('szkp:case_edit', kwargs={'pk': self.sprawa.pk}),
            data={
                'case_number': self.sprawa.case_number,
                'title': self.sprawa.title,
                'client': self.klient.pk,
                'case_type': CaseType.CYWILNA,
                'status': CaseStatus.ZAKOŃCZONA,
                'case_priority': '',
            },
        )
        self.sprawa.refresh_from_db()
        self.assertIsNotNone(
            self.sprawa.closed_at,
            'Po zapisie sprawy z status=ZAKOŃCZONA pole closed_at musi być ustawione',
        )

    # TI-R07-13
    def test_post_invoice_edit_przelicza_gross_amount(self):
        """POST edycji faktury ze zmianą net_amount przelicza gross_amount przez Invoice.save()."""
        faktura = Invoice.objects.create(
            case=self.sprawa, invoice_number='FV/R07/BIZ/001',
            net_amount=Decimal('1000.00'), vat_rate=Decimal('0.23'),
            issue_date=date.today(), due_date=date.today() + timedelta(days=14),
        )
        self.assertEqual(faktura.gross_amount, Decimal('1230.00'))
        self.client.post(
            reverse('szkp:invoice_edit',
                    kwargs={'case_pk': self.sprawa.pk, 'pk': faktura.pk}),
            data={
                'invoice_number': 'FV/R07/BIZ/001',
                'issue_date': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'due_date': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'net_amount': '2000.00',
                'vat_rate': '0.23',
                'currency': 'PLN',
                'status': InvoiceStatus.WYSTAWIONA,
            },
        )
        faktura.refresh_from_db()
        self.assertEqual(
            faktura.gross_amount, Decimal('2460.00'),
            'gross_amount musi być przeliczone po edycji net_amount przez formularz',
        )

    # TI-R07-14
    def test_post_invoice_edit_wlasny_numer_nie_daje_bledu_unikalnosci(self):
        """POST edycji faktury z tym samym invoice_number nie powinien zwracać błędu."""
        faktura = Invoice.objects.create(
            case=self.sprawa, invoice_number='FV/R07/BIZ/UNIQ',
            net_amount=Decimal('500.00'),
            issue_date=date.today(), due_date=date.today() + timedelta(days=14),
        )
        resp = self.client.post(
            reverse('szkp:invoice_edit',
                    kwargs={'case_pk': self.sprawa.pk, 'pk': faktura.pk}),
            data={
                'invoice_number': 'FV/R07/BIZ/UNIQ',   # ten sam numer
                'issue_date': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'due_date': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'net_amount': '500.00',
                'vat_rate': '0.23',
                'currency': 'PLN',
                'status': InvoiceStatus.WYSTAWIONA,
            },
        )
        # Redirect (302) = sukces; odpowiedź 200 = błąd walidacji
        self.assertEqual(
            resp.status_code, 302,
            'Edycja faktury z własnym numerem musi zakończyć się sukcesem (302), '
            'nie błędem walidacji (200)',
        )
