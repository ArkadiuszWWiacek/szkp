"""Testy integracyjne: Podgląd sprawy SU — TI-SU-CD-01 – TI-SU-CD-07.

Weryfikują, że:
  1. case_detail dla SU renderuje case_detail_su.html (base_dash.html)
  2. case_detail dla staff (nie SU) nadal renderuje case_detail.html (regresja)
  3. Kontekst widoku zawiera case z created_at / updated_at
  4. Powiązane obiekty (hearings, lawyers) trafiają do kontekstu
  5. case_form_su.html posiada poprawny link Anuluj (case_detail przy edycji, case_list przy tworzeniu)
"""
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseType,
    Client, ClientType,
    CourtHearing, HearingType, HearingStatus,
    Lawyer,
)
from szkp.tests.utils import make_due


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-CD-01 – TI-SU-CD-02: wybór szablonu przez case_detail
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class CaseDetailSUTemplateTest(TestCase):
    """case_detail rozgałęzia się na is_superuser i wybiera odpowiedni szablon."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_cdetail', password='x', is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_cdetail', password='x', is_staff=True, is_superuser=False,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Test', last_name='Klientcd', pesel='80010112350',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/CD/001',
            title='Sprawa integracja detail', case_type=CaseType.CYWILNA,
        )
        cls.lawyer_staff = Lawyer.objects.create(
            user=cls.staff, first_name='Jan', last_name='Staff', bar_number='TST/CD/S01',
        )
        CaseLawyer.objects.create(
            case=cls.case, lawyer=cls.lawyer_staff, role=CaseLawyerRole.PROWADZACY,
        )

    def test_ti_su_cd_01_su_case_detail_uzywa_szablonu_su(self):
        """TI-SU-CD-01: GET case_detail jako SU → szablon szkp/case_detail_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:case_detail', args=[self.case.pk]))
        self.assertTemplateUsed(
            response, 'szkp/case_detail_su.html',
            'SU na case_detail nie używa szablonu case_detail_su.html — '
            'view nie rozgałęzia na is_superuser',
        )

    def test_ti_su_cd_02_staff_case_detail_uzywa_regularnego_szablonu(self):
        """TI-SU-CD-02: GET case_detail jako staff (nie SU) → szkp/case_detail.html (regresja)."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('szkp:case_detail', args=[self.case.pk]))
        self.assertTemplateUsed(
            response, 'szkp/case_detail.html',
            'Staff na case_detail nie używa szablonu case_detail.html — regresja',
        )
        self.assertTemplateNotUsed(response, 'szkp/case_detail_su.html')


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-CD-03: context — created_at dostępne przez obiekt case
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class CaseDetailSUContextTest(TestCase):
    """case_detail przekazuje case z created_at / updated_at do kontekstu."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_ccontext', password='x', is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Context', last_name='Klient', pesel='80010112351',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/CD/CTX/001',
            title='Sprawa kontekstu SU', case_type=CaseType.KARNA,
        )

    def setUp(self):
        self.client.force_login(self.superuser)
        self.response = self.client.get(
            reverse('szkp:case_detail', args=[self.case.pk])
        )

    def test_ti_su_cd_03_context_zawiera_case_z_created_at(self):
        """TI-SU-CD-03: Kontekst case_detail zawiera obiekt case z polem created_at."""
        self.assertEqual(self.response.status_code, 200)
        ctx_case = self.response.context.get('case')
        self.assertIsNotNone(
            ctx_case,
            "Kontekst nie zawiera klucza 'case'",
        )
        self.assertIsNotNone(
            ctx_case.created_at,
            "case.created_at jest None — pole auto_now_add nie zostało ustawione",
        )

    def test_ti_su_cd_03b_response_zawiera_date_created_at(self):
        """TI-SU-CD-03b: Odpowiedź HTTP zawiera datę created_at (wyświetlaną w szablonie SU)."""
        created_date = self.case.created_at.strftime('%d.%m.%Y')
        self.assertContains(
            self.response, created_date,
            msg_prefix=f'Data created_at ({created_date}) niewidoczna w odpowiedzi — '
                       'case_detail_su.html nie wyświetla metadanych',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-CD-04: context — hearings
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class CaseDetailSUHearingsContextTest(TestCase):
    """case_detail przekazuje hearings dla zakładki Terminy."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_chearings', password='x', is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Hearing', last_name='Klient', pesel='80010112352',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/CD/H/001',
            title='Sprawa terminów', case_type=CaseType.CYWILNA,
        )
        cls.hearing = CourtHearing.objects.create(
            case=cls.case,
            court_name='Sąd Okręgowy',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=make_due(14),
            status=HearingStatus.PLANOWANY,
        )

    def test_ti_su_cd_04_context_zawiera_hearings_z_bazy(self):
        """TI-SU-CD-04: Kontekst case_detail zawiera hearings z terminem z bazy danych."""
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse('szkp:case_detail', args=[self.case.pk]) + '?tab=terminy'
        )
        self.assertEqual(response.status_code, 200)
        hearings = response.context.get('hearings')
        self.assertIsNotNone(hearings, "Kontekst nie zawiera klucza 'hearings'")
        self.assertEqual(
            hearings.count(), 1,
            f"Spodziewano się 1 terminu w kontekście, jest: {hearings.count()}",
        )
        self.assertIn(
            self.hearing, list(hearings),
            "Termin sądowy nie znalazł się w kontekście hearings",
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-CD-05: context — lawyers
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class CaseDetailSULawyersContextTest(TestCase):
    """case_detail przekazuje lawyers dla zakładki Prawnicy."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_clawyers', password='x', is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Lawyer', last_name='Klient', pesel='80010112353',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/CD/L/001',
            title='Sprawa prawników', case_type=CaseType.GOSPODARCZA,
        )
        cls.lawyer = Lawyer.objects.create(
            first_name='Maria', last_name='Kowalczyk', bar_number='TST/CD/L002',
        )
        cls.caselawyer = CaseLawyer.objects.create(
            case=cls.case, lawyer=cls.lawyer, role=CaseLawyerRole.PROWADZACY,
        )

    def test_ti_su_cd_05_context_zawiera_lawyers_z_bazy(self):
        """TI-SU-CD-05: Kontekst case_detail zawiera lawyers z przypisanym prawnikiem."""
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse('szkp:case_detail', args=[self.case.pk]) + '?tab=prawnicy'
        )
        self.assertEqual(response.status_code, 200)
        lawyers = response.context.get('lawyers')
        self.assertIsNotNone(lawyers, "Kontekst nie zawiera klucza 'lawyers'")
        self.assertEqual(
            lawyers.count(), 1,
            f"Spodziewano się 1 prawnika w kontekście, jest: {lawyers.count()}",
        )
        self.assertIn(
            self.caselawyer, list(lawyers),
            "CaseLawyer nie znalazł się w kontekście lawyers",
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SU-CD-06 – TI-SU-CD-07: link Anuluj w case_form_su.html
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class CaseFormSUCancelLinkTest(TestCase):
    """case_form_su.html: Anuluj przy edycji → case_detail; Anuluj przy tworzeniu → case_list."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_ccancel', password='x', is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Cancel', last_name='Klient', pesel='80010112354',
        )
        cls.case = Case.objects.create(
            client=klient, case_number='TST/CD/CC/001',
            title='Sprawa anulowania', case_type=CaseType.CYWILNA,
        )

    def test_ti_su_cd_06_anuluj_edycja_zawiera_url_case_detail(self):
        """TI-SU-CD-06: Formularz edycji sprawy (SU) zawiera link Anuluj → case_detail URL."""
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse('szkp:case_edit', args=[self.case.pk])
        )
        expected_url = reverse('szkp:case_detail', args=[self.case.pk])
        self.assertContains(
            response, expected_url,
            msg_prefix=(
                f'URL case_detail ({expected_url}) nieobecny w formularzu edycji — '
                'link Anuluj wskazuje na case_list zamiast case_detail'
            ),
        )

    def test_ti_su_cd_07_anuluj_nowy_zawiera_url_case_list(self):
        """TI-SU-CD-07: Formularz nowej sprawy (SU) zawiera link Anuluj → case_list URL."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:case_new'))
        case_list_url = reverse('szkp:case_list')
        detail_url = reverse('szkp:case_detail', args=[self.case.pk])
        self.assertContains(
            response, case_list_url,
            msg_prefix=(
                f'URL case_list ({case_list_url}) nieobecny w formularzu nowej sprawy — '
                'link Anuluj powinien wskazywać na listę spraw'
            ),
        )
        self.assertNotContains(
            response, detail_url,
            msg_prefix=(
                f'URL case_detail ({detail_url}) obecny w formularzu nowej sprawy — '
                'Anuluj nie powinien wskazywać na konkretną sprawę przy tworzeniu'
            ),
        )
