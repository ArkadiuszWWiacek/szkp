from django.db.models import RestrictedError
from django.test import SimpleTestCase, TestCase, tag

from szkp.models import Case, CaseType, Client, ClientType


@tag('unit')
class ClientCleanTest(SimpleTestCase):
    """Client.clean(): walidacja PESEL/NIP i czyszczenie pól niezgodnych z typem klienta."""

    def test_client_without_pesel_raises_validation_error(self):
        """Osoba fizyczna bez PESEL: clean() rzuca wyjątek z komunikatem 'PESEL wymagany...'."""
        client = Client(type=ClientType.OSOBA_FIZYCZNA)

        with self.assertRaises(Exception) as context:
            client.clean()

        self.assertIn('PESEL wymagany dla osoby fizycznej', str(context.exception))

    def test_client_without_nip_raises_validation_error(self):
        """Firma bez NIP: clean() rzuca wyjątek z komunikatem 'NIP wymagany...'."""
        client = Client(type=ClientType.FIRMA)

        with self.assertRaises(Exception) as context:
            client.clean()

        self.assertIn('NIP wymagany dla firmy', str(context.exception))

    def test_client_incorrect_pesel_validation(self):
        """PESEL za krótki (10 cyfr): full_clean() zgłasza błąd na polu 'pesel'."""
        client = Client(type=ClientType.OSOBA_FIZYCZNA, pesel='1234567890')

        with self.assertRaises(Exception) as context:
            client.full_clean()

        self.assertIn('pesel', str(context.exception))

    def test_client_incorrect_nip_validation(self):
        """NIP za długi (12 cyfr): full_clean() zgłasza błąd na polu 'nip'."""
        client = Client(type=ClientType.FIRMA, nip='123456789012')

        with self.assertRaises(Exception) as context:
            client.full_clean()

        self.assertIn('nip', str(context.exception))

    def test_client_type_osobafizyczna_clean(self):
        """Po clean() dla osoby fizycznej pola nip i company_name są zerowane."""
        client = Client(
            type=ClientType.OSOBA_FIZYCZNA,
            pesel='12345678901',
            nip='1234567890123',
            company_name='Test Company',
        )

        client.clean()

        self.assertEqual(client.pesel, '12345678901')
        self.assertIsNone(client.nip)
        self.assertIsNone(client.company_name)

    def test_client_type_firma_clean(self):
        """Po clean() dla firmy pole pesel jest zerowane."""
        client = Client(type=ClientType.FIRMA, nip='1234567890123', pesel='12345678901')

        client.clean()

        self.assertEqual(client.nip, '1234567890123')
        self.assertIsNone(client.pesel)


@tag('unit')
class ClientStrTest(SimpleTestCase):
    """Client.__str__: imię i nazwisko dla osoby, nazwa firmy lub fallback."""

    def test_str_individual(self):
        """str(Client osoba fizyczna) zwraca 'Imię Nazwisko'."""
        client = Client(type=ClientType.OSOBA_FIZYCZNA, first_name='Anna', last_name='Nowak')
        self.assertEqual(str(client), 'Anna Nowak')

    def test_str_firm(self):
        """str(Client firma) zwraca company_name."""
        client = Client(type=ClientType.FIRMA, company_name='Acme Sp. z o.o.')
        self.assertEqual(str(client), 'Acme Sp. z o.o.')

    def test_str_firm_brak_nazwy(self):
        """str(Client firma bez company_name) zwraca 'Firma (id=<pk>)'."""
        client = Client(type=ClientType.FIRMA, pk=5)
        self.assertEqual(str(client), 'Firma (id=5)')


@tag('integration')
class ClientPersistenceTest(TestCase):
    """Client model: usuwanie rekordów i ograniczenia bazy danych (RESTRICT)."""

    def test_usuniecie_klienta_bez_spraw_jest_mozliwe(self):
        """Klient bez przypisanych spraw może zostać usunięty."""
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Do', last_name='Usuniecia', pesel='89010112345',
        )
        pk = klient.pk
        klient.delete()
        self.assertFalse(Client.objects.filter(pk=pk).exists())

    def test_usuniecie_klienta_ze_sprawami_rzuca_restricted_error(self):
        """Próba usunięcia klienta z przypisanymi sprawami rzuca RestrictedError."""
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Powiazany', last_name='ZeSprawa', pesel='89010112345',
        )
        Case.objects.create(
            client=klient, case_number='TST-RESTRICT-001',
            title='Sprawa blokująca', case_type=CaseType.CYWILNA,
        )
        with self.assertRaises(RestrictedError):
            klient.delete()
