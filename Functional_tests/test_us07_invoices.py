from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from szkp.models import (
    Case, CaseType, Client, ClientType, Invoice, InvoiceStatus, Lawyer,
)

from Functional_tests.base import SzkpSeleniumTestCase


@tag('functional')
class US07InvoicesTest(SzkpSeleniumTestCase):

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='testprawnik', password='testpass123', is_staff=True,
        )
        self.lawyer = Lawyer.objects.create(
            user=self.user, first_name='Jan', last_name='Prawnik',
            bar_number='PL007',
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Maria', last_name='Fakturowa', pesel='90020212345',
        )
        self.sprawa = Case.objects.create(
            client=self.klient, case_number='TST-US07-001',
            title='Sprawa do testów faktur', case_type=CaseType.CYWILNA,
        )
        self._zaloguj_przez_orm(self.user)

    def _url_faktury(self):
        return self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/?tab=faktury'

    def _jutro(self):
        return (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')

    def _za_30_dni(self):
        return (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')

    # --- widoczność faktur na stronie sprawy ---

    def test_zakladka_faktury_jest_widoczna(self):
        self.selenium.get(self._url_faktury())
        self.assertIn('Faktury', self.selenium.page_source)

    def test_brak_faktur_wyswietla_pusty_stan(self):
        self.selenium.get(self._url_faktury())
        self.assertIn('Brak faktur', self.selenium.page_source)

    def test_faktura_widoczna_na_stronie_sprawy(self):
        Invoice.objects.create(
            case=self.sprawa,
            invoice_number='FV/2025/001',
            net_amount=Decimal('1000.00'),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
        )
        self.selenium.get(self._url_faktury())
        self.assertIn('FV/2025/001', self.selenium.page_source)

    # --- dodawanie faktury przez formularz ---

    def test_link_wystaw_fakture_przenosi_do_formularza(self):
        self.selenium.get(self._url_faktury())
        self.selenium.find_element(By.CSS_SELECTOR, 'a[href*="faktury/nowa"]').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'invoice_number'))
        )

    def test_dodaj_fakture_z_poprawnymi_danymi(self):
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/faktury/nowa/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'invoice_number'))
        )
        self.selenium.find_element(By.NAME, 'invoice_number').send_keys('FV/2025/100')
        self.selenium.execute_script(
            "document.querySelector('[name=\"issue_date\"]').value = arguments[0]",
            self._jutro(),
        )
        self.selenium.execute_script(
            "document.querySelector('[name=\"due_date\"]').value = arguments[0]",
            self._za_30_dni(),
        )
        self.selenium.find_element(By.NAME, 'net_amount').send_keys('500')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=faktury')
        )
        self.assertIn('FV/2025/100', self.selenium.page_source)

    def test_nowa_faktura_ma_domyslny_status_wystawiona(self):
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/faktury/nowa/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'invoice_number'))
        )
        self.selenium.find_element(By.NAME, 'invoice_number').send_keys('FV/2025/101')
        self.selenium.execute_script(
            "document.querySelector('[name=\"issue_date\"]').value = arguments[0]",
            self._jutro(),
        )
        self.selenium.execute_script(
            "document.querySelector('[name=\"due_date\"]').value = arguments[0]",
            self._za_30_dni(),
        )
        self.selenium.find_element(By.NAME, 'net_amount').send_keys('200')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=faktury')
        )
        self.assertIn('Wystawiona', self.selenium.page_source)

    def test_nowa_faktura_ma_domyslna_walute_PLN(self):
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/faktury/nowa/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'invoice_number'))
        )
        self.selenium.find_element(By.NAME, 'invoice_number').send_keys('FV/2025/102')
        self.selenium.execute_script(
            "document.querySelector('[name=\"issue_date\"]').value = arguments[0]",
            self._jutro(),
        )
        self.selenium.execute_script(
            "document.querySelector('[name=\"due_date\"]').value = arguments[0]",
            self._za_30_dni(),
        )
        self.selenium.find_element(By.NAME, 'net_amount').send_keys('300')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=faktury')
        )
        self.assertIn('PLN', self.selenium.page_source)

    def test_kwota_brutto_wyliczana_automatycznie(self):
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/faktury/nowa/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'invoice_number'))
        )
        self.selenium.find_element(By.NAME, 'invoice_number').send_keys('FV/2025/103')
        self.selenium.execute_script(
            "document.querySelector('[name=\"issue_date\"]').value = arguments[0]",
            self._jutro(),
        )
        self.selenium.execute_script(
            "document.querySelector('[name=\"due_date\"]').value = arguments[0]",
            self._za_30_dni(),
        )
        self.selenium.find_element(By.NAME, 'net_amount').send_keys('1000')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=faktury')
        )
        self.assertIn('1230,00', self.selenium.page_source)

    # --- walidacja formularza ---

    def test_duplikat_numeru_faktury_blokuje_zapis(self):
        Invoice.objects.create(
            case=self.sprawa,
            invoice_number='FV/2025/DUP',
            net_amount=Decimal('100.00'),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
        )
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/faktury/nowa/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'invoice_number'))
        )
        self.selenium.find_element(By.NAME, 'invoice_number').send_keys('FV/2025/DUP')
        self.selenium.execute_script(
            "document.querySelector('[name=\"issue_date\"]').value = arguments[0]",
            self._jutro(),
        )
        self.selenium.execute_script(
            "document.querySelector('[name=\"due_date\"]').value = arguments[0]",
            self._za_30_dni(),
        )
        self.selenium.find_element(By.NAME, 'net_amount').send_keys('100')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        self.assertIn(
            f'/szkp/sprawy/{self.sprawa.pk}/faktury/nowa/',
            self.selenium.current_url,
        )

    # --- zmiana statusu faktury ---

    def test_zmiana_statusu_faktury_na_oplacona(self):
        faktura = Invoice.objects.create(
            case=self.sprawa,
            invoice_number='FV/2025/EDIT',
            net_amount=Decimal('800.00'),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status=InvoiceStatus.WYSTAWIONA,
        )
        self.selenium.get(
            self.live_server_url
            + f'/szkp/sprawy/{self.sprawa.pk}/faktury/{faktura.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'status'))
        )
        Select(self.selenium.find_element(By.NAME, 'status')).select_by_value('opłacona')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=faktury')
        )
        self.assertIn('Opłacona', self.selenium.page_source)
