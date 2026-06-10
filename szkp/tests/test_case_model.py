from django.test import TestCase
from szkp.models import Case, Client


class CaseModelTest(TestCase):
    def test_case_str(self):
        client = Client.objects.create(pesel="12345678901", email="test@example.com")
        case = Case.objects.create(
            client=client, case_number="CASE-001", title="Test Case"
        )
        self.assertEqual(str(case), "CASE-001 - Test Case")
