from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base import SzkpSeleniumTestCase
from szkp.models import Case, CaseType, Client, ClientType


@tag('functional')
class US04ClientsTest(SzkpSeleniumTestCase):
    """US-04: Klienci — dodawanie, edycja, wyszukiwanie, usuwanie."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='testpracownik', password='testpass123',
        )
        self._zaloguj_przez_orm(self.user)

# ===========================================================================
# lista
# ===========================================================================

    @tag('smoke')
    def test_lista_klientow_wyswietla_sie(self):
        """Lista klientów jest dostępna po zalogowaniu."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/')
        self.assertIn('Klienci', self.selenium.page_source)

    def test_wyszukiwanie_po_nazwisku(self):
        """Wyszukiwanie po nazwisku zwraca pasującego klienta."""
        Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Jan', last_name='Szukany', pesel='89010112345',
        )
        self.selenium.get(self.live_server_url + '/szkp/klienci/?q=Szukany')
        self.assertIn('Szukany', self.selenium.page_source)

    def test_wyszukiwanie_po_nazwie_firmy(self):
        """Wyszukiwanie po nazwie firmy zwraca pasującego klienta."""
        Client.objects.create(
            type=ClientType.FIRMA,
            company_name='FirmaXYZ Sp. z o.o.', nip='5250012345',
        )
        self.selenium.get(self.live_server_url + '/szkp/klienci/?q=FirmaXYZ')
        self.assertIn('FirmaXYZ', self.selenium.page_source)

    def test_wyszukiwanie_po_pesel(self):
        """Wyszukiwanie po PESEL zwraca pasującą osobę fizyczną."""
        Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Piotr', last_name='Peseltowski', pesel='92051412345',
        )
        self.selenium.get(self.live_server_url + '/szkp/klienci/?q=92051412345')
        self.assertIn('Peseltowski', self.selenium.page_source)

    def test_wyszukiwanie_po_nip(self):
        """Wyszukiwanie po NIP zwraca pasującą firmę."""
        Client.objects.create(
            type=ClientType.FIRMA,
            company_name='NIP-Test Sp. z o.o.', nip='5250012346',
        )
        self.selenium.get(self.live_server_url + '/szkp/klienci/?q=5250012346')
        self.assertIn('NIP-Test', self.selenium.page_source)

    def test_wyszukiwanie_bez_wynikow(self):
        """Wyszukiwanie bez dopasowań wyświetla stan pusty, nie błąd."""
        self.selenium.get(
            self.live_server_url + '/szkp/klienci/?q=NieistniejecaNazwa9999'
        )
        self.assertNotIn('Traceback', self.selenium.page_source)
        self.assertNotIn('NieistniejecaNazwa9999</td>', self.selenium.page_source)

# ===========================================================================
# formularz: osoba
# ===========================================================================

    @tag('smoke')
    def test_dodaj_klienta_osobafizyczna(self):
        """Wypełnienie formularza osoby fizycznej tworzy klienta."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/nowy/')
        self.selenium.find_element(By.ID, 'id_first_name').send_keys('Jan')
        self.selenium.find_element(By.ID, 'id_last_name').send_keys('Kowalski')
        self.selenium.find_element(By.ID, 'id_pesel').send_keys('89010112345')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        self.assertIn('Kowalski', self.selenium.page_source)

    def test_walidacja_wymaga_pesel(self):
        """Formularz osoby fizycznej bez PESEL wyświetla błąd walidacji."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/nowy/')
        self.selenium.find_element(By.ID, 'id_first_name').send_keys('Jan')
        self.selenium.find_element(By.ID, 'id_last_name').send_keys('Kowalski')
        # PESEL celowo puste
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        src = self.selenium.page_source
        self.assertIn('PESEL', src)
        self.assertIn('nowy', self.selenium.current_url)

# ===========================================================================
# formularz: firma
# ===========================================================================

    def test_dodaj_klienta_firma(self):
        """Wypełnienie formularza firmy tworzy klienta."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/nowy/')
        self.selenium.find_element(
            By.CSS_SELECTOR, 'input[name="type"][value="firma"]'
        ).click()
        WebDriverWait(self.selenium, 3).until(
            EC.visibility_of_element_located((By.ID, 'id_company_name'))
        )
        self.selenium.find_element(By.ID, 'id_company_name').send_keys(
            'ACME Sp. z o.o.'
        )
        self.selenium.find_element(By.ID, 'id_nip').send_keys('5250012345')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        self.assertIn('ACME', self.selenium.page_source)

    def test_walidacja_wymaga_nip(self):
        """Formularz firmy bez NIP wyświetla błąd walidacji."""
        self.selenium.get(self.live_server_url + '/szkp/klienci/nowy/')
        self.selenium.find_element(
            By.CSS_SELECTOR, 'input[name="type"][value="firma"]'
        ).click()
        WebDriverWait(self.selenium, 3).until(
            EC.visibility_of_element_located((By.ID, 'id_company_name'))
        )
        self.selenium.find_element(By.ID, 'id_company_name').send_keys(
            'Firma Bez NIP'
        )
        # NIP celowo puste
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        src = self.selenium.page_source
        self.assertIn('NIP', src)
        self.assertIn('nowy', self.selenium.current_url)

# ===========================================================================
# edycja
# ===========================================================================

    def test_edycja_klienta_osobafizycznej(self):
        """Edycja klienta zapisuje zmiany i wyświetla je na liście."""
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Przed', last_name='Edycja', pesel='89010112345',
        )
        self.selenium.get(
            self.live_server_url + f'/szkp/klienci/{klient.pk}/edytuj/'
        )
        pole = self.selenium.find_element(By.ID, 'id_last_name')
        pole.clear()
        pole.send_keys('Zmieniony')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        self.assertIn('Zmieniony', self.selenium.page_source)

# ===========================================================================
# usuwanie
# ===========================================================================

    def test_usuniecie_klienta_bez_spraw(self):
        """Klient bez przypisanych spraw może być usunięty."""
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Do', last_name='Usuniecia', pesel='89010112345',
        )
        delete_url = self.live_server_url + f'/szkp/klienci/{klient.pk}/usun/'
        self.selenium.get(delete_url)
        try:
            self.selenium.find_element(
                By.CSS_SELECTOR, 'button.btn-szkp--danger'
            ).click()
        except Exception:
            self.fail('Brak przycisku potwierdzenia usunięcia — widok client_delete nie istnieje.')
        self.selenium.get(self.live_server_url + '/szkp/klienci/')
        self.assertNotIn('Usuniecia', self.selenium.page_source)

    def test_usuniecie_zablokowane_gdy_ma_sprawy(self):
        """Próba usunięcia klienta z przypisaną sprawą wyświetla błąd."""
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Powiazany', last_name='ZeSprawa', pesel='89010112345',
        )
        Case.objects.create(
            client=klient, case_number='TST-US04-001',
            title='Sprawa blokująca', case_type=CaseType.CYWILNA,
        )
        delete_url = self.live_server_url + f'/szkp/klienci/{klient.pk}/usun/'
        self.selenium.get(delete_url)
        try:
            self.selenium.find_element(
                By.CSS_SELECTOR, 'button.btn-szkp--danger'
            ).click()
        except Exception:
            self.fail('Brak przycisku potwierdzenia usunięcia — widok client_delete nie istnieje.')
        src = self.selenium.page_source
        # błąd wyświetlony, klient nadal istnieje
        self.assertIn('ZeSprawa', src)
