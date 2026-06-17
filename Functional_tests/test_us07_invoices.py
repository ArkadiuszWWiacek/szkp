from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseType, Client, ClientType,
    Invoice, InvoiceStatus, Lawyer,
)

from Functional_tests.base import SzkpSeleniumTestCase


@tag('functional')
class US07InvoicesTest(SzkpSeleniumTestCase):
    """US-07: Faktury — CRUD, widok zakładki sprawy, lista faktur, filtry statusu, zmiana statusu."""

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

# ===========================================================================
# wyszukiwanie na liście faktur
# ===========================================================================

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

# ===========================================================================
# widoczność faktur na stronie sprawy
# ===========================================================================

    def test_zakladka_faktury_jest_widoczna(self):
        """Zakładka 'Faktury' na stronie sprawy jest widoczna i zawiera napis 'Faktury'."""
        self.selenium.get(self._url_faktury())
        self.assertIn('Faktury', self.selenium.page_source)

    def test_brak_faktur_wyswietla_pusty_stan(self):
        """Zakładka faktur bez rekordów wyświetla komunikat 'Brak faktur'."""
        self.selenium.get(self._url_faktury())
        self.assertIn('Brak faktur', self.selenium.page_source)

    def test_faktura_widoczna_na_stronie_sprawy(self):
        """Istniejąca faktura jest widoczna na zakładce faktur sprawy."""
        Invoice.objects.create(
            case=self.sprawa,
            invoice_number='FV/2025/001',
            net_amount=Decimal('1000.00'),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=14),
        )
        self.selenium.get(self._url_faktury())
        self.assertIn('FV/2025/001', self.selenium.page_source)

# ===========================================================================
# dodawanie faktury przez formularz
# ===========================================================================

    def test_link_wystaw_fakture_przenosi_do_formularza(self):
        """Link 'Wystaw fakturę' przenosi do formularza wystawiania faktury."""
        self.selenium.get(self._url_faktury())
        self.selenium.find_element(By.CSS_SELECTOR, 'a[href*="faktury/nowa"]').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'invoice_number'))
        )

    @tag('smoke')
    def test_dodaj_fakture_z_poprawnymi_danymi(self):
        """Formularz wystawienia faktury z poprawnymi danymi zapisuje rekord i przekierowuje na zakładkę."""
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
        """Nowa faktura ma domyślnie status 'Wystawiona' widoczny na zakładce faktur."""
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
        """Nowa faktura ma domyślnie walutę PLN widoczną na zakładce faktur."""
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
        """Kwota brutto (netto × 1,23) jest obliczana automatycznie przez Invoice.save() i widoczna po zapisie."""
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

# ===========================================================================
# walidacja formularza
# ===========================================================================

    def test_duplikat_numeru_faktury_blokuje_zapis(self):
        """Formularz odrzuca zapis gdy invoice_number już istnieje — pozostaje na stronie formularza."""
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

# ===========================================================================
# zmiana statusu faktury
# ===========================================================================

    def test_zmiana_statusu_faktury_na_oplacona(self):
        """Edycja faktury ze zmianą statusu na 'opłacona' aktualizuje rekord i przekierowuje na zakładkę."""
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

# ===========================================================================
# lista faktur
# ===========================================================================

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

    @tag('smoke')
    def test_lista_faktur_dostepna(self):
        """Strona /szkp/faktury/ jest dostępna i zawiera tytuł 'Faktury'."""
        self.selenium.get(self._url_lista())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        self.assertIn('Faktury', self.selenium.page_source)

    def test_lista_faktur_wyswietla_faktury(self):
        """Istniejąca faktura jest widoczna na liście /szkp/faktury/."""
        self._make_invoice('FV/US07-L/001')
        self.selenium.get(self._url_lista())
        self.assertIn('FV/US07-L/001', self.selenium.page_source)

    def test_lista_faktur_brak_wyswietla_pusty_stan(self):
        """Lista faktur bez rekordów wyświetla komunikat 'Brak faktur'."""
        self.selenium.get(self._url_lista())
        self.assertIn('Brak faktur', self.selenium.page_source)

    def test_filtr_listy_po_statusie_oplacona(self):
        """Filtr statusu 'opłacona' wyświetla tylko opłacone faktury i ukrywa wystawione."""
        self._make_invoice('FV/US07-L/WYS', status=InvoiceStatus.WYSTAWIONA)
        self._make_invoice('FV/US07-L/OPL', status=InvoiceStatus.OPŁACONA)
        self.selenium.get(self._url_lista(status='opłacona'))
        self.assertIn('FV/US07-L/OPL', self.selenium.page_source)
        self.assertNotIn('FV/US07-L/WYS', self.selenium.page_source)

    def test_filtr_listy_po_statusie_przeterminowana(self):
        """Filtr statusu 'przeterminowana' wyświetla tylko przeterminowane faktury."""
        self._make_invoice('FV/US07-L/WYS2', status=InvoiceStatus.WYSTAWIONA)
        self._make_invoice('FV/US07-L/PRZ', status=InvoiceStatus.PRZETERMINOWANA)
        self.selenium.get(self._url_lista(status='przeterminowana'))
        self.assertIn('FV/US07-L/PRZ', self.selenium.page_source)
        self.assertNotIn('FV/US07-L/WYS2', self.selenium.page_source)

    def test_filtr_listy_wszystkie_pokazuje_wszystkie(self):
        """Link 'Wszystkie' wyświetla faktury wszystkich statusów."""
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
        """Faktura na liście ma link do zakładki faktur powiązanej sprawy."""
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
        """Przycisk 'Opłacona' jest widoczny przy fakturze o statusie 'wystawiona'."""
        self._make_invoice('FV/US07-L/BTN')
        self.selenium.get(self._url_lista())
        btn = self.selenium.find_element(
            By.CSS_SELECTOR, 'button[data-invoice-action="mark-paid"]'
        )
        self.assertIsNotNone(btn)

    def test_przycisk_oplacona_niewidoczny_przy_oplaconej(self):
        """Przycisk 'Opłacona' nie jest wyświetlany dla już opłaconej faktury."""
        self._make_invoice('FV/US07-L/NOBTN', status=InvoiceStatus.OPŁACONA)
        self.selenium.get(self._url_lista())
        btns = self.selenium.find_elements(
            By.CSS_SELECTOR, 'button[data-invoice-action="mark-paid"]'
        )
        self.assertEqual(len(btns), 0)

    def test_klik_oplacona_na_liscie_zmienia_status(self):
        """Kliknięcie przycisku 'Opłacona' zmienia status faktury i chowa przycisk."""
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

# ===========================================================================
# kliknięcie pozycji faktury na zakładce faktury sprawy
# ===========================================================================

    def test_klikniecie_pozycji_faktury_przenosi_na_liste_z_filtrem(self):
        """Kliknięcie faktury na zakładce sprawy przekierowuje na listę /szkp/faktury/ z filtrem numeru."""
        self._make_invoice('FV/US07/LINK')
        self.selenium.get(self._url_faktury())
        element = self.selenium.find_element(By.CSS_SELECTOR, 'a.invoice-item')
        self.selenium.execute_script('arguments[0].click();', element)
        WebDriverWait(self.selenium, 5).until(EC.url_contains('/szkp/faktury/'))
        current = self.selenium.current_url
        self.assertIn('/szkp/faktury/', current)
        self.assertIn('q=', current)
        self.assertIn('FV', current)


@tag('functional')
class US07InvoicesAccessTest(SzkpSeleniumTestCase):
    """US-07: Kontrola dostępu do formularza faktury."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='testprawnik_us07acc', password='testpass123', is_staff=True,
        )
        self.lawyer = Lawyer.objects.create(
            user=self.user, first_name='Jan', last_name='Prawnik',
            bar_number='PL-US07-001',
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Maria', last_name='Fakturowa', pesel='86020212345',
        )
        self.sprawa = Case.objects.create(
            client=self.klient, case_number='TST-US07-ACC-001',
            title='Sprawa do testów dostępu faktur', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=self.sprawa, lawyer=self.lawyer, role=CaseLawyerRole.PROWADZACY,
        )

    def _url(self):
        return self.live_server_url + reverse(
            'szkp:invoice_new', kwargs={'case_pk': self.sprawa.pk}
        )

    def test_formularz_faktury_wymaga_zalogowania(self):
        """Niezalogowany użytkownik jest przekierowywany na stronę logowania."""
        self.selenium.get(self._url())
        WebDriverWait(self.selenium, 5).until(
            lambda d: '/accounts/' in d.current_url or 'login' in d.current_url.lower()
        )
        self.assertIn('/accounts/', self.selenium.current_url)

    def test_nieprzypisany_prawnik_nie_ma_dostepu_do_formularza_faktury(self):
        """Prawnik nieprzypisany do sprawy otrzymuje błąd 403 przy próbie wystawienia faktury."""
        inny_user = User.objects.create_user(
            username='obcy_us07', password='testpass123', is_staff=False,
        )
        Lawyer.objects.create(
            user=inny_user, first_name='Obcy', last_name='Prawnik',
            bar_number='PL-US07-999',
        )
        self._zaloguj_przez_orm(inny_user)
        self.selenium.get(self._url())
        WebDriverWait(self.selenium, 5).until(
            lambda d: '403' in d.page_source or 'Forbidden' in d.page_source
                      or 'Brak dostępu' in d.page_source
        )
        kod = self.selenium.find_element(By.TAG_NAME, 'body').text
        self.assertTrue(
            '403' in kod or 'Forbidden' in kod or 'Brak dostępu' in kod,
            'Oczekiwano 403 dla prawnika bez dostępu do sprawy',
        )
