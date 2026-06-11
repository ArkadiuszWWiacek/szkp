from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from szkp.models import Case, CaseStatus, CaseType, CaseLawyer, CaseLawyerRole, Client, ClientType, Lawyer

from Functional_tests.base import SzkpSeleniumTestCase


@tag('functional')
class US05CasesTest(SzkpSeleniumTestCase):

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='testprawnik', password='testpass123', is_staff=True,
        )
        self.lawyer = Lawyer.objects.create(
            user=self.user, first_name='Jan', last_name='Prawnik',
            bar_number='PL001',
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Anna', last_name='Klientka', pesel='89010112345',
        )
        self._zaloguj_przez_orm(self.user)

    # --- lista i wyszukiwanie (GREEN) ---

    def test_lista_spraw_wyswietla_sie(self):
        self.selenium.get(self.live_server_url + '/szkp/sprawy/')
        self.assertIn('Sprawy', self.selenium.page_source)

    def test_wyszukiwanie_po_numerze_sprawy(self):
        Case.objects.create(
            client=self.klient, case_number='TST-SZUKAJ-001',
            title='Szukana sprawa', case_type=CaseType.CYWILNA,
        )
        self.selenium.get(self.live_server_url + '/szkp/sprawy/?q=TST-SZUKAJ-001')
        self.assertIn('TST-SZUKAJ-001', self.selenium.page_source)

    def test_filtrowanie_po_statusie(self):
        Case.objects.create(
            client=self.klient, case_number='TST-NOWA-001',
            title='Sprawa nowa', case_type=CaseType.CYWILNA,
            status=CaseStatus.NOWA,
        )
        Case.objects.create(
            client=self.klient, case_number='TST-ZAKONCZONA-001',
            title='Sprawa zakończona', case_type=CaseType.KARNA,
            status=CaseStatus.ZAKOŃCZONA,
        )
        self.selenium.get(self.live_server_url + '/szkp/sprawy/?status=nowa')
        src = self.selenium.page_source
        self.assertIn('TST-NOWA-001', src)
        self.assertNotIn('TST-ZAKONCZONA-001', src)

    # --- zmiana statusu przez case_detail (GREEN) ---

    def test_zmiana_statusu_na_zakonczona(self):
        sprawa = Case.objects.create(
            client=self.klient, case_number='TST-STATUS-001',
            title='Sprawa do zamknięcia', case_type=CaseType.CYWILNA,
            status=CaseStatus.NOWA,
        )
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{sprawa.pk}/')
        select = Select(self.selenium.find_element(By.NAME, 'status'))
        select.select_by_value('zakończona')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains(f'/szkp/sprawy/{sprawa.pk}/')
        )
        self.assertIn('Zakończona', self.selenium.page_source)

    # --- tworzenie (RED — brak widoku case_form) ---

    def test_dodaj_sprawe(self):
        self.selenium.get(self.live_server_url + '/szkp/sprawy/')
        self.selenium.find_element(By.CSS_SELECTOR, 'a[href*="nowy"]').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'case_number'))
        )
        self.selenium.find_element(By.NAME, 'case_number').send_keys('TST-NOWA-999')
        self.selenium.find_element(By.NAME, 'title').send_keys('Sprawa testowa')
        Select(self.selenium.find_element(By.NAME, 'client')).select_by_index(1)
        Select(self.selenium.find_element(By.NAME, 'case_type')).select_by_value('cywilna')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/sprawy/')
        )
        self.assertIn('TST-NOWA-999', self.selenium.page_source)

    def test_walidacja_wymaga_numeru_sprawy(self):
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Sprawa bez numeru')
        Select(self.selenium.find_element(By.NAME, 'client')).select_by_index(1)
        Select(self.selenium.find_element(By.NAME, 'case_type')).select_by_value('cywilna')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        self.assertIn('/szkp/sprawy/nowy/', self.selenium.current_url)

    def test_nowa_sprawa_przypisuje_prowadzacego(self):
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'case_number'))
        )
        self.selenium.find_element(By.NAME, 'case_number').send_keys('TST-ASSIGN-001')
        self.selenium.find_element(By.NAME, 'title').send_keys('Sprawa z przypisaniem')
        Select(self.selenium.find_element(By.NAME, 'client')).select_by_index(1)
        Select(self.selenium.find_element(By.NAME, 'case_type')).select_by_value('cywilna')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/sprawy/')
        )
        sprawa = Case.objects.get(case_number='TST-ASSIGN-001')
        self.assertTrue(
            CaseLawyer.objects.filter(
                case=sprawa, lawyer=self.lawyer, role=CaseLawyerRole.PROWADZACY,
            ).exists()
        )

    # --- edycja (RED — brak widoku case_edit) ---

    def test_edycja_tytulu_sprawy(self):
        sprawa = Case.objects.create(
            client=self.klient, case_number='TST-EDYCJA-001',
            title='Stary tytuł', case_type=CaseType.CYWILNA,
        )
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{sprawa.pk}/edytuj/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        pole_tytulu = self.selenium.find_element(By.NAME, 'title')
        pole_tytulu.clear()
        pole_tytulu.send_keys('Nowy tytuł')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/sprawy/')
        )
        self.assertIn('Nowy tytuł', self.selenium.page_source)
