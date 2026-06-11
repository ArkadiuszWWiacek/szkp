from django.db import IntegrityError
from django.test import TestCase, tag

from szkp.models import Case, CaseStatus, CaseType, Client, ClientType


@tag('unit')
class CaseModelTest(TestCase):
    def test_case_str(self):
        client = Client.objects.create(pesel="12345678901", email="test@example.com")
        case = Case.objects.create(
            client=client, case_number="CASE-001", title="Test Case"
        )
        self.assertEqual(str(case), "CASE-001 - Test Case")

    def test_default_status_is_nowa(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Jan', last_name='Test', pesel='89010112345',
        )
        case = Case.objects.create(
            client=klient, case_number='TST-DEF-001',
            title='Test domyślnego statusu', case_type=CaseType.CYWILNA,
        )
        self.assertEqual(case.status, CaseStatus.NOWA)

    def test_case_number_must_be_unique(self):
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Jan', last_name='Test', pesel='89010112345',
        )
        Case.objects.create(
            client=klient, case_number='TST-DUP-001',
            title='Pierwsza', case_type=CaseType.CYWILNA,
        )
        with self.assertRaises(IntegrityError):
            Case.objects.create(
                client=klient, case_number='TST-DUP-001',
                title='Duplikat', case_type=CaseType.CYWILNA,
            )
