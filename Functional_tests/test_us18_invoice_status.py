from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from szkp.models import (
    Case, CaseType, Client, ClientType, Invoice, InvoiceStatus, Lawyer,
)

from Functional_tests.base import SzkpSeleniumTestCase


@tag('functional')
class US18InvoiceStatusTest(SzkpSeleniumTestCase):

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='testprawnik18', password='testpass123', is_staff=True,
        )
        self.lawyer = Lawyer.objects.create(
            user=self.user, first_name='Jan', last_name='Prawnik',
            bar_number='PL018',
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Maria', last_name='Fakturowa', pesel='90020212346',
        )
        self.sprawa = Case.objects.create(
            client=self.klient, case_number='TST-US18-001',
            title='Sprawa do testów statusu faktur', case_type=CaseType.CYWILNA,
        )
        self._zaloguj_przez_orm(self.user)

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

    # --- lista faktur (podstawowa widoczność) ---

    def test_lista_faktur_dostepna(self):
        self.selenium.get(self._url_lista())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        self.assertIn('Faktury', self.selenium.page_source)

    def test_lista_faktur_wyswietla_faktury(self):
        self._make_invoice('FV/US18/001')
        self.selenium.get(self._url_lista())
        self.assertIn('FV/US18/001', self.selenium.page_source)

    def test_brak_faktur_wyswietla_pusty_stan(self):
        self.selenium.get(self._url_lista())
        self.assertIn('Brak faktur', self.selenium.page_source)

    # --- filtr po statusie ---

    def test_filtr_po_statusie_oplacona(self):
        self._make_invoice('FV/US18/WYS', status=InvoiceStatus.WYSTAWIONA)
        self._make_invoice('FV/US18/OPL', status=InvoiceStatus.OPŁACONA)
        self.selenium.get(self._url_lista(status='opłacona'))
        self.assertIn('FV/US18/OPL', self.selenium.page_source)
        self.assertNotIn('FV/US18/WYS', self.selenium.page_source)

    def test_filtr_po_statusie_przeterminowana(self):
        self._make_invoice('FV/US18/WYS2', status=InvoiceStatus.WYSTAWIONA)
        self._make_invoice('FV/US18/PRZ', status=InvoiceStatus.PRZETERMINOWANA)
        self.selenium.get(self._url_lista(status='przeterminowana'))
        self.assertIn('FV/US18/PRZ', self.selenium.page_source)
        self.assertNotIn('FV/US18/WYS2', self.selenium.page_source)

    def test_filtr_wszystkie_pokazuje_obie_faktury(self):
        self._make_invoice('FV/US18/A', status=InvoiceStatus.WYSTAWIONA)
        self._make_invoice('FV/US18/B', status=InvoiceStatus.OPŁACONA)
        self.selenium.get(self._url_lista())
        self.selenium.find_element(By.LINK_TEXT, 'Wszystkie').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Wszystkie'))
        )
        self.assertIn('FV/US18/A', self.selenium.page_source)
        self.assertIn('FV/US18/B', self.selenium.page_source)

    # --- link do sprawy ---

    def test_kazda_faktura_ma_link_do_sprawy(self):
        self._make_invoice('FV/US18/LINK')
        self.selenium.get(self._url_lista())
        self.selenium.find_element(
            By.CSS_SELECTOR, f'a[href*="/sprawy/{self.sprawa.pk}/"]'
        ).click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains(f'/sprawy/{self.sprawa.pk}/')
        )
        self.assertIn('tab=faktury', self.selenium.current_url)

    # --- przycisk "Opłacona" ---

    def test_przycisk_oplacona_widoczny_przy_wystawionej(self):
        self._make_invoice('FV/US18/BTN')
        self.selenium.get(self._url_lista())
        btn = self.selenium.find_element(
            By.CSS_SELECTOR, 'button[data-invoice-action="mark-paid"]'
        )
        self.assertIsNotNone(btn)

    def test_przycisk_oplacona_niewidoczny_przy_oplaconej(self):
        self._make_invoice('FV/US18/NOBTN', status=InvoiceStatus.OPŁACONA)
        self.selenium.get(self._url_lista())
        btns = self.selenium.find_elements(
            By.CSS_SELECTOR, 'button[data-invoice-action="mark-paid"]'
        )
        self.assertEqual(len(btns), 0)

    def test_klik_oplacona_zmienia_status(self):
        self._make_invoice('FV/US18/KLIK')
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
