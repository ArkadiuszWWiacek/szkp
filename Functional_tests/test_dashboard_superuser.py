"""Testy funkcjonalne: Superuser Dashboard (TC-D01 – TC-D25)."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By

from Functional_tests.base import SzkpSeleniumTestCase
from szkp.models import (
    Case, CaseStatus, CaseType,
    Client, ClientType,
    Invoice, InvoiceStatus,
    Lawyer, Task, TaskPriority, TaskStatus,
)
from szkp.tests.utils import make_due


# ═══════════════════════════════════════════════════════════════════════════
# TC-D01 – TC-D07: Layout (sidebar, topbar, nawigacja)
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserDashboardLayoutTest(SzkpSeleniumTestCase):
    """Superuser Dashboard: struktura layoutu — sidebar, topbar, brak starego navbar."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='admin_layout',
            password='adminpass123',
            is_staff=True,
            is_superuser=True,
        )
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/pulpit/')

    @tag('smoke')
    def test_tc_d01_superuser_widzi_sidebar(self):
        """TC-D01: Superuser na /szkp/pulpit/ widzi sidebar (.dash-sidebar)."""
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak elementu .dash-sidebar — widok superusera wciąż renderuje stary template',
        )

    @tag('smoke')
    def test_tc_d02_superuser_widzi_topbar(self):
        """TC-D02: Superuser widzi topbar administracyjny (.dash-topbar)."""
        topbar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-topbar')
        self.assertTrue(
            len(topbar) > 0,
            'Brak elementu .dash-topbar — widok superusera wciąż renderuje stary template',
        )

    def test_tc_d03_brak_starego_navbar_bootstrap(self):
        """TC-D03: Stara nawigacja Bootstrap (.szkp-navbar) nie jest renderowana dla superusera."""
        navbar = self.selenium.find_elements(By.CSS_SELECTOR, '.szkp-navbar')
        self.assertEqual(
            len(navbar), 0,
            'Element .szkp-navbar wciąż istnieje — nowy template nie zastąpił base.html',
        )

    def test_tc_d04_topbar_zawiera_badge_superuser(self):
        """TC-D04: Topbar zawiera odznakę SUPERUSER (.dash-topbar-admin-badge)."""
        badge = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-topbar-admin-badge')
        self.assertTrue(
            len(badge) > 0,
            'Brak .dash-topbar-admin-badge — odznaka SUPERUSER nie jest renderowana w topbarze',
        )

    def test_tc_d05_breadcrumb_zawiera_pulpit_administracyjny(self):
        """TC-D05: Breadcrumb w topbarze zawiera tekst 'Pulpit administracyjny'."""
        self.assertIn(
            'Pulpit administracyjny',
            self.selenium.page_source,
            "Tekst 'Pulpit administracyjny' nie pojawia się na stronie superusera",
        )

    def test_tc_d06_sidebar_zawiera_link_do_spraw(self):
        """TC-D06: Sidebar zawiera link nawigacyjny do /szkp/sprawy/."""
        links = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-nav-item')
        hrefs = [el.get_attribute('href') or '' for el in links]
        self.assertTrue(
            any('/szkp/sprawy/' in href for href in hrefs),
            'Sidebar (.dash-nav-item) nie zawiera linku do /szkp/sprawy/',
        )

    def test_tc_d07_sidebar_zawiera_link_do_admin(self):
        """TC-D07: Sidebar superusera zawiera link do /admin/."""
        links = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-nav-item')
        hrefs = [el.get_attribute('href') or '' for el in links]
        self.assertTrue(
            any('/admin/' in href for href in hrefs),
            'Sidebar nie zawiera linku do panelu /admin/',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-D08 – TC-D12: Metryki
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserDashboardMetricsTest(SzkpSeleniumTestCase):
    """Superuser Dashboard: pasek metryk — 5 kart z poprawnymi liczbami z bazy."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='admin_metrics',
            password='adminpass123',
            is_staff=True,
            is_superuser=True,
        )
        self.lawyer = Lawyer.objects.create(
            first_name='Jan', last_name='Testowy', bar_number='TST/MX/001',
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Metryk', last_name='Klient', pesel='80010112345',
        )

        # 2 aktywne sprawy (NOWA + W_TOKU)
        Case.objects.create(
            client=self.klient, case_number='TST/MX/001',
            title='Sprawa aktywna pierwsza', case_type=CaseType.CYWILNA,
            status=CaseStatus.NOWA,
        )
        Case.objects.create(
            client=self.klient, case_number='TST/MX/002',
            title='Sprawa aktywna druga', case_type=CaseType.CYWILNA,
            status=CaseStatus.W_TOKU,
        )

        # 1 faktura przeterminowana
        case_for_inv = Case.objects.get(case_number='TST/MX/001')
        Invoice.objects.create(
            case=case_for_inv,
            invoice_number='FV/MX/001',
            net_amount=Decimal('1000.00'),
            status=InvoiceStatus.PRZETERMINOWANA,
            issue_date='2026-01-01',
            due_date='2026-02-01',
        )

        # 2 zadania otwarte (1 pilne)
        Task.objects.create(
            title='Zadanie pilne metryka',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(3), status=TaskStatus.NOWE,
            priority=TaskPriority.PILNA,
        )
        Task.objects.create(
            title='Zadanie normalne metryka',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(5), status=TaskStatus.W_TOKU,
        )

        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/pulpit/')

    @tag('smoke')
    def test_tc_d08_pasek_metryk_jest_widoczny(self):
        """TC-D08: Pasek metryk (.dash-metric-strip) jest widoczny na dashboardzie superusera."""
        strip = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-metric-strip')
        self.assertTrue(
            len(strip) > 0,
            'Brak elementu .dash-metric-strip na stronie superusera',
        )

    def test_tc_d09_widocznych_jest_piec_kart_metryk(self):
        """TC-D09: Widocznych jest dokładnie 5 kart metryk (.dash-metric-card)."""
        cards = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-metric-card')
        self.assertEqual(
            len(cards), 5,
            f'Oczekiwano 5 kart metryk (.dash-metric-card), znaleziono: {len(cards)}',
        )

    def test_tc_d10_metryka_aktywnych_spraw(self):
        """TC-D10: Karta 'Sprawy aktywne' wyświetla liczbę 2."""
        metric_values = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-metric-value')
        values = [el.text.strip() for el in metric_values]
        self.assertIn(
            '2', values,
            f'Liczba aktywnych spraw (2) nie widoczna w .dash-metric-value. Znaleziono: {values}',
        )

    def test_tc_d11_metryka_faktur_przeterminowanych(self):
        """TC-D11: Karta faktur wyświetla liczbę 1 (przeterminowana faktura)."""
        metric_values = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-metric-value')
        values = [el.text.strip() for el in metric_values]
        self.assertIn(
            '1', values,
            f'Liczba przeterminowanych faktur (1) nie widoczna w .dash-metric-value. Znaleziono: {values}',
        )

    def test_tc_d12_metryka_otwartych_zadan(self):
        """TC-D12: Karta zadań wyświetla liczbę 2 (otwarte zadania)."""
        metric_values = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-metric-value')
        values = [el.text.strip() for el in metric_values]
        self.assertIn(
            '2', values,
            f'Liczba otwartych zadań (2) nie widoczna w .dash-metric-value. Znaleziono: {values}',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-D13 – TC-D17: OPS Grid (tabele: sprawy, faktury, użytkownicy)
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserDashboardOpsGridTest(SzkpSeleniumTestCase):
    """Superuser Dashboard: OPS Grid — trzy panele z danymi operacyjnymi."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='admin_ops',
            password='adminpass123',
            is_staff=True,
            is_superuser=True,
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Ops', last_name='Klient', pesel='80010112346',
        )
        self.case = Case.objects.create(
            client=self.klient, case_number='TST/OPS/001',
            title='Sprawa ops grid', case_type=CaseType.CYWILNA,
        )
        self.invoice = Invoice.objects.create(
            case=self.case,
            invoice_number='FV/OPS/001',
            net_amount=Decimal('2000.00'),
            status=InvoiceStatus.WYSTAWIONA,
            issue_date='2026-05-01',
            due_date='2026-06-30',
        )

        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/pulpit/')

    @tag('smoke')
    def test_tc_d13_ops_grid_jest_widoczny(self):
        """TC-D13: Siatka OPS (.dash-ops-grid) jest widoczna na dashboardzie superusera."""
        grid = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-ops-grid')
        self.assertTrue(
            len(grid) > 0,
            'Brak elementu .dash-ops-grid na stronie superusera',
        )

    def test_tc_d14_numer_sprawy_widoczny_w_tabeli(self):
        """TC-D14: Numer 'TST/OPS/001' pojawia się w tabeli 'Ostatnie sprawy'."""
        self.assertIn(
            'TST/OPS/001',
            self.selenium.page_source,
            'Numer sprawy TST/OPS/001 nie pojawia się w panelu ostatnich spraw',
        )

    def test_tc_d15_numer_faktury_widoczny_w_tabeli(self):
        """TC-D15: Numer 'FV/OPS/001' pojawia się w tabeli 'Faktury'."""
        self.assertIn(
            'FV/OPS/001',
            self.selenium.page_source,
            'Numer faktury FV/OPS/001 nie pojawia się w panelu faktur',
        )

    def test_tc_d16_panel_uzytkownikow_wyswietla_wiersze(self):
        """TC-D16: Panel 'Użytkownicy systemu' zawiera wiersze użytkowników (.dash-user-row)."""
        user_rows = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-user-row')
        self.assertTrue(
            len(user_rows) > 0,
            'Brak wierszy .dash-user-row — panel Użytkownicy systemu nie jest renderowany',
        )

    def test_tc_d17_panel_uzytkownikow_zawiera_login_superusera(self):
        """TC-D17: Wiersze panelu użytkowników (.dash-user-row) zawierają login superusera."""
        user_rows = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-user-row')
        rows_text = ' '.join(el.text for el in user_rows)
        self.assertIn(
            'admin_ops',
            rows_text,
            'Login superusera (admin_ops) nie pojawia się w wierszach .dash-user-row',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-D18 – TC-D25: Wide Grid (feed, szybkie akcje, stan systemu, rozkład)
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SuperuserDashboardWideGridTest(SzkpSeleniumTestCase):
    """Superuser Dashboard: Wide Grid — feed aktywności, szybkie akcje, stan systemu, stat bars."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='admin_wide',
            password='adminpass123',
            is_staff=True,
            is_superuser=True,
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Wide', last_name='Klient', pesel='80010112347',
        )
        self.case = Case.objects.create(
            client=self.klient, case_number='TST/WD/001',
            title='Sprawa do feeda wide', case_type=CaseType.CYWILNA,
            status=CaseStatus.W_TOKU,
        )

        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/pulpit/')

    @tag('smoke')
    def test_tc_d18_wide_grid_jest_widoczny(self):
        """TC-D18: Siatka wide-grid (.dash-wide-grid) jest widoczna na dashboardzie superusera."""
        grid = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-wide-grid')
        self.assertTrue(
            len(grid) > 0,
            'Brak elementu .dash-wide-grid na stronie superusera',
        )

    def test_tc_d19_panel_feeda_jest_widoczny(self):
        """TC-D19: Panel dziennika aktywności (.dash-feed-list) jest widoczny."""
        feed = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-feed-list')
        self.assertTrue(
            len(feed) > 0,
            'Brak elementu .dash-feed-list — dziennik aktywności nie jest renderowany',
        )

    def test_tc_d20_feed_zawiera_co_najmniej_jeden_wpis(self):
        """TC-D20: Dziennik aktywności zawiera co najmniej jeden wpis (.dash-feed-item)."""
        items = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-feed-item')
        self.assertTrue(
            len(items) > 0,
            'Brak wpisów .dash-feed-item w dzienniku aktywności',
        )

    def test_tc_d21_feed_zawiera_numer_sprawy(self):
        """TC-D21: Wpisy feeda zawierają numer nowo dodanej sprawy ('TST/WD/001')."""
        items = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-feed-item')
        feed_text = ' '.join(el.text for el in items)
        self.assertIn(
            'TST/WD/001',
            feed_text,
            "Numer sprawy 'TST/WD/001' nie pojawia się we wpisach .dash-feed-item",
        )

    def test_tc_d22_panel_szybkich_akcji_jest_widoczny(self):
        """TC-D22: Panel szybkich akcji (.dash-quick-actions) jest widoczny."""
        qa = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-quick-actions')
        self.assertTrue(
            len(qa) > 0,
            'Brak elementu .dash-quick-actions — panel szybkich akcji nie jest renderowany',
        )

    def test_tc_d23_szybkie_akcje_zawieraja_link_admin(self):
        """TC-D23: Wśród kafelków szybkich akcji (.dash-quick-action) jest link do /admin/."""
        actions = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-quick-action')
        hrefs = [el.get_attribute('href') or '' for el in actions]
        self.assertTrue(
            any('/admin/' in href for href in hrefs),
            'Brak linku do /admin/ wśród kafelków .dash-quick-action',
        )

    def test_tc_d24_panel_stanu_systemu_jest_widoczny(self):
        """TC-D24: Panel stanu systemu (.dash-status-list) jest widoczny dla superusera."""
        status_list = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-status-list')
        self.assertTrue(
            len(status_list) > 0,
            'Brak elementu .dash-status-list — panel stanu systemu nie jest renderowany',
        )

    def test_tc_d25_panel_rozkladu_spraw_jest_widoczny(self):
        """TC-D25: Panel rozkładu spraw wg statusu (.dash-stat-bar-row) jest widoczny."""
        stat_bars = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-stat-bar-row')
        self.assertTrue(
            len(stat_bars) > 0,
            'Brak elementu .dash-stat-bar-row — panel rozkładu spraw nie jest renderowany',
        )
