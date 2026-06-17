"""
R-05 — Paginacja listy faktur.
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
from szkp.models import Case, CaseType, Client, ClientType, Invoice, InvoiceStatus, Lawyer


# ---------------------------------------------------------------------------
# Pomocnicze dane testowe
# ---------------------------------------------------------------------------

def _klient(last_name, pesel):
    return Client.objects.create(
        type=ClientType.OSOBA_FIZYCZNA,
        first_name='Jan', last_name=last_name, pesel=pesel,
    )


def _sprawa(klient, case_number):
    return Case.objects.create(
        client=klient, case_number=case_number,
        title=f'Sprawa {case_number}', case_type=CaseType.CYWILNA,
    )


def _faktury(sprawa, count, prefix='FV/R05/', status=InvoiceStatus.WYSTAWIONA):
    today = datetime.date.today()
    objs = []
    for i in range(1, count + 1):
        objs.append(Invoice(
            case=sprawa,
            invoice_number=f'{prefix}{i:03d}',
            issue_date=today,
            due_date=today + datetime.timedelta(days=14),
            net_amount=Decimal('100.00') * i,
            status=status,
        ))
    Invoice.objects.bulk_create(objs)


# ===========================================================================
# Paginacja listy faktur
# ===========================================================================

@tag('functional')
class InvoiceListPaginationTest(SzkpSeleniumTestCase):
    """R-05: paginacja listy faktur — 20 rekordów na stronę."""

    URL = '/szkp/faktury/'

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='teststaff_r05', password='testpass123', is_staff=True,
        )
        Lawyer.objects.create(
            user=self.user, first_name='Jan', last_name='Prawnik', bar_number='PL-R05',
        )
        klient = _klient('Paginacyjny', '89010112399')
        self.sprawa = _sprawa(klient, 'TST-R05-001')
        _faktury(self.sprawa, 25)
        self._zaloguj_przez_orm(self.user)

    def test_strona_1_pokazuje_maksymalnie_20_wierszy(self):
        """
        Przy 25 fakturach strona 1 zawiera dokładnie 20 wierszy <tbody>.
        """
        self.selenium.get(self.live_server_url + self.URL)
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr'))
        )
        rows = self.selenium.find_elements(By.CSS_SELECTOR, 'tbody tr')
        self.assertEqual(
            len(rows), 20,
            f'Oczekiwano 20 wierszy na stronie 1, znaleziono {len(rows)}. '
            'Brak paginacji — widok zwraca wszystkie rekordy.'
        )

    def test_element_paginacji_widoczny_gdy_wiecej_niz_20_faktur(self):
        """
        Element .szkp-pagination pojawia się gdy jest >20 faktur.
        """
        self.selenium.get(self.live_server_url + self.URL)
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr'))
        )
        pagination = self.selenium.find_elements(By.CSS_SELECTOR, '.szkp-pagination')
        self.assertGreater(
            len(pagination), 0,
            'Brak elementu .szkp-pagination mimo 25 faktur. '
            'Paginacja nie jest zaimplementowana.'
        )

    def test_info_paginacji_wyswietla_zakres_i_total(self):
        """
        Tekst .szkp-pagination__info zawiera informację "Pokazano 1–20 z 25".
        """
        self.selenium.get(self.live_server_url + self.URL)
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr'))
        )
        info = self.selenium.find_element(By.CSS_SELECTOR, '.szkp-pagination__info')
        tekst = info.text
        self.assertIn('20', tekst, f'Brak liczby 20 w tekście paginacji: "{tekst}"')
        self.assertIn('25', tekst, f'Brak liczby 25 (total) w tekście paginacji: "{tekst}"')

    def test_przycisk_nastepna_strona_istnieje(self):
        """
        Link "›" (następna strona) istnieje gdy jest >20 faktur.
        """
        self.selenium.get(self.live_server_url + self.URL)
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr'))
        )
        next_btns = self.selenium.find_elements(
            By.XPATH, '//a[contains(@class,"szkp-page-btn") and contains(text(),"›")]'
        )
        self.assertGreater(
            len(next_btns), 0,
            'Brak linku "›" (następna strona) mimo 25 faktur. '
            'Paginacja nie jest zaimplementowana.'
        )

    def test_klikniecie_nastepna_strona_przenosi_na_strone_2(self):
        """
        Kliknięcie "›" pokazuje faktury 21–25 i ukrywa faktury ze strony 1.
        """
        self.selenium.get(self.live_server_url + self.URL)
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr'))
        )
        # Zapamiętaj numer faktury widocznej na stronie 1
        first_row_text = self.selenium.find_elements(
            By.CSS_SELECTOR, 'tbody tr'
        )[0].text

        next_btn = self.selenium.find_element(
            By.XPATH, '//a[contains(@class,"szkp-page-btn") and contains(text(),"›")]'
        )
        self.selenium.execute_script('arguments[0].click();', next_btn)
        WebDriverWait(self.selenium, 5).until(EC.url_contains('page=2'))

        rows_page2 = self.selenium.find_elements(By.CSS_SELECTOR, 'tbody tr')
        self.assertGreater(len(rows_page2), 0, 'Strona 2 jest pusta.')
        self.assertLessEqual(len(rows_page2), 5,
                             f'Strona 2 powinna mieć 5 wierszy (rekordy 21–25), '
                             f'znaleziono {len(rows_page2)}')
        page2_text = self.selenium.page_source
        self.assertNotIn(
            first_row_text.split()[0], page2_text,
            'Faktura ze strony 1 pojawia się na stronie 2 — paginacja nie działa.'
        )

    def test_link_nastepna_strona_zachowuje_filtr_statusu(self):
        """
        Link "›" w URL zawiera parametr status gdy aktywny jest filtr statusu.
        """
        self.selenium.get(
            self.live_server_url + self.URL + '?status=wystawiona'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr'))
        )
        next_btn = self.selenium.find_element(
            By.XPATH, '//a[contains(@class,"szkp-page-btn") and contains(text(),"›")]'
        )
        href = next_btn.get_attribute('href')
        self.assertIn(
            'status=wystawiona', href,
            f'Link "›" nie zachowuje parametru status=wystawiona. href={href}'
        )

    def test_link_nastepna_strona_zachowuje_parametr_q(self):
        """
        Link "›" zachowuje parametr q (wyszukiwanie) w URL.
        """
        self.selenium.get(
            self.live_server_url + self.URL + '?q=FV%2FR05%2F'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr'))
        )
        next_btn = self.selenium.find_element(
            By.XPATH, '//a[contains(@class,"szkp-page-btn") and contains(text(),"›")]'
        )
        href = next_btn.get_attribute('href')
        self.assertIn(
            'q=', href,
            f'Link "›" nie zachowuje parametru q. href={href}'
        )

    def test_link_nastepna_strona_zachowuje_sort_i_dir(self):
        """
        Link "›" zachowuje parametry sort i dir w URL.
        """
        self.selenium.get(
            self.live_server_url + self.URL + '?sort=invoice_number&dir=desc'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody tr'))
        )
        next_btn = self.selenium.find_element(
            By.XPATH, '//a[contains(@class,"szkp-page-btn") and contains(text(),"›")]'
        )
        href = next_btn.get_attribute('href')
        self.assertIn(
            'sort=invoice_number', href,
            f'Link "›" nie zachowuje parametru sort. href={href}'
        )
        self.assertIn(
            'dir=desc', href,
            f'Link "›" nie zachowuje parametru dir. href={href}'
        )
