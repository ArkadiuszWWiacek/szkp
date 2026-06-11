from django.db.models import RestrictedError
from django.test import TestCase, tag

from szkp.models import Case, CaseType, Client, ClientType

@tag('unit')
class ClientModelTest(TestCase):
    def test_client_without_pesel_raises_validation_error(self):
        client = Client(type=ClientType.OSOBA_FIZYCZNA)
        
        with self.assertRaises(Exception) as context:
            client.clean()
            
        self.assertIn('PESEL wymagany dla osoby fizycznej', str(context.exception))
    
    def test_client_without_nip_raises_validation_error(self):
        client = Client(type=ClientType.FIRMA)
        
        with self.assertRaises(Exception) as context:
            client.clean()
            
        self.assertIn('NIP wymagany dla firmy', str(context.exception))
        
    def test_client_incorrect_pesel_validation(self):
        client = Client(type=ClientType.OSOBA_FIZYCZNA, pesel="1234567890")  # Invalid PESEL
        
        with self.assertRaises(Exception) as context:
            client.full_clean()
            
        self.assertIn('pesel', str(context.exception))

    def test_client_incorrect_nip_validation(self):
        client = Client(type=ClientType.FIRMA, nip="123456789012")  # Invalid NIP

        with self.assertRaises(Exception) as context:
            client.full_clean()

        self.assertIn('nip', str(context.exception))

    def test_client_type_osobafizyczna_clean(self):
        client = Client(type=ClientType.OSOBA_FIZYCZNA, pesel="12345678901", nip="1234567890123", company_name="Test Company")
        
        client.clean()
        
        self.assertEqual(client.pesel, "12345678901")
        self.assertEqual(client.nip, None)
        self.assertEqual(client.company_name, None)
        
    def test_client_type_firma_clean(self):
        client = Client(type=ClientType.FIRMA, nip="1234567890123", pesel="12345678901")

        client.clean()

        self.assertEqual(client.nip, "1234567890123")
        self.assertEqual(client.pesel, None)

    def test_usuniecie_klienta_bez_spraw_jest_mozliwe(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Do', last_name='Usuniecia', pesel='89010112345',
        )
        pk = klient.pk
        klient.delete()
        self.assertFalse(Client.objects.filter(pk=pk).exists())

    def test_usuniecie_klienta_ze_sprawami_rzuca_restricted_error(self):
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