"""Testy funkcjonalne: Podgląd sprawy SU — TC-SU-D01 – TC-SU-D10.

Weryfikują, że superużytkownik widzi szczegóły sprawy w stylu base_dash.html
(pasek boczny .dash-sidebar) z pełną treścią zakładek i metadanymi modelu,
a formularz edycji poprawnie obsługuje link Anuluj.
"""
from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By

from Functional_tests.base import SzkpSeleniumTestCase
from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseType,
    Client, ClientType,
    CourtHearing, HearingType, HearingStatus,
    Lawyer,
    Task, TaskStatus,
)
from szkp.tests.utils import make_due


def _setup_case_with_data():
    """Tworzy sprawę z powiązanymi rekordami używaną przez wiele klas testowych."""
    klient = Client.objects.create(
        type=ClientType.OSOBA_FIZYCZNA,
        first_name='Tomasz', last_name='Klient', pesel='70010112345',
    )
    case = Case.objects.create(
        client=klient,
        case_number='TST/SUD/2024/001',
        title='Sprawa podglądu SU',
        case_type=CaseType.CYWILNA,
    )
    return case


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-D01 – TC-SU-D02: layout (base_dash vs base)
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCaseDetailLayoutTest(SzkpSeleniumTestCase):
    """TC-SU-D01–D02: SU widzi dash-sidebar; nie-SU widzi Bootstrap."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_casedetail', password='supass123',
            is_staff=True, is_superuser=True,
        )
        self.case = _setup_case_with_data()

    @tag('smoke')
    def test_tc_su_d01_su_case_detail_wyswietla_sidebar(self):
        """TC-SU-D01: SU na /szkp/sprawy/<pk>/ widzi .dash-sidebar (base_dash.html)."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case.pk}/')
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — SU na case_detail widzi szablon Bootstrap zamiast base_dash.html; '
            'case_detail_su.html nie istnieje lub view nie rozgałęzia dla SU',
        )

    def test_tc_su_d02_niesu_case_detail_nie_wyswietla_sidebar(self):
        """TC-SU-D02: Staff (nie SU) na /szkp/sprawy/<pk>/ NIE widzi .dash-sidebar."""
        staff = User.objects.create_user(
            username='staff_casedetail', password='staffpass123', is_staff=True,
        )
        lawyer_staff = Lawyer.objects.create(
            user=staff, first_name='Jan', last_name='Prawnik', bar_number='TST/SUD/002',
        )
        CaseLawyer.objects.create(
            case=self.case, lawyer=lawyer_staff, role=CaseLawyerRole.PROWADZACY,
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case.pk}/')
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            '.dash-sidebar obecny dla nie-SU na case_detail — błąd regresji szablonów',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-D03 – TC-SU-D04: pola sprawy i metadane
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCaseDetailFieldsTest(SzkpSeleniumTestCase):
    """TC-SU-D03–D04: SU widzi sygnaturę akt i metadane created_at."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_casefields', password='supass123',
            is_staff=True, is_superuser=True,
        )
        self.case = _setup_case_with_data()
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case.pk}/')

    def test_tc_su_d03_su_case_detail_wyswietla_sygnature(self):
        """TC-SU-D03: SU widzi sygnaturę akt sprawy (case_number) na stronie szczegółów."""
        body_text = self.selenium.find_element(By.TAG_NAME, 'body').text
        self.assertIn(
            self.case.case_number, body_text,
            f'Sygnatura {self.case.case_number!r} niewidoczna na stronie — '
            'case_detail_su.html nie renderuje pola case_number',
        )

    def test_tc_su_d04_su_case_detail_wyswietla_created_at(self):
        """TC-SU-D04: SU widzi metadane created_at na stronie szczegółów sprawy."""
        created_date = self.case.created_at.strftime('%d.%m.%Y')
        body_text = self.selenium.find_element(By.TAG_NAME, 'body').text
        self.assertIn(
            created_date, body_text,
            f'Data utworzenia {created_date!r} niewidoczna — '
            'case_detail_su.html nie wyświetla metadanych created_at',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-D05: zakładka Terminy
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCaseDetailTerminyTest(SzkpSeleniumTestCase):
    """TC-SU-D05: SU widzi zakładkę Terminy z listą terminów sądowych."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_caseterminy', password='supass123',
            is_staff=True, is_superuser=True,
        )
        self.case = _setup_case_with_data()
        self.hearing = CourtHearing.objects.create(
            case=self.case,
            court_name='Sąd Rejonowy w Testowie',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=make_due(10),
            status=HearingStatus.PLANOWANY,
        )
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case.pk}/?tab=terminy')

    def test_tc_su_d05_su_widzi_termin_sadowy_w_zakladce(self):
        """TC-SU-D05: SU w zakładce Terminy widzi nazwę sądu istniejącego terminu."""
        body_text = self.selenium.find_element(By.TAG_NAME, 'body').text
        self.assertIn(
            self.hearing.court_name, body_text,
            f'Nazwa sądu {self.hearing.court_name!r} niewidoczna w zakładce Terminy — '
            'case_detail_su.html nie renderuje listy terminów sądowych',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-D06: zakładka Prawnicy
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCaseDetailPrawnicyTest(SzkpSeleniumTestCase):
    """TC-SU-D06: SU widzi zakładkę Prawnicy z przypisanym prawnikiem."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_caseprawnicy', password='supass123',
            is_staff=True, is_superuser=True,
        )
        self.case = _setup_case_with_data()
        self.lawyer = Lawyer.objects.create(
            first_name='Anna', last_name='Kowalska', bar_number='TST/SUD/003',
        )
        CaseLawyer.objects.create(
            case=self.case, lawyer=self.lawyer, role=CaseLawyerRole.PROWADZACY,
        )
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case.pk}/?tab=prawnicy')

    def test_tc_su_d06_su_widzi_prawnika_w_zakladce(self):
        """TC-SU-D06: SU w zakładce Prawnicy widzi nazwisko przypisanego prawnika."""
        body_text = self.selenium.find_element(By.TAG_NAME, 'body').text
        self.assertIn(
            self.lawyer.last_name, body_text,
            f'Nazwisko {self.lawyer.last_name!r} niewidoczne w zakładce Prawnicy — '
            'case_detail_su.html nie renderuje listy przypisanych prawników',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-D07: zakładka Zadania
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCaseDetailZadaniaTest(SzkpSeleniumTestCase):
    """TC-SU-D07: SU widzi zakładkę Zadania z istniejącym zadaniem sprawy."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_casezadania', password='supass123',
            is_staff=True, is_superuser=True,
        )
        self.lawyer = Lawyer.objects.create(
            user=self.superuser, first_name='Su', last_name='Admin',
            bar_number='TST/SUD/004',
        )
        self.case = _setup_case_with_data()
        self.task = Task.objects.create(
            title='Zadanie powiązane ze sprawą',
            case=self.case,
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            due_date=make_due(7),
            status=TaskStatus.NOWE,
        )
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case.pk}/?tab=zadania')

    def test_tc_su_d07_su_widzi_zadanie_w_zakladce(self):
        """TC-SU-D07: SU w zakładce Zadania widzi tytuł istniejącego zadania sprawy."""
        body_text = self.selenium.find_element(By.TAG_NAME, 'body').text
        self.assertIn(
            self.task.title, body_text,
            f'Tytuł zadania {self.task.title!r} niewidoczny w zakładce Zadania — '
            'case_detail_su.html nie renderuje listy zadań powiązanych ze sprawą',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-D08 – TC-SU-D10: formularz edycji sprawy
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCaseFormCancelTest(SzkpSeleniumTestCase):
    """TC-SU-D08–D10: link Anuluj w formularzu edycji wraca do case_detail; nowy → case_list."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_caseformcancel', password='supass123',
            is_staff=True, is_superuser=True,
        )
        self.case = _setup_case_with_data()
        self._zaloguj_przez_orm(self.superuser)

    def test_tc_su_d08_anuluj_edycja_wraca_do_case_detail(self):
        """TC-SU-D08: Anuluj na formularzu edycji sprawy prowadzi do /szkp/sprawy/<pk>/."""
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case.pk}/edytuj/')
        cancel_links = self.selenium.find_elements(
            By.XPATH, '//a[contains(text(), "Anuluj")]',
        )
        self.assertGreater(
            len(cancel_links), 0,
            'Brak linku "Anuluj" na formularzu edycji sprawy',
        )
        cancel_href = cancel_links[0].get_attribute('href')
        expected_path = f'/szkp/sprawy/{self.case.pk}/'
        self.assertIn(
            expected_path, cancel_href,
            f'Link Anuluj wskazuje na {cancel_href!r} zamiast na {expected_path!r} — '
            'case_form_su.html nie używa case_detail jako celu anulowania edycji',
        )

    def test_tc_su_d09_anuluj_nowa_sprawa_wraca_do_case_list(self):
        """TC-SU-D09: Anuluj na formularzu nowej sprawy prowadzi do /szkp/sprawy/."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        cancel_links = self.selenium.find_elements(
            By.XPATH, '//a[contains(text(), "Anuluj")]',
        )
        self.assertGreater(
            len(cancel_links), 0,
            'Brak linku "Anuluj" na formularzu nowej sprawy',
        )
        cancel_href = cancel_links[0].get_attribute('href')
        self.assertIn(
            '/szkp/sprawy/', cancel_href,
            f'Link Anuluj wskazuje na {cancel_href!r} zamiast na /szkp/sprawy/ — '
            'case_form_su.html niepoprawnie obsługuje Anuluj dla nowej sprawy',
        )
        self.assertNotIn(
            f'/szkp/sprawy/{self.case.pk}/', cancel_href,
            'Anuluj w formularzu nowej sprawy wskazuje na konkretną sprawę zamiast na listę',
        )

    def test_tc_su_d10_formularz_edycji_wyswietla_created_at(self):
        """TC-SU-D10: Formularz edycji sprawy SU wyświetla datę created_at jako read-only."""
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case.pk}/edytuj/')
        created_date = self.case.created_at.strftime('%d.%m.%Y')
        body_text = self.selenium.find_element(By.TAG_NAME, 'body').text
        self.assertIn(
            created_date, body_text,
            f'Data created_at {created_date!r} niewidoczna w formularzu edycji sprawy — '
            'case_form_su.html nie wyświetla metadanych created_at / updated_at',
        )
