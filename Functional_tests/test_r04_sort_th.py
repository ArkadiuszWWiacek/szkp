"""
R-04 — Custom template tag `sort_th` dla sortowalnych nagłówków tabeli.
Testy funkcjonalne (Selenium).
"""
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Functional_tests.base import SzkpSeleniumTestCase
from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseType,
    Client, ClientType,
    Invoice, InvoiceStatus,
    Lawyer,
)


# ---------------------------------------------------------------------------
# Pomocnicze dane testowe
# ---------------------------------------------------------------------------

def _klient(last_name, pesel, first_name='Jan'):
    return Client.objects.create(
        type=ClientType.OSOBA_FIZYCZNA,
        first_name=first_name, last_name=last_name, pesel=pesel,
    )


def _sprawa(klient, case_number, case_type=CaseType.CYWILNA):
    return Case.objects.create(
        client=klient, case_number=case_number,
        title=f'Sprawa {case_number}', case_type=case_type,
    )


def _faktura(sprawa, number, days_offset=0):
    today = datetime.date.today()
    return Invoice.objects.create(
        case=sprawa,
        invoice_number=number,
        issue_date=today,
        due_date=today + datetime.timedelta(days=14 + days_offset),
        net_amount=Decimal('1000.00'),
        vat_rate=Decimal('0.23'),
        status=InvoiceStatus.WYSTAWIONA,
    )


# ===========================================================================
# Tabela spraw (case_list)
# ===========================================================================

@tag('functional')
class SortThCaseListTest(SzkpSeleniumTestCase):
    """Sortowalne nagłówki tabeli spraw z tagiem sort_th."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='teststaff_cases', password='testpass123', is_staff=True,
        )
        k1 = _klient('Alfa', '89010112341')
        k2 = _klient('Zeta', '89010112342')
        _sprawa(k1, 'TST-R04-A001', CaseType.CYWILNA)
        _sprawa(k2, 'TST-R04-Z001', CaseType.KARNA)
        self._zaloguj_przez_orm(self.user)

    def test_aktywna_kolumna_case_number_ma_klase_sort_active(self):
        """Nagłówek <th> kolumny 'case_number' ma klasę szkp-sort-active gdy posortowana."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/?sort=case_number&dir=asc')
        active_ths = self.selenium.find_elements(By.CSS_SELECTOR, 'th.szkp-sort-active')
        self.assertEqual(len(active_ths), 1,
                         'Oczekiwano dokładnie jednego <th> z klasą szkp-sort-active')

    def test_ikona_asc_ma_klase_sort_icon_asc(self):
        """Ikona na aktywnej kolumnie sortowanej ASC ma klasę szkp-sort-icon--asc."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/?sort=case_number&dir=asc')
        icon = self.selenium.find_element(
            By.CSS_SELECTOR, '.szkp-sort-active .szkp-sort-icon--asc'
        )
        self.assertIsNotNone(icon)

    def test_ikona_desc_ma_klase_sort_icon_desc(self):
        """Ikona na aktywnej kolumnie sortowanej DESC ma klasę szkp-sort-icon--desc."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/?sort=case_number&dir=desc')
        icon = self.selenium.find_element(
            By.CSS_SELECTOR, '.szkp-sort-active .szkp-sort-icon--desc'
        )
        self.assertIsNotNone(icon)

    def test_link_aktywnej_kolumny_asc_wskazuje_na_desc(self):
        """Link aktywnej kolumny ASC wskazuje na dir=desc (przełącza kierunek)."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/?sort=case_number&dir=asc')
        link = self.selenium.find_element(By.CSS_SELECTOR, 'th.szkp-sort-active a')
        href = link.get_attribute('href')
        self.assertIn('dir=desc', href)

    def test_link_aktywnej_kolumny_desc_wskazuje_na_asc(self):
        """Link aktywnej kolumny DESC wskazuje na dir=asc (przełącza kierunek)."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/?sort=case_number&dir=desc')
        link = self.selenium.find_element(By.CSS_SELECTOR, 'th.szkp-sort-active a')
        href = link.get_attribute('href')
        self.assertIn('dir=asc', href)

    def test_sort_link_zachowuje_nieznane_parametry_get(self):
        """Tag sort_th dynamicznie zachowuje WSZYSTKIE params z request.GET."""
        self.selenium.get(
            self.live_server_url
            + '/szkp/sprawy/?q=&status=&type=&extra_param=testval'
        )
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        hrefs = [el.get_attribute('href') for el in links]
        self.assertTrue(
            any('extra_param=testval' in h for h in hrefs),
            'Żaden link sortowania nie zachowuje extra_param=testval. '
            'Tag sort_th musi dynamicznie czytać request.GET.'
        )

    def test_link_na_kolumnie_case_number_sortuje_po_case_number(self):
        """Kliknięcie nagłówka Sygnatura przechodzi do URL z sort=case_number."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/?sort=client&dir=asc')
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        link = next(
            (l for l in links if 'sort=case_number' in l.get_attribute('href')),
            None,
        )
        self.assertIsNotNone(link, 'Brak linku sort=case_number w nagłówkach')
        link.click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('sort=case_number'))
        self.assertIn('sort=case_number', self.selenium.current_url)

    def test_kolumna_prawnicy_nie_jest_sortowalna(self):
        """Kolumna 'Prawnicy' nie ma linku <a> — nie jest obsługiwana przez sort_th."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/')
        headers = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th')
        prawnicy_th = next((h for h in headers if 'Prawnicy' in h.text), None)
        self.assertIsNotNone(prawnicy_th, "Brak kolumny 'Prawnicy' w nagłówku tabeli")
        links_in_th = prawnicy_th.find_elements(By.TAG_NAME, 'a')
        self.assertEqual(len(links_in_th), 0,
                         "Kolumna 'Prawnicy' nie powinna być sortowalna (brak <a>)")

    def test_sort_link_zachowuje_q_i_status(self):
        """Link sortowania w case_list zachowuje parametry q i status."""
        self.selenium.get(
            self.live_server_url + '/szkp/sprawy/?q=alfa&status=nowa&sort=client&dir=asc'
        )
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        link = next(
            (l for l in links if 'sort=case_number' in l.get_attribute('href')),
            None,
        )
        self.assertIsNotNone(link)
        href = link.get_attribute('href')
        self.assertIn('q=alfa', href)
        self.assertIn('status=nowa', href)

    def test_sort_link_nie_zawiera_parametru_page(self):
        """Link sortowania nie propaguje parametru page — kliknięcie wraca do strony 1."""
        self.selenium.get(
            self.live_server_url + '/szkp/sprawy/?sort=case_number&dir=asc&page=2'
        )
        link = self.selenium.find_element(By.CSS_SELECTOR, 'th.szkp-sort-active a')
        href = link.get_attribute('href')
        self.assertNotIn('page=', href)


# ===========================================================================
# Tabela klientów (client_list)
# ===========================================================================

@tag('functional')
class SortThClientListTest(SzkpSeleniumTestCase):
    """Sortowalne nagłówki tabeli klientów z tagiem sort_th."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='teststaff_clients', password='testpass123', is_staff=True,
        )
        _klient('Alfa', '89010112343', 'Anna')
        _klient('Zeta', '89010112344', 'Zygmunt')
        self._zaloguj_przez_orm(self.user)

    def test_aktywna_kolumna_last_name_ma_klase_sort_active(self):
        """Kolumna 'last_name' ma klasę szkp-sort-active gdy posortowana."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/?sort=last_name&dir=asc')
        active_ths = self.selenium.find_elements(By.CSS_SELECTOR, 'th.szkp-sort-active')
        self.assertEqual(len(active_ths), 1)

    def test_klikniecie_naglowka_typ_sortuje_po_type(self):
        """Kliknięcie nagłówka 'Typ' przechodzi do URL z sort=type."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/')
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        link = next(
            (l for l in links if 'sort=type' in l.get_attribute('href')),
            None,
        )
        self.assertIsNotNone(link, 'Brak linku sort=type w nagłówkach tabeli klientów')
        link.click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('sort=type'))
        self.assertIn('sort=type', self.selenium.current_url)

    def test_sort_link_zachowuje_nieznane_parametry_get(self):
        """Tag sort_th dynamicznie zachowuje WSZYSTKIE params z request.GET."""
        self.selenium.get(
            self.live_server_url + '/szkp/klienci/?q=&extra_param=abc'
        )
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        hrefs = [el.get_attribute('href') for el in links]
        self.assertTrue(
            any('extra_param=abc' in h for h in hrefs),
            'Żaden link sortowania w tabeli klientów nie zachowuje extra_param=abc. '
            'Tag sort_th musi dynamicznie czytać request.GET.'
        )

    def test_kolumna_pesel_nip_nie_jest_sortowalna(self):
        """Kolumna 'PESEL / NIP' nie ma linku sortowania."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/')
        headers = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th')
        pesel_th = next((h for h in headers if 'PESEL' in h.text), None)
        self.assertIsNotNone(pesel_th, "Brak kolumny 'PESEL / NIP'")
        links = pesel_th.find_elements(By.TAG_NAME, 'a')
        self.assertEqual(len(links), 0, "Kolumna PESEL/NIP nie powinna być sortowalna")

    def test_ikona_asc_na_aktywnej_kolumnie_klientow(self):
        """Ikona ASC pojawia się na aktywnej kolumnie klientów."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/?sort=last_name&dir=asc')
        icon = self.selenium.find_element(
            By.CSS_SELECTOR, '.szkp-sort-active .szkp-sort-icon--asc'
        )
        self.assertIsNotNone(icon)

    def test_sort_link_klientow_zachowuje_q(self):
        """Sort link w client_list zachowuje parametr q wyszukiwania."""
        self.selenium.get(
            self.live_server_url + '/szkp/klienci/?q=alfa&sort=created_at&dir=asc'
        )
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        link = next(
            (l for l in links if 'sort=last_name' in l.get_attribute('href')),
            None,
        )
        self.assertIsNotNone(link)
        href = link.get_attribute('href')
        self.assertIn('q=alfa', href)


# ===========================================================================
# Tabela faktur (invoice_list)
# ===========================================================================

@tag('functional')
class SortThInvoiceListTest(SzkpSeleniumTestCase):
    """Sortowalne nagłówki tabeli faktur z tagiem sort_th."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='teststaff_invoices', password='testpass123', is_staff=True,
        )
        k = _klient('Testowy', '89010112345')
        s = _sprawa(k, 'TST-R04-F001')
        _faktura(s, 'FV/2025/001', days_offset=0)
        _faktura(s, 'FV/2025/002', days_offset=5)
        self._zaloguj_przez_orm(self.user)

    def test_aktywna_kolumna_invoice_number_ma_klase_sort_active(self):
        """Kolumna 'invoice_number' ma klasę szkp-sort-active gdy posortowana."""
        self.selenium.get(
            self.live_server_url + '/szkp/faktury/?sort=invoice_number&dir=asc'
        )
        active_ths = self.selenium.find_elements(By.CSS_SELECTOR, 'th.szkp-sort-active')
        self.assertEqual(len(active_ths), 1)

    def test_klikniecie_naglowka_gross_amount_sortuje_po_kwocie(self):
        """Kliknięcie nagłówka 'Kwota brutto' przechodzi do URL z sort=gross_amount."""
        self.selenium.get(self.live_server_url + '/szkp/faktury/')
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        link = next(
            (l for l in links if 'sort=gross_amount' in l.get_attribute('href')),
            None,
        )
        self.assertIsNotNone(link, 'Brak linku sort=gross_amount w nagłówkach faktury')
        link.click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('sort=gross_amount'))
        self.assertIn('sort=gross_amount', self.selenium.current_url)

    def test_ikona_desc_na_aktywnej_kolumnie_faktur(self):
        """Ikona DESC pojawia się na aktywnej kolumnie faktur."""
        self.selenium.get(
            self.live_server_url + '/szkp/faktury/?sort=due_date&dir=desc'
        )
        icon = self.selenium.find_element(
            By.CSS_SELECTOR, '.szkp-sort-active .szkp-sort-icon--desc'
        )
        self.assertIsNotNone(icon)

    def test_sort_link_zachowuje_nieznane_parametry_get(self):
        """Tag sort_th dynamicznie zachowuje WSZYSTKIE params z request.GET."""
        self.selenium.get(
            self.live_server_url + '/szkp/faktury/?status=&extra_param=xyz'
        )
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        hrefs = [el.get_attribute('href') for el in links]
        self.assertTrue(
            any('extra_param=xyz' in h for h in hrefs),
            'Żaden link sortowania w tabeli faktur nie zachowuje extra_param=xyz. '
            'Tag sort_th musi dynamicznie czytać request.GET.'
        )

    def test_sort_link_faktur_zachowuje_status_i_q(self):
        """Sort link w invoice_list zachowuje parametry status i q."""
        self.selenium.get(
            self.live_server_url
            + '/szkp/faktury/?status=wystawiona&q=FV&sort=due_date&dir=asc'
        )
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        link = next(
            (l for l in links if 'sort=invoice_number' in l.get_attribute('href')),
            None,
        )
        self.assertIsNotNone(link, 'Brak linku sort=invoice_number w nagłówkach faktury')
        href = link.get_attribute('href')
        self.assertIn('status=wystawiona', href)
        self.assertIn('q=FV', href)

    def test_szesc_kolumn_sortowalnych_w_fakturach(self):
        """Tabela faktur ma dokładnie 6 sortowalnych nagłówków (kolumna akcji nie jest)."""
        self.selenium.get(self.live_server_url + '/szkp/faktury/')
        sort_links = [
            'sort=invoice_number', 'sort=case', 'sort=issue_date',
            'sort=due_date', 'sort=gross_amount', 'sort=status',
        ]
        links = self.selenium.find_elements(By.CSS_SELECTOR, 'thead th a')
        hrefs = [l.get_attribute('href') for l in links]
        for expected_sort in sort_links:
            self.assertTrue(
                any(expected_sort in h for h in hrefs),
                f'Brak linku sortowania dla {expected_sort} w tabeli faktur'
            )
