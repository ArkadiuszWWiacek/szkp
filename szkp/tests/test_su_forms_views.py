"""Testy integracyjne: Widoki formularzy SU — TI-SU-01 – TI-SU-18.

Weryfikują, że widoki:
  1. Wybierają szablon *_su.html dla superużytkownika
  2. Zachowują *regularny* szablon dla staff (nie-SU) — regresja
  3. Zapisują do bazy pola specyficzne dla SU (opened_at, country, itp.)
  4. case_lawyer_add akceptuje rolę PROWADZĄCY od SU

Testy są RED: widoki nie rozgałęziają się jeszcze na is_superuser.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseType, CaseStatus,
    Client, ClientType,
    CourtHearing,
    Invoice, InvoiceStatus,
    Lawyer,
    Task, TaskStatus,
)
from szkp.tests.utils import make_due


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-01 – TI-SU-04: case_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class CaseFormSUViewTest(TestCase):
    """SU na case_form dostaje szablon case_form_su.html i może zapisać opened_at / closed_at."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_casev', password='x', is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_casev', password='x', is_staff=True, is_superuser=False,
        )
        Lawyer.objects.create(
            user=cls.staff, first_name='Jan', last_name='Prawnik', bar_number='TST/CV/001',
        )
        cls.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Test', last_name='Klientv', pesel='80010112340',
        )

    def test_ti_su_01_su_case_form_uzywa_szablonu_su(self):
        """TI-SU-01: GET case_form jako SU → szablon szkp/case_form_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:case_new'))
        self.assertTemplateUsed(
            response, 'szkp/case_form_su.html',
            'SU na case_form nie używa szablonu case_form_su.html',
        )

    def test_ti_su_02_staff_case_form_uzywa_regularnego_szablonu(self):
        """TI-SU-02: GET case_form jako staff (nie SU) → szablon szkp/case_form.html."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('szkp:case_new'))
        self.assertTemplateUsed(
            response, 'szkp/case_form.html',
            'Staff na case_form nie używa szablonu case_form.html — regresja',
        )
        self.assertTemplateNotUsed(response, 'szkp/case_form_su.html')

    def test_ti_su_03_su_case_form_zapisuje_opened_at(self):
        """TI-SU-03: POST case_form jako SU z opened_at → Case.opened_at utrwalone w DB."""
        self.client.force_login(self.superuser)
        data = {
            'case_number': 'TST/SU/OA/001',
            'title': 'Sprawa SU opened_at',
            'client': self.klient.pk,
            'case_type': CaseType.CYWILNA,
            'opened_at': '2026-01-15T10:00',
        }
        self.client.post(reverse('szkp:case_new'), data)
        case = Case.objects.filter(case_number='TST/SU/OA/001').first()
        self.assertIsNotNone(case, 'Sprawa nie została zapisana')
        self.assertIsNotNone(
            case.opened_at,
            'Case.opened_at nie zostało zapisane — widok SU nie obsługuje tego pola',
        )

    def test_ti_su_04_su_case_form_zapisuje_closed_at(self):
        """TI-SU-04: POST case_form jako SU z closed_at przy status NOWA → Case.closed_at utrwalone.

        Status NOWA celowo: przy ZAKONCZONA widok sam ustawia closed_at (timezone.now()),
        co maskowaloby brak obslugi pola w formularzu SU.
        """
        self.client.force_login(self.superuser)
        data = {
            'case_number': 'TST/SU/CA/001',
            'title': 'Sprawa SU closed_at',
            'client': self.klient.pk,
            'case_type': CaseType.CYWILNA,
            'status': CaseStatus.NOWA,
            'closed_at': '2026-03-20T15:30',
        }
        self.client.post(reverse('szkp:case_new'), data)
        case = Case.objects.filter(case_number='TST/SU/CA/001').first()
        self.assertIsNotNone(case, 'Sprawa nie zostala zapisana')
        self.assertIsNotNone(
            case.closed_at,
            'Case.closed_at nie zostalo zapisane — widok SU nie obsluguje pola closed_at '
            'gdy status != ZAKONCZONA',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-05 – TI-SU-07: client_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class ClientFormSUViewTest(TestCase):
    """SU na client_form dostaje szablon client_form_su.html i może zapisać country."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_clientv', password='x', is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_clientv', password='x', is_staff=True, is_superuser=False,
        )

    def test_ti_su_05_su_client_form_uzywa_szablonu_su(self):
        """TI-SU-05: GET client_form jako SU → szablon szkp/client_form_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:client_new'))
        self.assertTemplateUsed(
            response, 'szkp/client_form_su.html',
            'SU na client_form nie używa szablonu client_form_su.html',
        )

    def test_ti_su_06_staff_client_form_uzywa_regularnego_szablonu(self):
        """TI-SU-06: GET client_form jako staff (nie SU) → szablon szkp/client_form.html."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('szkp:client_new'))
        self.assertTemplateUsed(
            response, 'szkp/client_form.html',
            'Staff na client_form nie używa szablonu client_form.html — regresja',
        )
        self.assertTemplateNotUsed(response, 'szkp/client_form_su.html')

    def test_ti_su_07_su_client_form_zapisuje_country(self):
        """TI-SU-07: POST client_form jako SU z country='Niemcy' → Client.country='Niemcy' w DB."""
        self.client.force_login(self.superuser)
        data = {
            'type': ClientType.OSOBA_FIZYCZNA,
            'first_name': 'Hans',
            'last_name': 'MullerSU',
            'pesel': '90010112340',
            'country': 'Niemcy',
        }
        self.client.post(reverse('szkp:client_new'), data)
        klient = Client.objects.filter(last_name='MullerSU').first()
        self.assertIsNotNone(klient, 'Klient nie został zapisany')
        self.assertEqual(
            klient.country, 'Niemcy',
            f'Client.country="{klient.country if klient else "?"}" zamiast "Niemcy" — widok SU nie obsługuje tego pola',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-08 – TI-SU-10: court_hearing_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class CourtHearingFormSUViewTest(TestCase):
    """SU na court_hearing_form dostaje szablon court_hearing_form_su.html i może zapisać responsible_lawyer."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_hearv', password='x', is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_hearv', password='x', is_staff=True, is_superuser=False,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Hear', last_name='Klientv', pesel='80010112341',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/HEARV/001',
            title='Sprawa terminow', case_type=CaseType.CYWILNA,
        )
        cls.lawyer_staff = Lawyer.objects.create(
            user=cls.staff, first_name='Jan', last_name='Asystent', bar_number='TST/HV/001',
        )
        CaseLawyer.objects.create(
            case=cls.case, lawyer=cls.lawyer_staff, role=CaseLawyerRole.ASYSTENT,
        )
        cls.responsible_lawyer = Lawyer.objects.create(
            first_name='Odp', last_name='Prawnik', bar_number='TST/HV/002',
        )

    def _url(self):
        return reverse('szkp:court_hearing_new', kwargs={'case_pk': self.case.pk})

    def test_ti_su_08_su_hearing_form_uzywa_szablonu_su(self):
        """TI-SU-08: GET court_hearing_form jako SU → szablon szkp/court_hearing_form_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(self._url())
        self.assertTemplateUsed(
            response, 'szkp/court_hearing_form_su.html',
            'SU na court_hearing_form nie używa szablonu court_hearing_form_su.html',
        )

    def test_ti_su_09_staff_hearing_form_uzywa_regularnego_szablonu(self):
        """TI-SU-09: GET court_hearing_form jako staff → szablon szkp/court_hearing_form.html."""
        self.client.force_login(self.staff)
        response = self.client.get(self._url())
        self.assertTemplateUsed(
            response, 'szkp/court_hearing_form.html',
            'Staff na court_hearing_form nie używa szablonu court_hearing_form.html — regresja',
        )
        self.assertTemplateNotUsed(response, 'szkp/court_hearing_form_su.html')

    def test_ti_su_10_su_hearing_form_zapisuje_responsible_lawyer(self):
        """TI-SU-10: POST court_hearing_form jako SU z responsible_lawyer → saved w DB."""
        self.client.force_login(self.superuser)
        future_dt = make_due(3).strftime('%Y-%m-%dT%H:%M')
        data = {
            'court_name': 'Sąd Rejonowy SU',
            'hearing_type': 'rozprawa',
            'scheduled_at': future_dt,
            'responsible_lawyer': self.responsible_lawyer.pk,
        }
        self.client.post(self._url(), data)
        hearing = CourtHearing.objects.filter(court_name='Sąd Rejonowy SU').first()
        self.assertIsNotNone(hearing, 'CourtHearing nie został zapisany')
        self.assertEqual(
            hearing.responsible_lawyer_id, self.responsible_lawyer.pk,
            'CourtHearing.responsible_lawyer nie zostało zapisane przez widok SU',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-11 – TI-SU-12: invoice_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class InvoiceFormSUViewTest(TestCase):
    """SU na invoice_form dostaje szablon invoice_form_su.html."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_invv', password='x', is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_invv', password='x', is_staff=True, is_superuser=False,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Inv', last_name='Klientv', pesel='80010112342',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/INVV/001',
            title='Sprawa faktur', case_type=CaseType.CYWILNA,
        )
        lawyer_staff = Lawyer.objects.create(
            user=cls.staff, first_name='Jan', last_name='InvPrawnik', bar_number='TST/IV/001',
        )
        CaseLawyer.objects.create(
            case=cls.case, lawyer=lawyer_staff, role=CaseLawyerRole.ASYSTENT,
        )

    def _url(self):
        return reverse('szkp:invoice_new', kwargs={'case_pk': self.case.pk})

    def test_ti_su_11_su_invoice_form_uzywa_szablonu_su(self):
        """TI-SU-11: GET invoice_form jako SU → szablon szkp/invoice_form_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(self._url())
        self.assertTemplateUsed(
            response, 'szkp/invoice_form_su.html',
            'SU na invoice_form nie używa szablonu invoice_form_su.html',
        )

    def test_ti_su_12_staff_invoice_form_uzywa_regularnego_szablonu(self):
        """TI-SU-12: GET invoice_form jako staff → szablon szkp/invoice_form.html."""
        self.client.force_login(self.staff)
        response = self.client.get(self._url())
        self.assertTemplateUsed(
            response, 'szkp/invoice_form.html',
            'Staff na invoice_form nie używa szablonu invoice_form.html — regresja',
        )
        self.assertTemplateNotUsed(response, 'szkp/invoice_form_su.html')


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-13 – TI-SU-14: task_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class TaskFormSUViewTest(TestCase):
    """SU na task_form dostaje szablon task_form_su.html."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_taskv', password='x', is_staff=True, is_superuser=True,
        )
        Lawyer.objects.create(
            user=cls.superuser, first_name='Su', last_name='Admin', bar_number='TST/TV/SU',
        )
        cls.staff = User.objects.create_user(
            username='staff_taskv', password='x', is_staff=True, is_superuser=False,
        )
        Lawyer.objects.create(
            user=cls.staff, first_name='Jan', last_name='TaskPrawnik', bar_number='TST/TV/001',
        )

    def test_ti_su_13_su_task_form_uzywa_szablonu_su(self):
        """TI-SU-13: GET task_form jako SU → szablon szkp/task_form_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:task_new'))
        self.assertTemplateUsed(
            response, 'szkp/task_form_su.html',
            'SU na task_form nie używa szablonu task_form_su.html',
        )

    def test_ti_su_14_staff_task_form_uzywa_regularnego_szablonu(self):
        """TI-SU-14: GET task_form jako staff → szablon szkp/task_form.html."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('szkp:task_new'))
        self.assertTemplateUsed(
            response, 'szkp/task_form.html',
            'Staff na task_form nie używa szablonu task_form.html — regresja',
        )
        self.assertTemplateNotUsed(response, 'szkp/task_form_su.html')


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-15 – TI-SU-16: case_lawyer_add
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class CaseLawyerFormSUViewTest(TestCase):
    """SU na case_lawyer_add dostaje szablon case_lawyer_add_su.html i może przypisać PROWADZĄCY."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_clv', password='x', is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_clv', password='x', is_staff=True, is_superuser=False,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='CL', last_name='Klientv', pesel='80010112343',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/CLV/001',
            title='Sprawa prawnicy SU', case_type=CaseType.CYWILNA,
        )
        cls.lead_lawyer = Lawyer.objects.create(
            user=cls.staff, first_name='Jan', last_name='Prowadzacy', bar_number='TST/CLV/001',
        )
        CaseLawyer.objects.create(
            case=cls.case, lawyer=cls.lead_lawyer, role=CaseLawyerRole.PROWADZACY,
        )
        cls.other_lawyer = Lawyer.objects.create(
            first_name='Inny', last_name='PrawnikCL', bar_number='TST/CLV/002',
        )

    def _url(self):
        return reverse('szkp:case_lawyer_add', kwargs={'case_pk': self.case.pk})

    def test_ti_su_15_su_case_lawyer_add_uzywa_szablonu_su(self):
        """TI-SU-15: GET case_lawyer_add jako SU → szablon szkp/case_lawyer_add_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(self._url())
        self.assertTemplateUsed(
            response, 'szkp/case_lawyer_add_su.html',
            'SU na case_lawyer_add nie używa szablonu case_lawyer_add_su.html',
        )

    def test_ti_su_16_su_zapisuje_case_lawyer_z_rola_prowadzacy(self):
        """TI-SU-16: POST case_lawyer_add jako SU z role=PROWADZĄCY → CaseLawyer zapisany w DB."""
        self.client.force_login(self.superuser)
        data = {
            'lawyer': self.other_lawyer.pk,
            'role': CaseLawyerRole.PROWADZACY,
        }
        self.client.post(self._url(), data)
        cl = CaseLawyer.objects.filter(
            case=self.case, lawyer=self.other_lawyer,
        ).first()
        self.assertIsNotNone(
            cl,
            'CaseLawyer nie został zapisany — SU nie może przypisać PROWADZĄCY przez case_lawyer_add',
        )
        self.assertEqual(
            cl.role if cl else None,
            CaseLawyerRole.PROWADZACY,
            f'CaseLawyer.role="{cl.role if cl else "?"}" zamiast PROWADZACY',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-17 – TI-SU-18: document_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class DocumentFormSUViewTest(TestCase):
    """SU na document_form dostaje szablon document_form_su.html."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_docv', password='x', is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_docv', password='x', is_staff=True, is_superuser=False,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Doc', last_name='Klientv', pesel='80010112344',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/DOCV/001',
            title='Sprawa dokumentow', case_type=CaseType.CYWILNA,
        )
        lawyer_staff = Lawyer.objects.create(
            user=cls.staff, first_name='Jan', last_name='DocPrawnik', bar_number='TST/DV/001',
        )
        CaseLawyer.objects.create(
            case=cls.case, lawyer=lawyer_staff, role=CaseLawyerRole.ASYSTENT,
        )

    def _url(self):
        return reverse('szkp:document_new', kwargs={'case_pk': self.case.pk})

    def test_ti_su_17_su_document_form_uzywa_szablonu_su(self):
        """TI-SU-17: GET document_form jako SU → szablon szkp/document_form_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(self._url())
        self.assertTemplateUsed(
            response, 'szkp/document_form_su.html',
            'SU na document_form nie używa szablonu document_form_su.html',
        )

    def test_ti_su_18_staff_document_form_uzywa_regularnego_szablonu(self):
        """TI-SU-18: GET document_form jako staff → szablon szkp/document_form.html."""
        self.client.force_login(self.staff)
        response = self.client.get(self._url())
        self.assertTemplateUsed(
            response, 'szkp/document_form.html',
            'Staff na document_form nie używa szablonu document_form.html — regresja',
        )
        self.assertTemplateNotUsed(response, 'szkp/document_form_su.html')
