from datetime import timedelta

from django.contrib.auth.models import User
from django.test import tag
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from szkp.models import (
    Case, CaseType, Client, ClientType, Lawyer, Task, TaskPriority, TaskStatus,
)

from Functional_tests.base import SzkpSeleniumTestCase


@tag('functional')
class US08TasksTest(SzkpSeleniumTestCase):

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='testprawnik', password='testpass123', is_staff=True,
        )
        self.lawyer = Lawyer.objects.create(
            user=self.user, first_name='Jan', last_name='Prawnik',
            bar_number='PL008',
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Maria', last_name='Zadaniowa', pesel='90020212345',
        )
        self.sprawa = Case.objects.create(
            client=self.klient, case_number='TST-US08-001',
            title='Sprawa do testów zadań', case_type=CaseType.CYWILNA,
        )
        self._zaloguj_przez_orm(self.user)

    def _url_zadania(self):
        return self.live_server_url + '/szkp/zadania/'

    def _za_7_dni(self):
        return timezone.now() + timedelta(days=7)

    def _wczoraj(self):
        return timezone.now() - timedelta(days=1)

    def _dzisiaj(self):
        return timezone.now()

    def _nowe_zadanie(self, title='Zadanie testowe', **kwargs):
        return Task.objects.create(
            title=title,
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            due_date=self._za_7_dni(),
            **kwargs,
        )

    # --- widok Moje zadania (GREEN) ---

    def test_strona_moje_zadania_jest_dostepna(self):
        self.selenium.get(self._url_zadania())
        self.assertIn('Moje zadania', self.selenium.page_source)

    def test_brak_zadan_wyswietla_pusty_stan(self):
        self.selenium.get(self._url_zadania())
        self.assertIn('Brak zadań', self.selenium.page_source)

    def test_zadanie_widoczne_na_liscie(self):
        self._nowe_zadanie(title='Sprawdzenie dokumentów')
        self.selenium.get(self._url_zadania())
        self.assertIn('Sprawdzenie dokumentów', self.selenium.page_source)

    def test_zadanie_bez_sprawy_widoczne(self):
        Task.objects.create(
            title='Zadanie bez sprawy',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
        )
        self.selenium.get(self._url_zadania())
        self.assertIn('Zadanie bez sprawy', self.selenium.page_source)

    def test_podzadanie_widoczne_pod_zadaniem_nadrzednym(self):
        parent = self._nowe_zadanie(title='Zadanie nadrzędne')
        Task.objects.create(
            title='Podzadanie pierwsze',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=parent,
        )
        self.selenium.get(self._url_zadania())
        self.assertIn('Zadanie nadrzędne', self.selenium.page_source)
        self.assertIn('Podzadanie pierwsze', self.selenium.page_source)

    # --- filtry (GREEN) ---

    def test_filtr_statusu_ogranicza_liste(self):
        self._nowe_zadanie(title='Zadanie nowe', status=TaskStatus.NOWE)
        self._nowe_zadanie(title='Zadanie zakończone', status=TaskStatus.ZAKOŃCZONE)
        self.selenium.get(self._url_zadania() + '?status=nowe')
        self.assertIn('Zadanie nowe', self.selenium.page_source)
        self.assertNotIn('Zadanie zakończone', self.selenium.page_source)

    def test_filtr_dzis_pokazuje_zadania_na_dzis(self):
        self._nowe_zadanie(title='Na dziś', due_date=self._dzisiaj())
        self._nowe_zadanie(title='Za tydzień', due_date=self._za_7_dni())
        self.selenium.get(self._url_zadania() + '?period=today')
        self.assertIn('Na dziś', self.selenium.page_source)
        self.assertNotIn('Za tydzień', self.selenium.page_source)

    def test_wyczysc_filtry_usuwa_parametry_url(self):
        self._nowe_zadanie()
        self.selenium.get(self._url_zadania() + '?status=nowe')
        self.selenium.find_element(By.CSS_SELECTOR, 'a.text-muted-szkp').click()
        WebDriverWait(self.selenium, 5).until(
            lambda d: 'status=' not in d.current_url
        )
        self.assertNotIn('status=', self.selenium.current_url)

    # --- filtrowanie po zalogowanym prawniku (RED — brak filtra) ---

    def test_zadania_innego_prawnika_nie_sa_widoczne(self):
        inny_user = User.objects.create_user(
            username='innyprawnik', password='testpass123',
        )
        inny_prawnik = Lawyer.objects.create(
            user=inny_user, first_name='Inna', last_name='Osoba',
            bar_number='PL999',
        )
        Task.objects.create(
            title='Zadanie innego prawnika',
            assigned_lawyer=inny_prawnik,
            created_by=inny_prawnik,
        )
        self.selenium.get(self._url_zadania())
        self.assertNotIn('Zadanie innego prawnika', self.selenium.page_source)

    # --- tworzenie zadania (RED — brak widoku) ---

    def test_link_nowe_zadanie_przenosi_do_formularza(self):
        self.selenium.get(self._url_zadania())
        self.selenium.find_element(By.CSS_SELECTOR, 'a[href*="zadania/nowe"]').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )

    def test_dodaj_zadanie_z_poprawnymi_danymi(self):
        self.selenium.get(self.live_server_url + '/szkp/zadania/nowe/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Nowe zadanie formularz')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/zadania/')
        )
        self.assertIn('Nowe zadanie formularz', self.selenium.page_source)

    def test_nowe_zadanie_ma_domyslny_status_nowe(self):
        self.selenium.get(self.live_server_url + '/szkp/zadania/nowe/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Zadanie statusowe')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/zadania/')
        )
        self.assertIn('Nowe', self.selenium.page_source)

    def test_priorytet_wybierany_z_listy(self):
        self.selenium.get(self.live_server_url + '/szkp/zadania/nowe/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'priority'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Zadanie pilne')
        Select(self.selenium.find_element(By.NAME, 'priority')).select_by_value('pilna')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/zadania/')
        )
        self.assertIn('Pilna', self.selenium.page_source)

    # --- zmiana statusu (RED — brak widoku edycji) ---

    def test_zmiana_statusu_zadania_na_zakonczone(self):
        zadanie = self._nowe_zadanie(title='Do zakończenia')
        self.selenium.get(
            self.live_server_url + f'/szkp/zadania/{zadanie.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'status'))
        )
        Select(self.selenium.find_element(By.NAME, 'status')).select_by_value('zakończone')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/zadania/')
        )
        self.assertIn('Zakończone', self.selenium.page_source)

    def test_zakonczenie_zadania_ustawia_completed_at(self):
        zadanie = self._nowe_zadanie(title='Zadanie do zamknięcia')
        self.selenium.get(
            self.live_server_url + f'/szkp/zadania/{zadanie.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'status'))
        )
        Select(self.selenium.find_element(By.NAME, 'status')).select_by_value('zakończone')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/zadania/')
        )
        zadanie.refresh_from_db()
        self.assertIsNotNone(zadanie.completed_at)

    # --- zadania przeterminowane (RED — brak CSS) ---

    def test_zadanie_przeterminowane_wyroznione_wizualnie(self):
        self._nowe_zadanie(title='Zadanie przeterminowane', due_date=self._wczoraj())
        self.selenium.get(self._url_zadania())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.szkp-task--overdue'))
        )
