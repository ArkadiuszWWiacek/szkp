from django.test import TestCase
from szkp.models.Client import Client, ClientType

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