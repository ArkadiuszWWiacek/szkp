from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseType, Client, ClientType,
    CourtHearing, HearingStatus, HearingType, Lawyer,
)

from Functional_tests.base import SzkpSeleniumTestCase


@tag('functional')
class US06CourtHearingsTest(SzkpSeleniumTestCase):
    """US-06: Terminy sądowe — lista na zakładce sprawy, dodawanie, walidacja, zmiana statusu."""

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
        self.sprawa = Case.objects.create(
            client=self.klient, case_number='TST-US06-001',
            title='Sprawa do testów terminów', case_type=CaseType.CYWILNA,
        )
        self._zaloguj_przez_orm(self.user)

    def _url_terminy(self):
        return self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/?tab=terminy'

# ===========================================================================
# widoczność terminów na stronie sprawy
# ===========================================================================

    @tag('smoke')
    def test_zakladka_terminy_wyswietla_sie(self):
        """Zakładka 'Terminy sądowe' na stronie sprawy jest widoczna."""
        self.selenium.get(self._url_terminy())
        self.assertIn('Terminy sądowe', self.selenium.page_source)

    def test_brak_terminow_wyswietla_pusty_stan(self):
        """Zakładka terminów bez rekordów wyświetla komunikat 'Brak terminów'."""
        self.selenium.get(self._url_terminy())
        self.assertIn('Brak terminów', self.selenium.page_source)

    def test_termin_widoczny_na_stronie_sprawy(self):
        """Istniejący termin jest widoczny po nazwie sądu na zakładce terminów."""
        CourtHearing.objects.create(
            case=self.sprawa,
            court_name='Sąd Rejonowy w Krakowie',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=datetime.now(tz=timezone.utc) + timedelta(days=7),
        )
        self.selenium.get(self._url_terminy())
        self.assertIn('Sąd Rejonowy w Krakowie', self.selenium.page_source)

# ===========================================================================
# dodawanie terminu przez formularz
# ===========================================================================

    @tag('smoke')
    def test_dodaj_termin_z_data_w_przyszlosci(self):
        """Formularz nowego terminu z datą w przyszłości zapisuje rekord i przekierowuje na zakładkę terminów."""
        self.selenium.get(self._url_terminy())
        self.selenium.find_element(By.CSS_SELECTOR, 'a[href*="terminy/nowy"]').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'court_name'))
        )
        self.selenium.find_element(By.NAME, 'court_name').send_keys('Sąd Okręgowy w Warszawie')
        Select(self.selenium.find_element(By.NAME, 'hearing_type')).select_by_value('rozprawa')
        przyszla_data = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M')
        self.selenium.find_element(By.NAME, 'scheduled_at').send_keys(przyszla_data)
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=terminy')
        )
        self.assertIn('Sąd Okręgowy w Warszawie', self.selenium.page_source)

    def test_walidacja_data_w_przeszlosci_blokuje(self):
        """Nowy termin z datą w przeszłości nie jest akceptowany — formularz pozostaje na stronie."""
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/terminy/nowy/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'court_name'))
        )
        self.selenium.find_element(By.NAME, 'court_name').send_keys('Sąd Rejonowy w Gdańsku')
        Select(self.selenium.find_element(By.NAME, 'hearing_type')).select_by_value('rozprawa')
        przeszla_data = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        # Firefox headless ignores send_keys() with past dates on datetime-local inputs;
        # setting the value via JS bypasses the browser-level restriction.
        self.selenium.execute_script(
            "document.querySelector('[name=\"scheduled_at\"]').value = arguments[0]",
            przeszla_data,
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        self.assertIn(
            f'/szkp/sprawy/{self.sprawa.pk}/terminy/nowy/',
            self.selenium.current_url,
        )

    def test_nowy_termin_ma_domyslny_status_planowany(self):
        """Nowo dodany termin ma domyślnie status 'Planowany' widoczny na zakładce."""
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/terminy/nowy/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'court_name'))
        )
        self.selenium.find_element(By.NAME, 'court_name').send_keys('Sąd Apelacyjny w Łodzi')
        Select(self.selenium.find_element(By.NAME, 'hearing_type')).select_by_value('posiedzenie')
        przyszla_data = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M')
        self.selenium.find_element(By.NAME, 'scheduled_at').send_keys(przyszla_data)
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=terminy')
        )
        self.assertIn('Planowany', self.selenium.page_source)

    def test_nowy_termin_ma_domyslne_przypomnienie_1440(self):
        """Pole 'reminder_minutes_before' ma domyślną wartość 1440 (24 godziny)."""
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/terminy/nowy/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'reminder_minutes_before'))
        )
        pole = self.selenium.find_element(By.NAME, 'reminder_minutes_before')
        self.assertEqual(pole.get_attribute('value'), '1440')

# ===========================================================================
# zmiana statusu terminu
# ===========================================================================

    def test_zmiana_statusu_terminu_na_odbyty(self):
        """Edycja terminu ze zmianą statusu na 'odbyty' aktualizuje rekord i przekierowuje na zakładkę."""
        termin = CourtHearing.objects.create(
            case=self.sprawa,
            court_name='Sąd Rejonowy w Poznaniu',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=datetime.now(tz=timezone.utc) + timedelta(days=3),
            status=HearingStatus.PLANOWANY,
        )
        self.selenium.get(
            self.live_server_url
            + f'/szkp/sprawy/{self.sprawa.pk}/terminy/{termin.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'status'))
        )
        Select(self.selenium.find_element(By.NAME, 'status')).select_by_value('odbyty')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=terminy')
        )
        self.assertIn('Odbyty', self.selenium.page_source)


@tag('functional')
class US06CourtHearingsAccessTest(SzkpSeleniumTestCase):
    """US-06: Kontrola dostępu do formularza terminu."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='testprawnik_us06acc', password='testpass123', is_staff=True,
        )
        self.lawyer = Lawyer.objects.create(
            user=self.user, first_name='Jan', last_name='Prawnik',
            bar_number='PL-US06-001',
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Anna', last_name='Klientka', pesel='85010112345',
        )
        self.sprawa = Case.objects.create(
            client=self.klient, case_number='TST-US06-ACC-001',
            title='Sprawa do testów dostępu terminów', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=self.sprawa, lawyer=self.lawyer, role=CaseLawyerRole.PROWADZACY,
        )

    def _url(self):
        return self.live_server_url + reverse(
            'szkp:court_hearing_new', kwargs={'case_pk': self.sprawa.pk}
        )

    def test_formularz_terminu_wymaga_zalogowania(self):
        """Niezalogowany użytkownik jest przekierowywany na stronę logowania."""
        self.selenium.get(self._url())
        WebDriverWait(self.selenium, 5).until(
            lambda d: '/accounts/' in d.current_url or 'login' in d.current_url.lower()
        )
        self.assertIn('/accounts/', self.selenium.current_url)

    def test_nieprzypisany_prawnik_nie_ma_dostepu_do_formularza_terminu(self):
        """Prawnik nieprzypisany do sprawy otrzymuje błąd 403 przy próbie dodania terminu."""
        inny_user = User.objects.create_user(
            username='obcy_us06', password='testpass123', is_staff=False,
        )
        Lawyer.objects.create(
            user=inny_user, first_name='Obcy', last_name='Prawnik',
            bar_number='PL-US06-999',
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
