from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import tag
from django.urls import reverse

from szkp.models import (
    Case, CaseType, Document, DocumentType, DocumentVersion,
)
from szkp.tests.base import StaffLawyerTestCase


def _plik(name='doc.pdf', content=b'test pdf content', mime='application/pdf'):
    return SimpleUploadedFile(name, content, content_type=mime)


@tag('integration')
class DocumentFormCreateViewTest(StaffLawyerTestCase):
    """document_form (nowy dokument): walidacja POST, tworzenie Document + DocumentVersion."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US09-NEW-001',
            title='Sprawa do testów dokumentów', case_type=CaseType.CYWILNA,
        )

    def _url(self):
        return reverse('szkp:document_new', kwargs={'case_pk': self.sprawa.pk})

    def _redirect_url(self):
        return reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=dokumenty'

    def _valid_data(self, **overrides):
        data = {
            'title': 'Pozew o zapłatę',
            'document_type': DocumentType.POZEW,
            'file': _plik(),
        }
        data.update(overrides)
        return data

    def test_get_formularz_zwraca_200(self):
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_get_context_zawiera_form_data(self):
        r = self.client.get(self._url())
        self.assertIn('form_data', r.context)

    def test_post_valid_tworzy_dokument(self):
        self.client.post(self._url(), self._valid_data())
        self.assertTrue(
            Document.objects.filter(case=self.sprawa, title='Pozew o zapłatę').exists()
        )

    def test_post_valid_tworzy_wersje_z_file_path(self):
        self.client.post(self._url(), self._valid_data(title='Umowa'))
        dokument = Document.objects.get(case=self.sprawa, title='Umowa')
        wersja = DocumentVersion.objects.get(document=dokument)
        self.assertTrue(wersja.file_path, 'file_path powinien być ustawiony po uploadzie')
        self.assertEqual(wersja.version_number, 1)

    def test_post_valid_przypisuje_created_by_lawyer(self):
        self.client.post(self._url(), self._valid_data(title='Notatka'))
        dokument = Document.objects.get(case=self.sprawa, title='Notatka')
        wersja = DocumentVersion.objects.get(document=dokument)
        self.assertEqual(wersja.created_by_lawyer, self.lawyer)

    def test_post_valid_redirect_na_zakladke_dokumenty(self):
        r = self.client.post(self._url(), self._valid_data())
        self.assertRedirects(r, self._redirect_url())

    def test_post_brak_tytulu_zwraca_blad(self):
        r = self.client.post(self._url(), self._valid_data(title=''))
        self.assertEqual(r.status_code, 200)
        self.assertIn('title', r.context['errors'])

    def test_post_brak_pliku_zwraca_blad(self):
        data = {'title': 'Pismo', 'document_type': DocumentType.PISMO_SADOWE}
        r = self.client.post(self._url(), data)
        self.assertEqual(r.status_code, 200)
        self.assertIn('file', r.context['errors'])

    def test_post_brak_typu_dokumentu_zwraca_blad(self):
        r = self.client.post(self._url(), self._valid_data(document_type=''))
        self.assertEqual(r.status_code, 200)
        self.assertIn('document_type', r.context['errors'])

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])

    def test_nieprzypisany_prawnik_dostaje_403(self):
        user2 = User.objects.create_user('obcy_doc', password='pass', is_staff=False)
        self.client.force_login(user2)
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 403)


@tag('integration')
class DocumentFormEditViewTest(StaffLawyerTestCase):
    """document_form (edycja dokumentu): aktualizacja metadanych, opcjonalny upload nowej wersji."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US09-EDIT-001',
            title='Sprawa do edycji dokumentów', case_type=CaseType.CYWILNA,
        )
        cls.dokument = Document.objects.create(
            case=cls.sprawa,
            title='Oryginalny tytuł',
            document_type=DocumentType.NOTATKA,
        )
        cls.wersja = DocumentVersion.objects.create(
            document=cls.dokument,
            created_by_lawyer=cls.lawyer,
            version_number=1,
            file_path='/documents/test/notatka_v1.pdf',
        )

    def _url(self):
        return reverse(
            'szkp:document_edit',
            kwargs={'case_pk': self.sprawa.pk, 'pk': self.dokument.pk},
        )

    def _redirect_url(self):
        return reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=dokumenty'

    def _valid_edit_data(self, **overrides):
        data = {
            'title': self.dokument.title,
            'document_type': self.dokument.document_type,
        }
        data.update(overrides)
        return data

    def test_get_formularz_edycji_zwraca_200(self):
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_get_form_data_wypelnione_danymi_dokumentu(self):
        r = self.client.get(self._url())
        self.assertEqual(r.context['form_data']['title'], self.dokument.title)
        self.assertEqual(r.context['form_data']['document_type'], self.dokument.document_type)

    def test_post_valid_aktualizuje_tytul(self):
        self.client.post(self._url(), self._valid_edit_data(title='Zmieniony tytuł'))
        self.dokument.refresh_from_db()
        self.assertEqual(self.dokument.title, 'Zmieniony tytuł')

    def test_post_z_plikiem_tworzy_nowa_wersje(self):
        self.client.post(self._url(), self._valid_edit_data(file=_plik('v2.pdf')))
        wersje = DocumentVersion.objects.filter(document=self.dokument).order_by('version_number')
        self.assertEqual(wersje.count(), 2)
        self.assertEqual(wersje.last().version_number, 2)

    def test_post_bez_pliku_nie_tworzy_nowej_wersji(self):
        self.client.post(self._url(), self._valid_edit_data())
        self.assertEqual(
            DocumentVersion.objects.filter(document=self.dokument).count(), 1
        )

    def test_post_redirect_na_zakladke_dokumenty(self):
        r = self.client.post(self._url(), self._valid_edit_data())
        self.assertRedirects(r, self._redirect_url())


@tag('integration')
class DocumentVersionUploadViewTest(StaffLawyerTestCase):
    """document_version_upload: dodawanie kolejnych wersji pliku do istniejącego dokumentu."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US09-VER-001',
            title='Sprawa do testów wersji', case_type=CaseType.CYWILNA,
        )
        cls.dokument = Document.objects.create(
            case=cls.sprawa,
            title='Dokument wielowersyjny',
            document_type=DocumentType.UMOWA,
        )
        cls.wersja_1 = DocumentVersion.objects.create(
            document=cls.dokument,
            created_by_lawyer=cls.lawyer,
            version_number=1,
            file_path='/documents/test/umowa_v1.pdf',
        )

    def _url(self):
        return reverse(
            'szkp:document_version_upload',
            kwargs={'case_pk': self.sprawa.pk, 'document_pk': self.dokument.pk},
        )

    def _redirect_url(self):
        return reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=dokumenty'

    def test_get_formularz_zwraca_200(self):
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_post_valid_tworzy_wersje_z_numerem_2(self):
        self.client.post(self._url(), {'file': _plik('v2.pdf')})
        nowa = DocumentVersion.objects.filter(
            document=self.dokument, version_number=2,
        ).first()
        self.assertIsNotNone(nowa, 'Powinna istnieć wersja nr 2')

    def test_post_valid_ustawia_file_path(self):
        self.client.post(self._url(), {'file': _plik('v2.pdf')})
        nowa = DocumentVersion.objects.get(document=self.dokument, version_number=2)
        self.assertTrue(nowa.file_path, 'file_path powinien być ustawiony')

    def test_post_valid_przypisuje_created_by_lawyer(self):
        self.client.post(self._url(), {'file': _plik('v2.pdf')})
        nowa = DocumentVersion.objects.get(document=self.dokument, version_number=2)
        self.assertEqual(nowa.created_by_lawyer, self.lawyer)

    def test_post_brak_pliku_zwraca_blad(self):
        r = self.client.post(self._url(), {})
        self.assertEqual(r.status_code, 200)
        self.assertIn('file', r.context['errors'])

    def test_post_redirect_na_zakladke_dokumenty(self):
        r = self.client.post(self._url(), {'file': _plik('v2.pdf')})
        self.assertRedirects(r, self._redirect_url())

    def test_trzecia_wersja_ma_numer_3(self):
        DocumentVersion.objects.create(
            document=self.dokument,
            created_by_lawyer=self.lawyer,
            version_number=2,
            file_path='/documents/test/umowa_v2.pdf',
        )
        self.client.post(self._url(), {'file': _plik('v3.pdf')})
        nowa = DocumentVersion.objects.filter(
            document=self.dokument, version_number=3,
        ).first()
        self.assertIsNotNone(nowa, 'Powinna istnieć wersja nr 3')

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])

    def test_nieprzypisany_prawnik_dostaje_403(self):
        user2 = User.objects.create_user('obcy_ver', password='pass', is_staff=False)
        self.client.force_login(user2)
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 403)
