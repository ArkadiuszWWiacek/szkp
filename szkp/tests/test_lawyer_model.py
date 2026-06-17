from django.test import SimpleTestCase, tag

from szkp.models import Lawyer


@tag('unit')
class LawyerStrTest(SimpleTestCase):
    """Lawyer.__str__: zwraca 'Imię Nazwisko'."""

    def test_str(self):
        """str(Lawyer) zwraca 'Imię Nazwisko'."""
        lawyer = Lawyer(first_name='Jan', last_name='Kowalski')
        self.assertEqual(str(lawyer), 'Jan Kowalski')
