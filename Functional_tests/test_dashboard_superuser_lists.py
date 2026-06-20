"""Testy funkcjonalne: Widoki list dla superusera (PSU-L01 – PSU-L05)."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By

from Functional_tests.base import SzkpSeleniumTestCase
from szkp.models import (
    Case, CaseStatus, CaseType,
    Client, ClientType,
    Invoice, InvoiceStatus,
    Lawyer, Task, TaskStatus,
)
from szkp.tests.utils import make_due

SPRAWY      = '/szkp/sprawy/'
KLIENCI     = '/szkp/klienci/'
FAKTURY     = '/szkp/faktury/'
ZADANIA     = '/szkp/zadania/'
UZYTKOWNICY = '/szkp/uzytkownicy/'


# ═══════════════════════════════════════════════════════════════════════════
# PSU-L01: /szkp/sprawy/ — superuser
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserCaseListTest(SzkpSeleniumTestCase):
    """PSU-L01: Lista spraw dla superusera — layout dash + CRUD."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_lst_cases', password='x',
            is_staff=True, is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username='staff_lst_cases', password='x',
            is_staff=True, is_superuser=False,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Lista', last_name='Spraw', pesel='80010212300',
        )
        Case.objects.create(
            client=klient, case_number='TST/SU/CASE/001',
            title='Sprawa testowa lista', case_type=CaseType.CYWILNA,
            status=CaseStatus.NOWA,
        )

    def _jako_superuser(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + SPRAWY)

    def _jako_staff(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.staff)
        self.selenium.get(self.live_server_url + SPRAWY)

    @tag('smoke')
    def test_psu_l01a_superuser_widzi_dash_sidebar(self):
        """PSU-L01a: Superuser na /szkp/sprawy/ widzi sidebar layoutu dash (.dash-sidebar)."""
        self._jako_superuser()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — superuser widzi stary Bootstrap layout zamiast dash',
        )

    def test_psu_l01b_breadcrumb_zawiera_sprawy(self):
        """PSU-L01b: Breadcrumb w topbarze zawiera tekst identyfikujący sekcję spraw."""
        self._jako_superuser()
        bc = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-topbar-breadcrumb')
        self.assertTrue(len(bc) > 0, 'Brak elementu .dash-topbar-breadcrumb w topbarze')
        self.assertIn(
            'Sprawy', bc[0].text,
            f"Breadcrumb nie zawiera 'Sprawy': '{bc[0].text}'",
        )

    def test_psu_l01c_wiersz_zawiera_przycisk_edytuj(self):
        """PSU-L01c: W tabeli spraw każdy wiersz ma link 'Edytuj' (case_edit)."""
        self._jako_superuser()
        edit_links = self.selenium.find_elements(By.PARTIAL_LINK_TEXT, 'Edytuj')
        self.assertTrue(
            len(edit_links) > 0,
            'Brak linków "Edytuj" w tabeli spraw superusera — widok CRUD niezaimplementowany',
        )

    def test_psu_l01d_wiersz_zawiera_link_podglad(self):
        """PSU-L01d: W tabeli spraw każdy wiersz ma link 'Podgląd' do case_detail."""
        self._jako_superuser()
        view_links = self.selenium.find_elements(By.PARTIAL_LINK_TEXT, 'Podgląd')
        self.assertTrue(
            len(view_links) > 0,
            'Brak linków "Podgląd" w tabeli spraw — case_list_su.html niezaimplementowany',
        )

    def test_psu_l01e_przycisk_nowa_sprawa_w_dash_headerze(self):
        """PSU-L01e: Przycisk 'Nowa sprawa' w nagłówku dash (.dash-page-header .dash-btn)."""
        self._jako_superuser()
        btns = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-page-header .dash-btn')
        self.assertTrue(
            len(btns) > 0,
            'Brak .dash-btn w .dash-page-header — szablon case_list_su.html nie istnieje',
        )

    def test_psu_l01f_staff_bez_superuser_nie_widzi_dash(self):
        """PSU-L01f: Staff bez is_superuser na /szkp/sprawy/ NIE widzi .dash-sidebar (stary layout)."""
        self._jako_staff()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            'Staff bez is_superuser widzi .dash-sidebar — routing do dash-template jest nieprawidłowy',
        )


# ═══════════════════════════════════════════════════════════════════════════
# PSU-L02: /szkp/klienci/ — superuser
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserClientListTest(SzkpSeleniumTestCase):
    """PSU-L02: Lista klientów dla superusera — layout dash + CRUD z kasowaniem."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_lst_clients', password='x',
            is_staff=True, is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username='staff_lst_clients', password='x',
            is_staff=True, is_superuser=False,
        )
        Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Adam', last_name='Klientowy', pesel='80010212301',
        )

    def _jako_superuser(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + KLIENCI)

    def _jako_staff(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.staff)
        self.selenium.get(self.live_server_url + KLIENCI)

    @tag('smoke')
    def test_psu_l02a_superuser_widzi_dash_sidebar(self):
        """PSU-L02a: Superuser na /szkp/klienci/ widzi .dash-sidebar."""
        self._jako_superuser()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — superuser widzi stary Bootstrap layout zamiast dash',
        )

    def test_psu_l02b_wiersz_w_dash_tabeli_ma_edytuj_i_usun(self):
        """PSU-L02b: Wiersze tabeli dash (.dash-data-table) mają linki 'Edytuj' i 'Usuń'."""
        self._jako_superuser()
        edit_links = self.selenium.find_elements(
            By.CSS_SELECTOR, '.dash-data-table a[href*="/edytuj/"]',
        )
        delete_links = self.selenium.find_elements(
            By.CSS_SELECTOR, '.dash-data-table a[href*="/usun/"]',
        )
        self.assertTrue(
            len(edit_links) > 0,
            'Brak linków /edytuj/ wewnątrz .dash-data-table — client_list_su.html niezaimplementowany',
        )
        self.assertTrue(
            len(delete_links) > 0,
            'Brak linków /usun/ wewnątrz .dash-data-table — client_list_su.html niezaimplementowany',
        )

    def test_psu_l02c_klikniecie_usun_prowadzi_do_potwierdzenia(self):
        """PSU-L02c: Kliknięcie linku 'Usuń' w tabeli dash prowadzi do strony /usun/."""
        self._jako_superuser()
        delete_links = self.selenium.find_elements(
            By.CSS_SELECTOR, '.dash-data-table a[href*="/usun/"]',
        )
        self.assertTrue(
            len(delete_links) > 0,
            'Brak linków /usun/ w .dash-data-table — nie można kliknąć "Usuń"',
        )
        delete_links[0].click()
        self.assertIn(
            '/usun/', self.selenium.current_url,
            f'Kliknięcie "Usuń" nie przekierowuje do /usun/. URL: {self.selenium.current_url}',
        )

    def test_psu_l02d_przycisk_nowy_klient_w_dash_headerze(self):
        """PSU-L02d: Przycisk 'Nowy klient' w nagłówku dash (.dash-page-header .dash-btn)."""
        self._jako_superuser()
        btns = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-page-header .dash-btn')
        self.assertTrue(
            len(btns) > 0,
            'Brak .dash-btn w .dash-page-header — client_list_su.html niezaimplementowany',
        )

    def test_psu_l02e_staff_bez_superuser_nie_widzi_dash(self):
        """PSU-L02e: Staff bez is_superuser na /szkp/klienci/ NIE widzi .dash-sidebar (stary layout)."""
        self._jako_staff()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            'Staff bez is_superuser widzi .dash-sidebar — routing do dash-template jest nieprawidłowy',
        )


# ═══════════════════════════════════════════════════════════════════════════
# PSU-L03: /szkp/faktury/ — superuser
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserInvoiceListTest(SzkpSeleniumTestCase):
    """PSU-L03: Lista faktur dla superusera — layout dash + Edytuj + Opłacona."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_lst_inv', password='x',
            is_staff=True, is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username='staff_lst_inv', password='x',
            is_staff=True, is_superuser=False,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Fakt', last_name='Klient', pesel='80010212302',
        )
        case = Case.objects.create(
            client=klient, case_number='TST/SU/INV/001',
            title='Sprawa dla faktur', case_type=CaseType.CYWILNA,
        )
        Invoice.objects.create(
            case=case, invoice_number='FV/SU/001',
            net_amount=Decimal('1000.00'), status=InvoiceStatus.WYSTAWIONA,
            issue_date='2026-01-01', due_date='2026-03-01',
        )

    def _jako_superuser(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + FAKTURY)

    def _jako_staff(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.staff)
        self.selenium.get(self.live_server_url + FAKTURY)

    @tag('smoke')
    def test_psu_l03a_superuser_widzi_dash_sidebar(self):
        """PSU-L03a: Superuser na /szkp/faktury/ widzi .dash-sidebar."""
        self._jako_superuser()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — superuser widzi stary Bootstrap layout zamiast dash',
        )

    def test_psu_l03b_wiersz_w_dash_tabeli_ma_link_edytuj(self):
        """PSU-L03b: Wiersze tabeli dash (.dash-data-table) mają link 'Edytuj' do invoice_edit."""
        self._jako_superuser()
        edit_links = self.selenium.find_elements(
            By.CSS_SELECTOR, '.dash-data-table a[href*="/edytuj/"]',
        )
        self.assertTrue(
            len(edit_links) > 0,
            'Brak linków /edytuj/ wewnątrz .dash-data-table — invoice_list_su.html niezaimplementowany',
        )

    def test_psu_l03c_wiersz_wystawionej_faktury_ma_przycisk_oplacona(self):
        """PSU-L03c: Wiersz faktury wystawionej w tabeli dash zawiera formularz 'Opłacona' (POST)."""
        self._jako_superuser()
        paid_forms = self.selenium.find_elements(
            By.CSS_SELECTOR, '.dash-data-table form',
        )
        self.assertTrue(
            len(paid_forms) > 0,
            'Brak formularzy POST wewnątrz .dash-data-table — przycisk "Opłacona" niedostępny dla superusera',
        )

    def test_psu_l03d_staff_bez_superuser_nie_widzi_dash(self):
        """PSU-L03d: Staff bez is_superuser na /szkp/faktury/ NIE widzi .dash-sidebar (stary layout)."""
        self._jako_staff()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            'Staff bez is_superuser widzi .dash-sidebar — routing do dash-template jest nieprawidłowy',
        )


# ═══════════════════════════════════════════════════════════════════════════
# PSU-L04: /szkp/zadania/ — superuser
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserTaskListTest(SzkpSeleniumTestCase):
    """PSU-L04: Lista zadań dla superusera — layout dash + tabela + CRUD."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_lst_tasks', password='x',
            is_staff=True, is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username='staff_lst_tasks', password='x',
            is_staff=True, is_superuser=False,
        )
        inny_prawnik = Lawyer.objects.create(
            first_name='Inny', last_name='Prawnik', bar_number='TST/SU/ZAD/INP',
        )
        self.parent_task = Task.objects.create(
            title='Zadanie testowe listy su',
            assigned_lawyer=inny_prawnik,
            created_by=inny_prawnik,
            due_date=make_due(3),
            status=TaskStatus.NOWE,
        )
        self.subtask = Task.objects.create(
            title='Podzadanie testowe listy su',
            assigned_lawyer=inny_prawnik,
            created_by=inny_prawnik,
            parent_task=self.parent_task,
            due_date=make_due(5),
            status=TaskStatus.NOWE,
        )

    def _jako_superuser(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + ZADANIA)

    def _jako_staff(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.staff)
        self.selenium.get(self.live_server_url + ZADANIA)

    @tag('smoke')
    def test_psu_l04a_superuser_widzi_dash_sidebar(self):
        """PSU-L04a: Superuser na /szkp/zadania/ widzi .dash-sidebar."""
        self._jako_superuser()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — superuser widzi stary Bootstrap layout zamiast dash',
        )

    def test_psu_l04b_zadania_wyswietlane_w_tabeli_nie_kartach(self):
        """PSU-L04b: Lista zadań superusera używa formatu tabeli (.dash-data-table), nie kart."""
        self._jako_superuser()
        dash_tables = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-data-table')
        self.assertTrue(
            len(dash_tables) > 0,
            'Brak .dash-data-table — zadania wyświetlane w formacie kart (.szkp-task), nie w tabeli',
        )

    def test_psu_l04c_wiersz_w_dash_tabeli_ma_edytuj_i_usun(self):
        """PSU-L04c: Wiersze tabeli dash (.dash-data-table) mają linki 'Edytuj' i 'Usuń'."""
        self._jako_superuser()
        edit_links = self.selenium.find_elements(
            By.CSS_SELECTOR, '.dash-data-table a[href*="/edytuj/"]',
        )
        delete_links = self.selenium.find_elements(
            By.CSS_SELECTOR, '.dash-data-table a[href*="/usun/"]',
        )
        self.assertTrue(
            len(edit_links) > 0,
            'Brak linków /edytuj/ wewnątrz .dash-data-table — task_list_su.html niezaimplementowany',
        )
        self.assertTrue(
            len(delete_links) > 0,
            'Brak linków /usun/ wewnątrz .dash-data-table — task_list_su.html niezaimplementowany',
        )

    def test_psu_l04d_przycisk_nowe_zadanie_w_dash_headerze(self):
        """PSU-L04d: Przycisk 'Nowe zadanie' w nagłówku dash (.dash-page-header .dash-btn)."""
        self._jako_superuser()
        btns = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-page-header .dash-btn')
        self.assertTrue(
            len(btns) > 0,
            'Brak .dash-btn w .dash-page-header — task_list_su.html niezaimplementowany',
        )

    def test_psu_l04e_staff_bez_superuser_nie_widzi_dash(self):
        """PSU-L04e: Staff bez is_superuser na /szkp/zadania/ NIE widzi .dash-sidebar (stary layout)."""
        self._jako_staff()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            'Staff bez is_superuser widzi .dash-sidebar — routing do dash-template jest nieprawidłowy',
        )

    def test_psu_l04f_podzadania_wyswietlane_pod_zadaniem_nadrzednym(self):
        """PSU-L04f: Lista zadań SU wyświetla wiersze podzadań z klasą .task-row--subtask."""
        self._jako_superuser()
        subtask_rows = self.selenium.find_elements(By.CSS_SELECTOR, '.task-row--subtask')
        self.assertGreater(
            len(subtask_rows), 0,
            'Brak wierszy .task-row--subtask — podzadania nie są grupowane pod zadaniem nadrzędnym; '
            'task_list_su.html nie renderuje podzadań',
        )

    def test_psu_l04g_wiersz_podzadania_nie_ma_linku_edytuj(self):
        """PSU-L04g: Wiersze .task-row--subtask nie zawierają linku /edytuj/."""
        self._jako_superuser()
        subtask_rows = self.selenium.find_elements(By.CSS_SELECTOR, '.task-row--subtask')
        self.assertGreater(
            len(subtask_rows), 0,
            'Brak wierszy .task-row--subtask — nie można zweryfikować braku linku Edytuj',
        )
        for row in subtask_rows:
            edit_links = row.find_elements(By.CSS_SELECTOR, 'a[href*="/edytuj/"]')
            self.assertEqual(
                len(edit_links), 0,
                'Wiersz .task-row--subtask zawiera link /edytuj/ — podzadanie powinno być '
                'edytowalne tylko z formularza zadania nadrzędnego',
            )

    def test_psu_l04h_wiersz_nadrzedny_ma_link_edytuj(self):
        """PSU-L04h: Wiersze .task-row--parent zawierają link /edytuj/."""
        self._jako_superuser()
        parent_rows = self.selenium.find_elements(By.CSS_SELECTOR, '.task-row--parent')
        self.assertGreater(
            len(parent_rows), 0,
            'Brak wierszy .task-row--parent — zadania nadrzędne nie mają wymaganej klasy CSS',
        )
        edit_links = parent_rows[0].find_elements(By.CSS_SELECTOR, 'a[href*="/edytuj/"]')
        self.assertGreater(
            len(edit_links), 0,
            'Wiersz .task-row--parent nie zawiera linku /edytuj/ — brak akcji edycji przy zadaniu nadrzędnym',
        )


# ═══════════════════════════════════════════════════════════════════════════
# PSU-L05: /szkp/uzytkownicy/ — superuser
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserUserListTest(SzkpSeleniumTestCase):
    """PSU-L05: Lista użytkowników dla superusera — nowy widok + zarządzanie kontami."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_lst_users', password='x',
            is_staff=True, is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username='staff_lst_users', password='x',
            is_staff=True, is_superuser=False,
        )
        User.objects.create_user(
            username='inny_uzytkownik', email='inny@test.pl',
            password='x', is_staff=False,
        )

    def _jako_superuser(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + UZYTKOWNICY)

    def _jako_staff(self):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.staff)
        self.selenium.get(self.live_server_url + UZYTKOWNICY)

    @tag('smoke')
    def test_psu_l05a_superuser_widzi_dash_sidebar(self):
        """PSU-L05a: Superuser na /szkp/uzytkownicy/ widzi .dash-sidebar."""
        self._jako_superuser()
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — URL /szkp/uzytkownicy/ nie istnieje lub nie używa layoutu dash',
        )

    def test_psu_l05b_widoczni_wszyscy_uzytkownicy(self):
        """PSU-L05b: Lista wyświetla wszystkich użytkowników (w tym 'inny_uzytkownik')."""
        self._jako_superuser()
        self.assertIn(
            'inny_uzytkownik',
            self.selenium.page_source,
            'Użytkownik "inny_uzytkownik" nie widoczny — widok /uzytkownicy/ nie istnieje lub nie zwraca listy',
        )

    def test_psu_l05c_link_edytuj_prowadzi_do_panelu_admin(self):
        """PSU-L05c: Linki 'Edytuj' w tabeli użytkowników wskazują na /admin/auth/user/."""
        self._jako_superuser()
        edit_links = self.selenium.find_elements(By.PARTIAL_LINK_TEXT, 'Edytuj')
        self.assertTrue(len(edit_links) > 0, 'Brak linków "Edytuj" na liście użytkowników')
        admin_links = [
            el for el in edit_links
            if '/admin/auth/user/' in (el.get_attribute('href') or '')
        ]
        self.assertTrue(
            len(admin_links) > 0,
            'Linki "Edytuj" nie prowadzą do /admin/auth/user/ — błędna nawigacja CRUD użytkowników',
        )

    def test_psu_l05d_wiersz_ma_przycisk_dezaktywuj_lub_aktywuj(self):
        """PSU-L05d: Każdy wiersz listy użytkowników zawiera przycisk toggle is_active."""
        self._jako_superuser()
        toggle_btns = self.selenium.find_elements(
            By.XPATH,
            "//*[contains(text(), 'Dezaktywuj') or contains(text(), 'Aktywuj')]",
        )
        self.assertTrue(
            len(toggle_btns) > 0,
            'Brak przycisków "Dezaktywuj"/"Aktywuj" — user_toggle_active niezaimplementowany',
        )

    def test_psu_l05e_przycisk_nowy_uzytkownik_widoczny(self):
        """PSU-L05e: Link/przycisk 'Nowy użytkownik' widoczny w nagłówku widoku."""
        self._jako_superuser()
        btns = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-page-header .dash-btn')
        self.assertTrue(
            len(btns) > 0,
            'Brak .dash-btn w .dash-page-header — user_list_su.html niezaimplementowany',
        )

    def test_psu_l05f_staff_bez_superuser_dostaje_403(self):
        """PSU-L05f: Staff bez is_superuser na /szkp/uzytkownicy/ dostaje 403 lub redirect na login."""
        self._jako_staff()
        current_url = self.selenium.current_url
        page_source = self.selenium.page_source
        is_login_redirect = 'login' in current_url
        is_forbidden = (
            '403' in page_source
            or 'Forbidden' in page_source
            or 'Zabroniony' in page_source
        )
        self.assertTrue(
            is_login_redirect or is_forbidden,
            f'Staff bez is_superuser nie dostał 403 ani redirectu na login. URL: {current_url}',
        )


# ═══════════════════════════════════════════════════════════════════════════
# PSU-L04-SS: /szkp/zadania/ — sortowanie i wyszukiwanie (superuser)
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserTaskListSortSearchTest(SzkpSeleniumTestCase):
    """PSU-L04-SS: Sortowanie kolumn i wyszukiwanie po tytule na liście zadań SU."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_sort_tasks', password='x',
            is_staff=True, is_superuser=True,
        )
        self.prawnik = Lawyer.objects.create(
            first_name='Jan', last_name='Kowalski', bar_number='TST/SS/001',
        )
        self.task_a = Task.objects.create(
            title='Analiza umowy',
            assigned_lawyer=self.prawnik,
            created_by=self.prawnik,
            due_date=make_due(5),
            status=TaskStatus.NOWE,
        )
        self.task_b = Task.objects.create(
            title='Rozprawa sądowa',
            assigned_lawyer=self.prawnik,
            created_by=self.prawnik,
            due_date=make_due(3),
            status=TaskStatus.W_TOKU,
        )

    def _jako_superuser(self, url_suffix=''):
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + ZADANIA + url_suffix)

    def test_psu_l04i_task_list_su_ma_pole_wyszukiwania(self):
        """PSU-L04i: Widok /szkp/zadania/ dla SU zawiera <input name="q"> w toolbarze."""
        self._jako_superuser()
        inputs = self.selenium.find_elements(By.CSS_SELECTOR, 'input[name="q"]')
        self.assertGreater(
            len(inputs), 0,
            'Brak <input name="q"> — pole wyszukiwania nie zostało dodane do task_list_su.html',
        )

    def test_psu_l04j_wyszukiwanie_filtruje_po_tytule(self):
        """PSU-L04j: Wyszukiwanie ?q=Analiza wyświetla tylko zadanie 'Analiza umowy'."""
        self._jako_superuser('?q=Analiza')
        source = self.selenium.page_source
        self.assertIn(
            'Analiza umowy', source,
            'Wyniki wyszukiwania nie zawierają "Analiza umowy" — filtrowanie po tytule nie działa',
        )
        self.assertNotIn(
            'Rozprawa sądowa', source,
            '"Rozprawa sądowa" nadal widoczna po wyszukaniu ?q=Analiza — filtr nie wyklucza niepasujących',
        )

    def test_psu_l04k_kolumna_prawnik_ma_link_sortowania(self):
        """PSU-L04k: Nagłówek kolumny 'Przypisany prawnik' zawiera <a href*="sort=assigned_lawyer">."""
        self._jako_superuser()
        sort_links = self.selenium.find_elements(
            By.CSS_SELECTOR, 'th a[href*="sort=assigned_lawyer"]',
        )
        self.assertGreater(
            len(sort_links), 0,
            'Brak <a href*="sort=assigned_lawyer"> w <th> — kolumna Przypisany prawnik nie jest sortowalna',
        )

    def test_psu_l04l_kolumna_termin_ma_link_sortowania(self):
        """PSU-L04l: Nagłówek kolumny 'Termin' zawiera <a href*="sort=due_date">."""
        self._jako_superuser()
        sort_links = self.selenium.find_elements(
            By.CSS_SELECTOR, 'th a[href*="sort=due_date"]',
        )
        self.assertGreater(
            len(sort_links), 0,
            'Brak <a href*="sort=due_date"> w <th> — kolumna Termin nie jest sortowalna',
        )

    def test_psu_l04m_kolumna_status_ma_link_sortowania(self):
        """PSU-L04m: Nagłówek kolumny 'Status' zawiera <a href*="sort=status">."""
        self._jako_superuser()
        sort_links = self.selenium.find_elements(
            By.CSS_SELECTOR, 'th a[href*="sort=status"]',
        )
        self.assertGreater(
            len(sort_links), 0,
            'Brak <a href*="sort=status"> w <th> — kolumna Status nie jest sortowalna',
        )

    def test_psu_l04n_kolumna_tytul_nie_ma_linku_sortowania(self):
        """PSU-L04n: Nagłówek 'Tytuł' jest zwykłym <th> bez linku sortowania."""
        self._jako_superuser()
        title_headers = self.selenium.find_elements(
            By.XPATH,
            "//thead//th[normalize-space(.)='Tytuł']",
        )
        self.assertGreater(
            len(title_headers), 0,
            'Brak komórki nagłówkowej "Tytuł" — nie można zweryfikować braku linku sortowania',
        )
        for th in title_headers:
            sort_links = th.find_elements(By.CSS_SELECTOR, 'a[href*="sort="]')
            self.assertEqual(
                len(sort_links), 0,
                'Komórka nagłówkowa "Tytuł" zawiera link sortowania — zgodnie ze specyfikacją '
                'ta kolumna nie powinna być sortowalna',
            )

    def test_psu_l04o_sortowanie_zmienia_kolejnosc_wynikow(self):
        """PSU-L04o: ?sort=status&dir=asc sortuje zadania rosnąco po statusie."""
        Task.objects.create(
            title='Zadanie zakończone',
            assigned_lawyer=self.prawnik,
            created_by=self.prawnik,
            due_date=make_due(1),
            status=TaskStatus.ZAKOŃCZONE,
        )
        self._jako_superuser('?sort=status&dir=asc')
        rows = self.selenium.find_elements(By.CSS_SELECTOR, '.task-row--parent')
        self.assertGreaterEqual(
            len(rows), 3,
            f'Oczekiwano ≥3 wierszy .task-row--parent po sortowaniu, znaleziono: {len(rows)}',
        )
        # Kolumna Status jest 5. (indeks 4): Tytuł|Prawnik|Sprawa|Termin|Status|Akcje
        statuses = [
            row.find_elements(By.TAG_NAME, 'td')[4].text
            for row in rows[:3]
        ]
        self.assertEqual(
            statuses, sorted(statuses),
            f'Kolejność statusów po sort=status&dir=asc nie jest rosnąca: {statuses}',
        )
