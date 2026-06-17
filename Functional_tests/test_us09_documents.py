import os
import tempfile

from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from szkp.models import (
    Case, CaseType, Client, ClientType, Document, DocumentType,
    DocumentVersion, Lawyer,
)

from Functional_tests.base import SzkpSeleniumTestCase


def _setup_sprawa(test_case):
    test_case.user = User.objects.create_user(
        username='testprawnik', password='testpass123', is_staff=True,
    )
    test_case.lawyer = Lawyer.objects.create(
        user=test_case.user, first_name='Jan', last_name='Prawnik',
        bar_number='PL001',
    )
    test_case.klient = Client.objects.create(
        type=ClientType.OSOBA_FIZYCZNA,
        first_name='Anna', last_name='Klientka', pesel='89010112345',
    )
    test_case.sprawa = Case.objects.create(
        client=test_case.klient, case_number='TST-US09-001',
        title='Sprawa do testów dokumentów', case_type=CaseType.CYWILNA,
    )


@tag('functional')
class US09DocumentDisplayTest(SzkpSeleniumTestCase):

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        _setup_sprawa(self)
        self._zaloguj_przez_orm(self.user)

    def _url_dokumenty(self):
        return self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/?tab=dokumenty'

    @tag('smoke')
    def test_zakladka_dokumenty_wyswietla_sie(self):
        self.selenium.get(self._url_dokumenty())
        self.assertIn('Dokumenty', self.selenium.page_source)

    def test_brak_dokumentow_wyswietla_pusty_stan(self):
        self.selenium.get(self._url_dokumenty())
        self.assertIn('Brak dokumentów', self.selenium.page_source)

    def test_dokument_widoczny_na_stronie_sprawy(self):
        Document.objects.create(
            case=self.sprawa,
            title='Pozew o zapłatę',
            document_type=DocumentType.POZEW,
        )
        self.selenium.get(self._url_dokumenty())
        self.assertIn('Pozew o zapłatę', self.selenium.page_source)

    def test_przycisk_dodaj_dokument_dostepny(self):
        self.selenium.get(self._url_dokumenty())
        linki = self.selenium.find_elements(By.CSS_SELECTOR, f'a[href*="dokumenty/nowy"]')
        self.assertTrue(len(linki) > 0, 'Brak linku do dodania dokumentu na zakładce')


@tag('functional')
class US09DocumentAddTest(SzkpSeleniumTestCase):

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        _setup_sprawa(self)
        self._zaloguj_przez_orm(self.user)

    def _url_dokumenty(self):
        return self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/?tab=dokumenty'

    def _url_nowy(self):
        return (
            self.live_server_url
            + reverse('szkp:document_new', kwargs={'case_pk': self.sprawa.pk})
        )

    def _testowy_plik(self, suffix='.pdf'):
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(b'test document content')
        tmp.close()
        self.addCleanup(os.unlink, tmp.name)
        return tmp.name

    @tag('smoke')
    def test_dodaje_nowy_dokument_z_plikiem(self):
        self.selenium.get(self._url_dokumenty())
        self.selenium.find_element(By.CSS_SELECTOR, 'a[href*="dokumenty/nowy"]').click()
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Umowa zlecenia')
        Select(self.selenium.find_element(By.NAME, 'document_type')).select_by_value('umowa')
        self.selenium.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(
            self._testowy_plik()
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('tab=dokumenty'))
        self.assertIn('Umowa zlecenia', self.selenium.page_source)

    def test_typ_dokumentu_wybierany_z_listy(self):
        self.selenium.get(self._url_nowy())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'document_type'))
        )
        select = Select(self.selenium.find_element(By.NAME, 'document_type'))
        wartosci = [o.get_attribute('value') for o in select.options]
        for oczekiwana in ('pozew', 'odpowiedz', 'pismo_sadowe', 'notatka', 'umowa', 'dowod', 'wyrok', 'ugoda'):
            self.assertIn(oczekiwana, wartosci, f'Brak opcji "{oczekiwana}" w select document_type')

    def test_file_path_zapisany_po_uploadzie(self):
        self.selenium.get(self._url_nowy())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Notatka służbowa')
        Select(self.selenium.find_element(By.NAME, 'document_type')).select_by_value('notatka')
        self.selenium.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(
            self._testowy_plik()
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('tab=dokumenty'))
        wersja = DocumentVersion.objects.filter(document__case=self.sprawa).first()
        self.assertIsNotNone(wersja, 'Brak rekordu DocumentVersion po uploadzie')
        self.assertTrue(wersja.file_path, 'file_path jest pusty po uploadzie')

    def test_po_zapisie_redirect_na_zakladke_dokumenty(self):
        self.selenium.get(self._url_nowy())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Pozew')
        Select(self.selenium.find_element(By.NAME, 'document_type')).select_by_value('pozew')
        self.selenium.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(
            self._testowy_plik()
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('tab=dokumenty'))
        self.assertIn('tab=dokumenty', self.selenium.current_url)

    def test_walidacja_brak_tytulu(self):
        self.selenium.get(self._url_nowy())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'document_type'))
        )
        Select(self.selenium.find_element(By.NAME, 'document_type')).select_by_value('notatka')
        self.selenium.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(
            self._testowy_plik()
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        self.assertIn(
            reverse('szkp:document_new', kwargs={'case_pk': self.sprawa.pk}),
            self.selenium.current_url,
        )

    def test_walidacja_brak_pliku(self):
        self.selenium.get(self._url_nowy())
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys('Wyrok sądu')
        Select(self.selenium.find_element(By.NAME, 'document_type')).select_by_value('wyrok')
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        self.assertIn(
            reverse('szkp:document_new', kwargs={'case_pk': self.sprawa.pk}),
            self.selenium.current_url,
        )


@tag('functional')
class US09DocumentVersionTest(SzkpSeleniumTestCase):

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        _setup_sprawa(self)
        self._zaloguj_przez_orm(self.user)

    def _url_dokumenty(self):
        return self.live_server_url + f'/szkp/sprawy/{self.sprawa.pk}/?tab=dokumenty'

    def _testowy_plik(self, suffix='.pdf'):
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(b'test document content')
        tmp.close()
        self.addCleanup(os.unlink, tmp.name)
        return tmp.name

    def _dodaj_dokument_przez_formularz(self, title='Dokument testowy', doc_type='notatka'):
        url = self.live_server_url + reverse(
            'szkp:document_new', kwargs={'case_pk': self.sprawa.pk}
        )
        self.selenium.get(url)
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.NAME, 'title'))
        )
        self.selenium.find_element(By.NAME, 'title').send_keys(title)
        Select(self.selenium.find_element(By.NAME, 'document_type')).select_by_value(doc_type)
        self.selenium.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(
            self._testowy_plik()
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('tab=dokumenty'))

    def test_pierwsza_wersja_ma_numer_1(self):
        self._dodaj_dokument_przez_formularz()
        wersja = DocumentVersion.objects.filter(document__case=self.sprawa).first()
        self.assertIsNotNone(wersja)
        self.assertEqual(wersja.version_number, 1)

    def test_druga_wersja_ma_numer_2(self):
        self._dodaj_dokument_przez_formularz(title='Ugoda')
        dokument = Document.objects.get(case=self.sprawa)
        url = self.live_server_url + reverse(
            'szkp:document_version_upload',
            kwargs={'case_pk': self.sprawa.pk, 'document_pk': dokument.pk},
        )
        self.selenium.get(url)
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(
            self._testowy_plik()
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('tab=dokumenty'))
        wersje = DocumentVersion.objects.filter(document=dokument).order_by('version_number')
        self.assertEqual(wersje.count(), 2)
        self.assertEqual(wersje.last().version_number, 2)

    def test_wiele_wersji_widocznych_na_stronie(self):
        self._dodaj_dokument_przez_formularz(title='Odpowiedź na pozew')
        dokument = Document.objects.get(case=self.sprawa)
        url = self.live_server_url + reverse(
            'szkp:document_version_upload',
            kwargs={'case_pk': self.sprawa.pk, 'document_pk': dokument.pk},
        )
        self.selenium.get(url)
        WebDriverWait(self.selenium, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(
            self._testowy_plik()
        )
        self.selenium.find_element(By.CSS_SELECTOR, 'button.btn-szkp--primary').click()
        WebDriverWait(self.selenium, 5).until(EC.url_contains('tab=dokumenty'))
        self.selenium.get(self._url_dokumenty())
        self.assertIn('Odpowiedź na pozew', self.selenium.page_source)
        self.assertIn('wersja 1', self.selenium.page_source.lower())
        self.assertIn('wersja 2', self.selenium.page_source.lower())


@tag('functional')
class US09DocumentAccessTest(SzkpSeleniumTestCase):

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        _setup_sprawa(self)

    def _url_nowy(self):
        return (
            self.live_server_url
            + reverse('szkp:document_new', kwargs={'case_pk': self.sprawa.pk})
        )

    def test_formularz_wymaga_zalogowania(self):
        self.selenium.get(self._url_nowy())
        WebDriverWait(self.selenium, 5).until(
            lambda d: '/accounts/' in d.current_url or 'login' in d.current_url.lower()
        )
        self.assertIn('/accounts/', self.selenium.current_url)

    def test_prawnik_bez_dostepu_otrzymuje_403(self):
        inny_user = User.objects.create_user(
            username='obcy_prawnik', password='testpass123', is_staff=False,
        )
        Lawyer.objects.create(
            user=inny_user, first_name='Obcy', last_name='Prawnik',
            bar_number='PL999',
        )
        self._zaloguj_przez_orm(inny_user)
        self.selenium.get(self._url_nowy())
        WebDriverWait(self.selenium, 5).until(
            lambda d: '403' in d.page_source or 'Forbidden' in d.page_source
                      or '/szkp/' not in d.current_url or 'nowy' not in d.current_url
        )
        self.assertNotIn('input', self.selenium.page_source.lower().split('<form')[0]
                         if '<form' in self.selenium.page_source.lower() else '')
        kod = self.selenium.find_element(By.TAG_NAME, 'body').text
        self.assertTrue(
            '403' in kod or 'Forbidden' in kod or 'Brak dostępu' in kod
            or 'dokumenty/nowy' not in self.selenium.current_url,
            'Oczekiwano 403 lub przekierowania dla prawnika bez dostępu do sprawy',
        )
