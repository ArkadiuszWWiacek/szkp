from django.contrib.auth.models import User
from django.test import TestCase, tag

from szkp.models import Lawyer, Task
from szkp.tests.utils import make_due


@tag('integration')
class DashboardUpcomingTasksViewTest(TestCase):
    """Dashboard: queryset upcoming_tasks w kontekście widoku."""

    @classmethod
    def setUpTestData(cls):
        cls.lawyer = Lawyer.objects.create(
            first_name='Test', last_name='Prawnik', bar_number='TST/DV/001'
        )
        cls.user = User.objects.create_user(username='test_prawnik', password='x')

    def _get_dashboard(self):
        self.client.force_login(self.user)
        return self.client.get('/szkp/pulpit/')

    def test_upcoming_tasks_zawiera_zadania_1_7_dni(self):
        task = Task.objects.create(
            title='Task w zakresie',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(3), status='nowe',
        )
        response = self._get_dashboard()
        self.assertIn(task, response.context['upcoming_tasks'])

    def test_upcoming_tasks_wyklucza_dzisiejsze(self):
        task = Task.objects.create(
            title='Task dzisiaj',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(0), status='nowe',
        )
        response = self._get_dashboard()
        self.assertNotIn(task, response.context['upcoming_tasks'])

    def test_upcoming_tasks_wyklucza_po_7_dniach(self):
        task = Task.objects.create(
            title='Task po 7 dniach',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(8), status='nowe',
        )
        response = self._get_dashboard()
        self.assertNotIn(task, response.context['upcoming_tasks'])

    def test_upcoming_tasks_wyklucza_zakonczone(self):
        task = Task.objects.create(
            title='Task zakończony',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(3), status='zakończone',
        )
        response = self._get_dashboard()
        self.assertNotIn(task, response.context['upcoming_tasks'])
