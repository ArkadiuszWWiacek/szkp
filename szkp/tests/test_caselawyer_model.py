from django.test import SimpleTestCase, tag

from szkp.models import Case, CaseLawyer, CaseLawyerRole, Lawyer


@tag('unit')
class CaseLawyerStrTest(SimpleTestCase):
    def test_str(self):
        case = Case(case_number='1/2024/CIV', title='Sprawa testowa')
        lawyer = Lawyer(first_name='Jan', last_name='Kowalski')
        cl = CaseLawyer(case=case, lawyer=lawyer, role=CaseLawyerRole.ASYSTENT)
        self.assertEqual(str(cl), '1/2024/CIV - Sprawa testowa — Jan Kowalski (Asystent)')
