from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase, tag

from szkp.models import Case, CaseStatus, CaseType, Client, ClientType


@tag('unit')
class CaseModelTest(SimpleTestCase):
    """Case model: __str__ i wartości domyślne — bez zapisu do DB."""

    def test_case_str(self):
        """str(Case) zwraca 'case_number - title'."""
        case = Case(case_number='CASE-001', title='Test Case')
        self.assertEqual(str(case), 'CASE-001 - Test Case')

    def test_default_status_is_nowa(self):
        """Domyślny status nowej sprawy to CaseStatus.NOWA."""
        self.assertEqual(Case().status, CaseStatus.NOWA)


@tag('integration')
class CaseModelPersistenceTest(TestCase):
    """Case model: unikalność i ograniczenia bazy danych."""

    def test_case_number_must_be_unique(self):
        """Duplikat case_number rzuca IntegrityError."""
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
