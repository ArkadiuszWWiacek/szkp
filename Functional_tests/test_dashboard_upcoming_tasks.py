from django.contrib.auth.models import User
from django.test import tag

from .base import SzkpSeleniumTestCase
from szkp.models import Lawyer, Task
from szkp.tests.utils import make_due


@tag('functional')
class DashboardUpcomingTasksTest(SzkpSeleniumTestCase):
    """Dashboard: podsekcja 'Nadchodzące 7 dni' w karcie Moje zadania."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.lawyer = Lawyer.objects.create(
            first_name='Test', last_name='Prawnik', bar_number='TST/DU/001'
        )
        self.user = User.objects.create_user(
            username='test_prawnik', password='testpass123',
            first_name='Test', last_name='Prawnik',
        )
        self.lawyer.user = self.user
        self.lawyer.save()

        self.task_today = Task.objects.create(
            title='Zadanie dzisiejsze testowe',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(0), status='nowe',
        )
        self.task_tomorrow = Task.objects.create(
            title='Zadanie jutrzejsze testowe',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(1), status='nowe',
        )
        self.task_day7 = Task.objects.create(
            title='Zadanie siodmego dnia testowe',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(7), status='w_toku',
        )
        self.task_day8 = Task.objects.create(
            title='Zadanie osmego dnia testowe',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(8), status='nowe',
        )
        self.task_done = Task.objects.create(
            title='Zadanie zakonczone testowe',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(2), status='zakończone',
        )

        self._zaloguj_przez_orm(self.user)
        self.selenium.get(self.live_server_url + '/szkp/pulpit/')

    @tag('smoke')
    def test_sekcja_nadchodzace_wyswietla_sie(self):
        """Na pulpicie widoczna jest podsekcja 'Nadchodzące'."""
        self.assertIn('Nadchodzące', self.selenium.page_source)

    def test_zadanie_jutro_pojawia_sie_w_nadchodzacych(self):
        """Zadanie z terminem jutro jest widoczne na pulpicie."""
        self.assertIn(self.task_tomorrow.title, self.selenium.page_source)

    def test_zadanie_za_7_dni_pojawia_sie_w_nadchodzacych(self):
        """Zadanie z terminem za 7 dni jest widoczne na pulpicie."""
        self.assertIn(self.task_day7.title, self.selenium.page_source)

    def test_zadanie_za_8_dni_nie_pojawia_sie(self):
        """Zadanie z terminem za 8 dni nie jest widoczne na pulpicie."""
        self.assertNotIn(self.task_day8.title, self.selenium.page_source)

    def test_zakonczone_zadanie_nie_pojawia_sie(self):
        """Ukończone zadanie nie pojawia się w sekcji nadchodzących."""
        self.assertNotIn(self.task_done.title, self.selenium.page_source)
