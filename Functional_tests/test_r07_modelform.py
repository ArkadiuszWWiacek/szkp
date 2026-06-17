"""
R-07: Zamiana forms.Form na ModelForm.
Testy funkcjonalne (Selenium).

"""

import os
import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseStatus, CaseType,
    Client, ClientType,
    CourtHearing, HearingType,
    Document, DocumentType, DocumentVersion,
    Invoice, InvoiceStatus,
    Lawyer,
)

from Functional_tests.base import SzkpSeleniumTestCase


# ---------------------------------------------------------------------------
# Pomocniczy miksin — wspólny setUp dla testów wymagających staff + sprawy
# ---------------------------------------------------------------------------

def _setup_base(tc):
    tc.user = User.objects.create_user(
        username='r07user', password='testpass123', is_staff=True,
    )
    tc.lawyer = Lawyer.objects.create(
        user=tc.user, first_name='Anna', last_name='Tester', bar_number='R07-001',
    )
    tc.klient = Client.objects.create(
        type=ClientType.OSOBA_FIZYCZNA,
        first_name='Jan', last_name='Testowy', pesel='90010112345',
    )
    tc.sprawa = Case.objects.create(
        client=tc.klient, case_number='TST-R07-001',
        title='Sprawa do testów R-07', case_type=CaseType.CYWILNA,
    )
    CaseLawyer.objects.create(
        case=tc.sprawa, lawyer=tc.lawyer, role=CaseLawyerRole.PROWADZACY,
    )
    tc._zaloguj_przez_orm(tc.user)


def _tmp_file(suffix='.pdf'):
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(b'test content r07')
    tmp.close()
    return tmp.name


# ===========================================================================
# Zamiana forms.Form na ModelForm
# ===========================================================================

@tag('functional')
class R07ClientFormTest(SzkpSeleniumTestCase):
    """R-07: ClientForm — pre-populacja i widoczność pól przy edycji."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username='r07client', password='testpass123',
        )
        self._zaloguj_przez_orm(self.user)

    def test_edycja_firmy_pola_firmowe_prepopulowane(self):
        """Edycja firmy: company_name i NIP są widoczne i wypełnione w formularzu GET."""
        firma = Client.objects.create(
            type=ClientType.FIRMA,
            company_name='ACME Sp. z o.o.',
            nip='5250012345',
        )
        self.selenium.get(
            self.live_server_url + f'/szkp/klienci/{firma.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.ID, 'id_company_name'))
        )
        company_val = self.selenium.find_element(By.ID, 'id_company_name').get_attribute('value')
        nip_val = self.selenium.find_element(By.ID, 'id_nip').get_attribute('value')
        self.assertEqual(company_val, 'ACME Sp. z o.o.')
        self.assertEqual(nip_val, '5250012345')

    def test_edycja_firmy_sekcja_firmowa_widoczna_bez_klikania(self):
        """Edycja firmy: sekcja pól firmowych jest widoczna od razu (nie ukryta przez d-none)."""
        firma = Client.objects.create(
            type=ClientType.FIRMA,
            company_name='Firma Widoczna', nip='5250012346',
        )
        self.selenium.get(
            self.live_server_url + f'/szkp/klienci/{firma.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.visibility_of_element_located((By.ID, 'id_company_name'))
        )
        pole = self.selenium.find_element(By.ID, 'id_company_name')
        self.assertTrue(pole.is_displayed(), 'Pole company_name powinno być widoczne dla firmy')

    def test_edycja_osoby_fizycznej_pola_prepopulowane(self):
        """Edycja osoby fizycznej: imię, nazwisko i PESEL są wypełnione w formularzu GET."""
        osoba = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Prepopulowane', last_name='Dane', pesel='89010112345',
        )
        self.selenium.get(
            self.live_server_url + f'/szkp/klienci/{osoba.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.ID, 'id_first_name'))
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'id_first_name').get_attribute('value'),
            'Prepopulowane',
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'id_last_name').get_attribute('value'),
            'Dane',
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'id_pesel').get_attribute('value'),
            '89010112345',
        )


# ===========================================================================
# Formularz sprawy — logika biznesowa
# ===========================================================================

@tag('functional')
class R07CaseFormTest(SzkpSeleniumTestCase):
    """R-07: CaseForm — closed_at oraz pre-populacja client dropdown."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        _setup_base(self)

    def test_nowa_sprawa_ze_statusem_zakonczona_ustawia_closed_at(self):
        """Tworzenie nowej sprawy z status=ZAKOŃCZONA przez formularz ustawia pole closed_at."""
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'case_number'))
        )
        self.selenium.find_element(By.NAME, 'case_number').send_keys('TST-R07-ZAKONCZ')
        self.selenium.find_element(By.NAME, 'title').send_keys('Sprawa zamknięta')
        Select(self.selenium.find_element(By.NAME, 'client')).select_by_value(
            str(self.klient.pk)
        )
        Select(self.selenium.find_element(By.NAME, 'case_type')).select_by_value('cywilna')
        Select(self.selenium.find_element(By.NAME, 'status')).select_by_value('zakończona')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('/szkp/sprawy/')
        )
        sprawa = Case.objects.get(case_number='TST-R07-ZAKONCZ')
        self.assertIsNotNone(
            sprawa.closed_at,
            'closed_at powinno być ustawione gdy nowa sprawa ma status ZAKOŃCZONA',
        )

    def test_edycja_sprawy_zmiana_statusu_na_zakonczona_ustawia_closed_at(self):
        """Edycja istniejącej sprawy (NOWA→ZAKOŃCZONA) przez formularz ustawia closed_at."""
        sprawa = Case.objects.create(
            client=self.klient, case_number='TST-R07-EDIT-ZAKONCZ',
            title='Do zamknięcia', case_type=CaseType.CYWILNA,
            status=CaseStatus.NOWA,
        )
        self.assertIsNone(sprawa.closed_at)
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{sprawa.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'status'))
        )
        Select(self.selenium.find_element(By.NAME, 'status')).select_by_value('zakończona')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains(f'/szkp/sprawy/{sprawa.pk}/')
        )
        sprawa.refresh_from_db()
        self.assertIsNotNone(
            sprawa.closed_at,
            'closed_at powinno być ustawione po zmianie statusu na ZAKOŃCZONA przez formularz',
        )

    def test_edycja_sprawy_client_dropdown_ma_wybrany_aktualny_klient(self):
        """Edycja sprawy: dropdown klienta ma pre-wybranego aktualnego klienta."""
        sprawa = Case.objects.create(
            client=self.klient, case_number='TST-R07-CLIENT-DROP',
            title='Sprawa client dropdown', case_type=CaseType.CYWILNA,
        )
        self.selenium.get(
            self.live_server_url + f'/szkp/sprawy/{sprawa.pk}/edytuj/'
        )
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.ID, 'id_client'))
        )
        select = Select(self.selenium.find_element(By.ID, 'id_client'))
        wybrany = select.first_selected_option.get_attribute('value')
        self.assertEqual(
            wybrany, str(self.klient.pk),
            'Formularz edycji sprawy powinien mieć pre-wybranego aktualnego klienta',
        )


# ===========================================================================
# Formularz faktury — walidacja unikalności i kwoty
# ===========================================================================

@tag('functional')
class R07InvoiceFormTest(SzkpSeleniumTestCase):
    """R-07: InvoiceForm — instance_pk exclusion i przeliczanie gross_amount."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        _setup_base(self)

    def _jutro(self):
        return (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')

    def _za_30_dni(self):
        return (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')

    def _url_edit(self, pk):
        return self.live_server_url + reverse(
            'szkp:invoice_edit',
            kwargs={'case_pk': self.sprawa.pk, 'pk': pk},
        )

    def test_edycja_faktury_zachowuje_wlasny_numer_bez_bledu_duplikatu(self):
        """Edycja faktury z własnym numerem nie powoduje błędu unikalności."""
        faktura = Invoice.objects.create(
            case=self.sprawa, invoice_number='FV/R07/EDIT/001',
            net_amount=Decimal('100.00'),
            issue_date=date.today(), due_date=date.today() + timedelta(days=14),
        )
        self.selenium.get(self._url_edit(faktura.pk))
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'invoice_number'))
        )
        # Wysyłamy formularz z tym samym numerem faktury — nie powinno dać błędu
        self.selenium.execute_script(
            "document.querySelector('[name=\"issue_date\"]').value = arguments[0]",
            self._jutro(),
        )
        self.selenium.execute_script(
            "document.querySelector('[name=\"due_date\"]').value = arguments[0]",
            self._za_30_dni(),
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=faktury')
        )
        self.assertIn('tab=faktury', self.selenium.current_url,
                      'Edycja z własnym numerem faktury powinna przekierować na tab=faktury')

    def test_edycja_faktury_zmiana_kwoty_netto_przelicza_gross_amount(self):
        """Edycja faktury ze zmianą net_amount przelicza gross_amount na Invoice.save()."""
        faktura = Invoice.objects.create(
            case=self.sprawa, invoice_number='FV/R07/GROSS/001',
            net_amount=Decimal('1000.00'), vat_rate=Decimal('0.23'),
            issue_date=date.today(), due_date=date.today() + timedelta(days=14),
        )
        self.assertEqual(faktura.gross_amount, Decimal('1230.00'))
        self.selenium.get(self._url_edit(faktura.pk))
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'net_amount'))
        )
        pole = self.selenium.find_element(By.NAME, 'net_amount')
        pole.clear()
        pole.send_keys('2000')
        self.selenium.execute_script(
            "document.querySelector('[name=\"issue_date\"]').value = arguments[0]",
            self._jutro(),
        )
        self.selenium.execute_script(
            "document.querySelector('[name=\"due_date\"]').value = arguments[0]",
            self._za_30_dni(),
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=faktury')
        )
        faktura.refresh_from_db()
        self.assertEqual(
            faktura.gross_amount, Decimal('2460.00'),
            'gross_amount powinno być przeliczone po zmianie net_amount przez formularz',
        )

    def test_edycja_faktury_pola_kwot_sa_prepopulowane(self):
        """Edycja faktury: pola net_amount i vat_rate pokazują aktualne wartości."""
        faktura = Invoice.objects.create(
            case=self.sprawa, invoice_number='FV/R07/PREPOP/001',
            net_amount=Decimal('1234.56'), vat_rate=Decimal('0.08'),
            issue_date=date.today(), due_date=date.today() + timedelta(days=14),
        )
        self.selenium.get(self._url_edit(faktura.pk))
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'net_amount'))
        )
        net = self.selenium.find_element(By.NAME, 'net_amount').get_attribute('value')
        vat = self.selenium.find_element(By.NAME, 'vat_rate').get_attribute('value')
        self.assertEqual(
            Decimal(net), Decimal('1234.56'),
            f'net_amount powinno być pre-populowane: oczekiwano 1234.56, otrzymano {net}',
        )
        self.assertEqual(
            Decimal(vat), Decimal('0.08'),
            f'vat_rate powinno być pre-populowane: oczekiwano 0.08, otrzymano {vat}',
        )


# ===========================================================================
# Formularz terminu sądowego
# ===========================================================================

@tag('functional')
class R07CourtHearingFormTest(SzkpSeleniumTestCase):
    """R-07: CourtHearingForm — is_new=False zezwala na datę w przeszłości."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        _setup_base(self)

    def _url_edit_termin(self, pk):
        return self.live_server_url + reverse(
            'szkp:court_hearing_edit',
            kwargs={'case_pk': self.sprawa.pk, 'pk': pk},
        )

    def test_edycja_terminu_data_w_przeszlosci_jest_akceptowana(self):
        """Edycja istniejącego terminu: zmiana daty na przeszłą jest dozwolona (is_new=False)."""
        from datetime import datetime, timezone as dt_tz
        termin = CourtHearing.objects.create(
            case=self.sprawa,
            court_name='Sąd Rejonowy Testowy',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=datetime.now(tz=dt_tz.utc) + timedelta(days=30),
        )
        self.selenium.get(self._url_edit_termin(termin.pk))
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'scheduled_at'))
        )
        przeszla_data = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self.selenium.execute_script(
            "document.querySelector('[name=\"scheduled_at\"]').value = arguments[0]",
            przeszla_data,
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=terminy')
        )
        self.assertIn(
            'tab=terminy', self.selenium.current_url,
            'Edycja terminu z datą w przeszłości powinna zostać zaakceptowana (is_new=False)',
        )

    def test_edycja_terminu_court_name_jest_prepopulowany(self):
        """Edycja terminu: pole court_name pokazuje aktualną wartość z bazy."""
        from datetime import datetime, timezone as dt_tz
        termin = CourtHearing.objects.create(
            case=self.sprawa,
            court_name='Sąd Okręgowy Prepopulowany',
            hearing_type=HearingType.POSIEDZENIE,
            scheduled_at=datetime.now(tz=dt_tz.utc) + timedelta(days=14),
        )
        self.selenium.get(self._url_edit_termin(termin.pk))
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'court_name'))
        )
        val = self.selenium.find_element(By.NAME, 'court_name').get_attribute('value')
        self.assertEqual(
            val, 'Sąd Okręgowy Prepopulowany',
            'Pole court_name powinno być pre-populowane aktualną wartością z bazy',
        )


# ===========================================================================
# Formularz dokumentu — edycja bez pliku
# ===========================================================================

@tag('functional')
class R07DocumentFormTest(SzkpSeleniumTestCase):
    """R-07: DocumentForm — edycja metadanych bez nowego pliku (is_new=False)."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        _setup_base(self)

    def _url_edit_dok(self, pk):
        return self.live_server_url + reverse(
            'szkp:document_edit',
            kwargs={'case_pk': self.sprawa.pk, 'pk': pk},
        )

    def _dodaj_dokument(self, title='Dokument testowy R07', doc_type=DocumentType.NOTATKA):
        return Document.objects.create(
            case=self.sprawa, title=title, document_type=doc_type,
        )

    def test_edycja_dokumentu_bez_nowego_pliku_jest_mozliwa(self):
        """Edycja dokumentu (tylko tytuł/typ, bez nowego pliku) nie powoduje błędu 'plik wymagany'."""
        dok = self._dodaj_dokument()
        self.selenium.get(self._url_edit_dok(dok.pk))
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        pole = self.selenium.find_element(By.NAME, 'title')
        pole.clear()
        pole.send_keys('Dokument po edycji')
        # NIE dodajemy pliku
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(
            EC.url_contains('tab=dokumenty')
        )
        self.assertIn(
            'tab=dokumenty', self.selenium.current_url,
            'Edycja dokumentu bez nowego pliku powinna przekierować na tab=dokumenty',
        )
        dok.refresh_from_db()
        self.assertEqual(
            dok.title, 'Dokument po edycji',
            'Tytuł dokumentu powinien zostać zaktualizowany',
        )

    def test_edycja_dokumentu_tytul_jest_prepopulowany(self):
        """Edycja dokumentu: pole title zawiera aktualny tytuł z bazy (GET)."""
        dok = self._dodaj_dokument(title='Tytuł Do Sprawdzenia')
        self.selenium.get(self._url_edit_dok(dok.pk))
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        val = self.selenium.find_element(By.NAME, 'title').get_attribute('value')
        self.assertEqual(
            val, 'Tytuł Do Sprawdzenia',
            'Pole title w formularzu edycji powinno pokazywać aktualny tytuł dokumentu',
        )
