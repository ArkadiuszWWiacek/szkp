from django.contrib.auth.models import User
from django.test import TestCase

from szkp.models import Client, ClientType, Lawyer


class StaffLawyerTestCase(TestCase):
    """Wspólny setUp dla testów widoków wymagających zalogowanego prawnika (is_staff).

    Dostarcza:
        cls.user    — User(username='prawnik', is_staff=True)
        cls.lawyer  — Lawyer(user=cls.user, first_name='Jan', last_name='Prawnik', bar_number='PL001')
        cls.klient  — Client(OSOBA_FIZYCZNA, first_name='Anna', last_name='Klientka', pesel='89010112345')
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('prawnik', password='pass', is_staff=True)
        cls.lawyer = Lawyer.objects.create(
            user=cls.user, first_name='Jan', last_name='Prawnik', bar_number='PL001',
        )
        cls.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Anna', last_name='Klientka', pesel='89010112345',
        )

    def setUp(self):
        self.client.force_login(self.user)
