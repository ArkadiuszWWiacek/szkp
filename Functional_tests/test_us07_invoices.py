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

    # --- wyszukiwanie na liście faktur ---

    def test_wyszukiwanie_po_numerze_faktury(self):
        """Wyszukiwanie po numerze faktury zwraca pasującą fakturę."""
        case = Case.objects.create(
            client=self.klient, case_number='TST-FNK-001',
            title='Sprawa testowa', case_type=CaseType.CYWILNA,
        )
        Invoice.objects.create(
            case=case, invoice_number='FV/TEST/2025/001',
            issue_date=date.today(), due_date=date.today(),
            net_amount=Decimal('100.00'),
        )
        self.selenium.get(self.live_server_url + '/szkp/faktury/?q=FV%2FTEST%2F2025%2F001')
        self.assertIn('FV/TEST/2025/001', self.selenium.page_source)

    def test_wyszukiwanie_po_numerze_sprawy(self):
        """Wyszukiwanie po numerze sprawy zwraca faktury tej sprawy."""
        case = Case.objects.create(
            client=self.klient, case_number='TST-FNK-002',
            title='Sprawa testowa 2', case_type=CaseType.CYWILNA,
        )
        Invoice.objects.create(
            case=case, invoice_number='FV/TEST/2025/002',
            issue_date=date.today(), due_date=date.today(),
            net_amount=Decimal('200.00'),
        )
        self.selenium.get(self.live_server_url + '/szkp/faktury/?q=TST-FNK-002')
        self.assertIn('FV/TEST/2025/002', self.selenium.page_source)

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

    # --- lista faktur ---

    def _url_lista(self, status=None):
        url = self.live_server_url + '/szkp/faktury/'
        if status:
            url += f'?status={status}'
        return url

    def _make_invoice(self, number, status=InvoiceStatus.WYSTAWIONA, **kwargs):
        return Invoice.objects.create(
            case=self.sprawa,
            invoice_number=number,
            net_amount=Decimal('500.00'),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
            status=status,
            **kwargs,
        )

    def test_lista_faktur_dostepna(self):
        self.selenium.get(self._url_lista())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        self.assertIn('Faktury', self.selenium.page_source)

    def test_lista_faktur_wyswietla_faktury(self):
        self._make_invoice('FV/US07-L/001')
        self.selenium.get(self._url_lista())
        self.assertIn('FV/US07-L/001', self.selenium.page_source)

    def test_lista_faktur_brak_wyswietla_pusty_stan(self):
        self.selenium.get(self._url_lista())
        self.assertIn('Brak faktur', self.selenium.page_source)

    def test_filtr_listy_po_statusie_oplacona(self):
        self._make_invoice('FV/US07-L/WYS', status=InvoiceStatus.WYSTAWIONA)
        self._make_invoice('FV/US07-L/OPL', status=InvoiceStatus.OPŁACONA)
        self.selenium.get(self._url_lista(status='opłacona'))
        self.assertIn('FV/US07-L/OPL', self.selenium.page_source)
        self.assertNotIn('FV/US07-L/WYS', self.selenium.page_source)

    def test_filtr_listy_po_statusie_przeterminowana(self):
        self._make_invoice('FV/US07-L/WYS2', status=InvoiceStatus.WYSTAWIONA)
        self._make_invoice('FV/US07-L/PRZ', status=InvoiceStatus.PRZETERMINOWANA)
        self.selenium.get(self._url_lista(status='przeterminowana'))
        self.assertIn('FV/US07-L/PRZ', self.selenium.page_source)
        self.assertNotIn('FV/US07-L/WYS2', self.selenium.page_source)

    def test_filtr_listy_wszystkie_pokazuje_wszystkie(self):
        self._make_invoice('FV/US07-L/A', status=InvoiceStatus.WYSTAWIONA)
        self._make_invoice('FV/US07-L/B', status=InvoiceStatus.OPŁACONA)
        self.selenium.get(self._url_lista())
        self.selenium.find_element(By.LINK_TEXT, 'Wszystkie').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Wszystkie'))
        )
        self.assertIn('FV/US07-L/A', self.selenium.page_source)
        self.assertIn('FV/US07-L/B', self.selenium.page_source)

    def test_lista_faktura_ma_link_do_sprawy(self):
        self._make_invoice('FV/US07-L/LINK')
        self.selenium.get(self._url_lista())
        self.selenium.find_element(
            By.CSS_SELECTOR, f'a[href*="/sprawy/{self.sprawa.pk}/"]'
        ).click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains(f'/sprawy/{self.sprawa.pk}/')
        )
        self.assertIn('tab=faktury', self.selenium.current_url)

    def test_przycisk_oplacona_widoczny_przy_wystawionej(self):
        self._make_invoice('FV/US07-L/BTN')
        self.selenium.get(self._url_lista())
        btn = self.selenium.find_element(
            By.CSS_SELECTOR, 'button[data-invoice-action="mark-paid"]'
        )
        self.assertIsNotNone(btn)

    def test_przycisk_oplacona_niewidoczny_przy_oplaconej(self):
        self._make_invoice('FV/US07-L/NOBTN', status=InvoiceStatus.OPŁACONA)
        self.selenium.get(self._url_lista())
        btns = self.selenium.find_elements(
            By.CSS_SELECTOR, 'button[data-invoice-action="mark-paid"]'
        )
        self.assertEqual(len(btns), 0)

    def test_klik_oplacona_na_liscie_zmienia_status(self):
        self._make_invoice('FV/US07-L/KLIK')
        self.selenium.get(self._url_lista())
        self.selenium.find_element(
            By.CSS_SELECTOR, 'button[data-invoice-action="mark-paid"]'
        ).click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        self.assertIn('Opłacona', self.selenium.page_source)
        btns = self.selenium.find_elements(
            By.CSS_SELECTOR, 'button[data-invoice-action="mark-paid"]'
        )
        self.assertEqual(len(btns), 0)

    # --- kliknięcie pozycji faktury na zakładce faktury sprawy ---

    def test_klikniecie_pozycji_faktury_przenosi_na_liste_z_filtrem(self):
        self._make_invoice('FV/US07/LINK')
        self.selenium.get(self._url_faktury())
        element = self.selenium.find_element(By.CSS_SELECTOR, 'a.invoice-item')
        self.selenium.execute_script('arguments[0].click();', element)
        WebDriverWait(self.selenium, 5).until(EC.url_contains('/szkp/faktury/'))
        current = self.selenium.current_url
        self.assertIn('/szkp/faktury/', current)
        self.assertIn('q=', current)
        self.assertIn('FV', current)
