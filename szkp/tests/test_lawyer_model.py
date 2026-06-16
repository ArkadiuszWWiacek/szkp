from django.test import SimpleTestCase, tag

from szkp.models import Lawyer


@tag('unit')
class LawyerStrTest(SimpleTestCase):
    def test_str(self):
        lawyer = Lawyer(first_name='Jan', last_name='Kowalski')
        self.assertEqual(str(lawyer), 'Jan Kowalski')
