from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from szkp.models import Case, CaseType, Client, ClientType


@tag('integration')
class ClientListSearchTest(TestCase):
    """client_list: filtrowanie querysetem po ?q="""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pracownik', password='pass')
        Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Jan', last_name='Kowalski', pesel='89010112345',
        )
        Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Anna', last_name='Nowak', pesel='89010112346',
        )
        Client.objects.create(
            type=ClientType.FIRMA,
            company_name='ACME Sp. z o.o.', nip='5250012345',
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_brak_q_zwraca_wszystkich_klientow(self):
        r = self.client.get(reverse('szkp:client_list'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['page_obj'].paginator.count, 3)

    def test_filtr_po_nazwisku(self):
        r = self.client.get(reverse('szkp:client_list'), {'q': 'Kowalski'})
        results = list(r.context['page_obj'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].last_name, 'Kowalski')

    def test_filtr_po_imieniu(self):
        r = self.client.get(reverse('szkp:client_list'), {'q': 'Anna'})
        self.assertEqual(len(list(r.context['page_obj'])), 1)

    def test_filtr_po_nazwie_firmy(self):
        r = self.client.get(reverse('szkp:client_list'), {'q': 'ACME'})
        results = list(r.context['page_obj'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].company_name, 'ACME Sp. z o.o.')

    def test_filtr_bez_wynikow_zwraca_pusta_strone(self):
        r = self.client.get(reverse('szkp:client_list'), {'q': 'NieMaKogos9999'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['page_obj'].paginator.count, 0)

    def test_filtr_q_przekazany_do_kontekstu(self):
        r = self.client.get(reverse('szkp:client_list'), {'q': 'test'})
        self.assertEqual(r.context['q'], 'test')

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(reverse('szkp:client_list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])


@tag('integration')
class ClientFormValidationTest(TestCase):
    """client_form: walidacja POST — brak PESEL/NIP, poprawne tworzenie, edycja."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pracownik', password='pass')

    def setUp(self):
        self.client.force_login(self.user)

    def _post_new(self, data):
        return self.client.post(reverse('szkp:client_new'), data)

    # --- walidacja: osoba fizyczna

    def test_brak_pesel_zwraca_blad_w_kontekscie(self):
        r = self._post_new({'type': 'osobafizyczna', 'first_name': 'Jan', 'last_name': 'Test'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('pesel', r.context['errors'])

    def test_niepoprawny_pesel_zwraca_blad(self):
        r = self._post_new({
            'type': 'osobafizyczna', 'first_name': 'Jan',
            'last_name': 'Test', 'pesel': '123',
        })
        self.assertIn('pesel', r.context['errors'])

    def test_brak_imienia_zwraca_blad(self):
        r = self._post_new({
            'type': 'osobafizyczna', 'last_name': 'Test', 'pesel': '89010112345',
        })
        self.assertIn('first_name', r.context['errors'])

    def test_brak_nazwiska_zwraca_blad(self):
        r = self._post_new({
            'type': 'osobafizyczna', 'first_name': 'Jan', 'pesel': '89010112345',
        })
        self.assertIn('last_name', r.context['errors'])

    # --- walidacja: firma

    def test_brak_nip_zwraca_blad_w_kontekscie(self):
        r = self._post_new({'type': 'firma', 'company_name': 'Test Sp. z o.o.'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('nip', r.context['errors'])

    def test_brak_nazwy_firmy_zwraca_blad(self):
        r = self._post_new({'type': 'firma', 'nip': '5250012345'})
        self.assertIn('company_name', r.context['errors'])

    def test_brak_typu_zwraca_blad(self):
        r = self._post_new({'first_name': 'Jan'})
        self.assertIn('type', r.context['errors'])

    # --- poprawne tworzenie

    def test_poprawny_post_osobafizyczna_tworzy_klienta(self):
        r = self._post_new({
            'type': 'osobafizyczna', 'first_name': 'Jan',
            'last_name': 'Kowalski', 'pesel': '89010112345',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Client.objects.filter(last_name='Kowalski').exists())

    def test_poprawny_post_firma_tworzy_klienta(self):
        r = self._post_new({'type': 'firma', 'company_name': 'ACME Sp. z o.o.', 'nip': '5250012345'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Client.objects.filter(company_name='ACME Sp. z o.o.').exists())

    def test_po_utworzeniu_redirect_do_listy(self):
        r = self._post_new({
            'type': 'osobafizyczna', 'first_name': 'Jan',
            'last_name': 'Redirect', 'pesel': '89010112345',
        })
        self.assertRedirects(r, reverse('szkp:client_list'))

    # --- edycja

    def test_edycja_klienta_aktualizuje_dane(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Stare', last_name='Nazwisko', pesel='89010112345',
        )
        r = self.client.post(
            reverse('szkp:client_edit', kwargs={'pk': klient.pk}),
            {'type': 'osobafizyczna', 'first_name': 'Nowe', 'last_name': 'Zmienione', 'pesel': '89010112345'},
        )
        self.assertEqual(r.status_code, 302)
        klient.refresh_from_db()
        self.assertEqual(klient.last_name, 'Zmienione')

    def test_blad_edycji_zwraca_forme_z_bledami(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Stare', last_name='Nazwisko', pesel='89010112345',
        )
        r = self.client.post(
            reverse('szkp:client_edit', kwargs={'pk': klient.pk}),
            {'type': 'osobafizyczna', 'first_name': '', 'last_name': 'Test'},
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('first_name', r.context['errors'])


@tag('integration')
class ClientDeleteViewTest(TestCase):
    """client_delete: strona potwierdzenia i usuwanie."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pracownik', password='pass')

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_strona_potwierdzenia_zwraca_200(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Do', last_name='Usuniecia', pesel='89010112345',
        )
        r = self.client.get(reverse('szkp:client_delete', kwargs={'pk': klient.pk}))
        self.assertEqual(r.status_code, 200)

    def test_post_usuwa_klienta_bez_spraw(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Do', last_name='Usuniecia', pesel='89010112345',
        )
        pk = klient.pk
        r = self.client.post(reverse('szkp:client_delete', kwargs={'pk': pk}))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Client.objects.filter(pk=pk).exists())

    def test_post_z_przypisana_sprawa_blokuje_usuniecie(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Powiazany', last_name='ZeSprawa', pesel='89010112345',
        )
        Case.objects.create(
            client=klient, case_number='TST-US04-DEL-001',
            title='Sprawa blokująca', case_type=CaseType.CYWILNA,
        )
        r = self.client.post(reverse('szkp:client_delete', kwargs={'pk': klient.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Client.objects.filter(pk=klient.pk).exists())

    def test_po_usunieciu_redirect_do_listy(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Do', last_name='Redirect', pesel='89010112345',
        )
        r = self.client.post(reverse('szkp:client_delete', kwargs={'pk': klient.pk}))
        self.assertRedirects(r, reverse('szkp:client_list'))
