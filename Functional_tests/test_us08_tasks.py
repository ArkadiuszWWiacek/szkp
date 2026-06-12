from datetime import timedelta

from django.contrib.auth.models import User
from django.test import tag
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
        kwargs.setdefault('due_date', self._za_7_dni())
        return Task.objects.create(
            title=title,
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            **kwargs,
        )

    # --- widok Moje zadania ---

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

    # --- filtry ---

    def test_input_filtr_sygnatury_widoczny_na_stronie(self):
        self.selenium.get(self._url_zadania())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input[name="case_number"]')
            )
        )

    def test_filtr_po_sygnaturze_ogranicza_liste(self):
        inne_sprawa = Case.objects.create(
            client=self.klient, case_number='TST-US08-999',
            title='Inna sprawa', case_type=CaseType.CYWILNA,
        )
        Task.objects.create(
            title='Zadanie pasującej sprawy',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            case=self.sprawa,
        )
        Task.objects.create(
            title='Zadanie innej sprawy',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            case=inne_sprawa,
        )
        self.selenium.get(self._url_zadania())
        input_el = WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="case_number"]'))
        )
        input_el.send_keys('TST-US08-001' + Keys.RETURN)
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('case_number=')
        )
        self.assertIn('Zadanie pasującej sprawy', self.selenium.page_source)
        self.assertNotIn('Zadanie innej sprawy', self.selenium.page_source)

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

    # --- filtrowanie po zalogowanym prawniku ---

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

    # --- tworzenie zadania ---

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

    # --- zmiana statusu ---

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

    # --- zadania przeterminowane ---

    def test_zadanie_przeterminowane_wyroznione_wizualnie(self):
        self._nowe_zadanie(title='Zadanie przeterminowane', due_date=self._wczoraj())
        self.selenium.get(self._url_zadania())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.szkp-task--overdue'))
        )

    # --- szybka zmiana statusu z listy ---

    def test_dropdown_statusu_widoczny_na_liscie(self):
        self._nowe_zadanie(title='Zadanie z dropdownem')
        self.selenium.get(self._url_zadania())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'select[name="status"]'))
        )

    def test_zmiana_statusu_przez_dropdown_na_liscie(self):
        zadanie = self._nowe_zadanie(title='Do zmiany statusu', status=TaskStatus.NOWE)
        self.selenium.get(self._url_zadania())
        select_el = WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'select[aria-label="Zmień status zadania"]')
            )
        )
        Select(select_el).select_by_value('w_toku')
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/zadania/')
        )
        zadanie.refresh_from_db()
        self.assertEqual(zadanie.status, TaskStatus.W_TOKU)

    def test_status_archiwalne_niedostepny_w_dropdown(self):
        self._nowe_zadanie(title='Zadanie bez archiwum')
        self.selenium.get(self._url_zadania())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'select[name="status"]'))
        )
        page = self.selenium.page_source
        self.assertNotIn('Archiwalne', page)
        self.assertNotIn('archiwalne', page)

    # --- usuwanie zadania ---

    def test_przycisk_usun_widoczny_przy_zadaniu(self):
        self._nowe_zadanie(title='Zadanie do usunięcia')
        self.selenium.get(self._url_zadania())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/usun/"]'))
        )

    def test_przycisk_usun_widoczny_przy_podzadaniu(self):
        parent = self._nowe_zadanie(title='Zadanie nadrzędne')
        Task.objects.create(
            title='Podzadanie do usunięcia',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=parent,
        )
        self.selenium.get(self._url_zadania())
        delete_links = WebDriverWait(self.selenium, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/usun/"]'))
        )
        self.assertGreaterEqual(len(delete_links), 2)

    def test_klik_usun_prowadzi_do_potwierdzenia(self):
        zadanie = self._nowe_zadanie(title='Zadanie do potwierdzenia')
        self.selenium.get(self._url_zadania())
        link = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="/usun/"]'))
        )
        link.click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/usun/')
        )
        self.assertIn('Zadanie do potwierdzenia', self.selenium.page_source)

    def test_potwierdzenie_usuwa_zadanie(self):
        zadanie = self._nowe_zadanie(title='Zadanie do skasowania')
        self.selenium.get(self.live_server_url + f'/szkp/zadania/{zadanie.pk}/usun/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn-szkp--danger'))
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--danger').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/zadania/')
        )
        self.assertNotIn('Zadanie do skasowania', self.selenium.page_source)

    def test_ostrzezenie_o_kaskadzie_gdy_ma_podzadania(self):
        parent = self._nowe_zadanie(title='Nadrzędne z podzadaniami')
        Task.objects.create(
            title='Podzadanie',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=parent,
        )
        self.selenium.get(self.live_server_url + f'/szkp/zadania/{parent.pk}/usun/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.szkp-page'))
        )
        self.assertIn('podzadań', self.selenium.page_source)

    # --- edycja podzadania ---

    def test_przycisk_edytuj_widoczny_przy_podzadaniu(self):
        parent = self._nowe_zadanie(title='Nadrzędne')
        sub = Task.objects.create(
            title='Podzadanie edytowalne',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=parent,
        )
        self.selenium.get(self._url_zadania())
        edit_links = WebDriverWait(self.selenium, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, f'a[href*="/zadania/{sub.pk}/edytuj/"]'))
        )
        self.assertTrue(len(edit_links) > 0)

    def test_edycja_podzadania_otwiera_formularz(self):
        parent = self._nowe_zadanie(title='Nadrzędne')
        sub = Task.objects.create(
            title='Podzadanie do edycji',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=parent,
        )
        self.selenium.get(self.live_server_url + f'/szkp/zadania/{sub.pk}/edytuj/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.assertIn('Podzadanie do edycji', self.selenium.find_element(By.NAME, 'title').get_attribute('value'))

    # --- dodawanie podzadania z formularza edycji ---

    def test_formularz_edycji_nadrzednego_zawiera_link_dodaj_podzadanie(self):
        zadanie = self._nowe_zadanie(title='Zadanie nadrzędne')
        self.selenium.get(self.live_server_url + f'/szkp/zadania/{zadanie.pk}/edytuj/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'a[href*="?parent={zadanie.pk}"]'))
        )

    def test_formularz_edycji_podzadania_bez_linku_dodaj_podzadanie(self):
        parent = self._nowe_zadanie(title='Nadrzędne')
        sub = Task.objects.create(
            title='Podzadanie',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=parent,
        )
        self.selenium.get(self.live_server_url + f'/szkp/zadania/{sub.pk}/edytuj/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.assertNotIn(f'?parent={sub.pk}', self.selenium.page_source)

    # --- dodawanie zadania z poziomu zakładki Zadania w szczegółach sprawy ---

    def _url_zadania_sprawy(self):
        return self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/?tab=zadania'

    def test_przycisk_dodaj_zadanie_na_stronie_sprawy_prowadzi_do_formularza(self):
        self.selenium.get(self._url_zadania_sprawy())
        self.selenium.find_element(By.CSS_SELECTOR, f'a[href*="/sprawy/{self.sprawa.pk}/zadania/nowe"]').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )

    def test_dodaj_zadanie_ze_sprawy_powiazuje_je_ze_sprawa(self):
        self.selenium.get(self._url_zadania_sprawy())
        self.selenium.find_element(By.CSS_SELECTOR, f'a[href*="/sprawy/{self.sprawa.pk}/zadania/nowe"]').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Zadanie ze sprawy')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=zadania')
        )
        zadanie = Task.objects.filter(title='Zadanie ze sprawy').first()
        self.assertIsNotNone(zadanie)
        self.assertEqual(zadanie.case, self.sprawa)

    def test_dodaj_podzadanie_przez_link_z_formularza(self):
        parent = self._nowe_zadanie(title='Zadanie z podzadaniem')
        self.selenium.get(self.live_server_url + f'/szkp/zadania/{parent.pk}/edytuj/')
        link = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'a[href*="?parent={parent.pk}"]'))
        )
        link.click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Nowe podzadanie')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/zadania/')
        )
        self.assertIn('Nowe podzadanie', self.selenium.page_source)

    # --- kliknięcie w zadanie → my_tasks z filtrem sygnatury ---

    def test_wiersz_zadania_na_sprawie_linkuje_do_my_tasks_z_filtrem_sygnatury(self):
        Task.objects.create(
            title='Zadanie klikalne',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            case=self.sprawa,
        )
        self.selenium.get(self._url_zadania_sprawy())
        link = WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f'a.szkp-task[href*="case_number={self.sprawa.case_number}"]')
            )
        )
        href = link.get_attribute('href')
        self.selenium.get(href)
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('case_number=')
        )
        self.assertIn('Moje zadania', self.selenium.page_source)
        self.assertIn(self.sprawa.case_number, self.selenium.current_url)

