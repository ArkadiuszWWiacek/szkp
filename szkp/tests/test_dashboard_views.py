from django.contrib.auth.models import User
from django.test import TestCase, tag

from szkp.models import Case, Client, ClientType, Lawyer, CaseLawyer, CaseLawyerRole, Task
from szkp.tests.utils import make_due


@tag('integration')
class DashboardUpcomingTasksViewTest(TestCase):
    """Dashboard: queryset upcoming_tasks filtrowany po prawniku."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test_prawnik', password='x')
        cls.lawyer = Lawyer.objects.create(
            first_name='Test', last_name='Prawnik',
            bar_number='TST/DV/001', user=cls.user,
        )

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


@tag('integration')
class DashboardIzolacjaPrawnikaTest(TestCase):
    """Dashboard: nie-staff widzi tylko swoje dane."""

    @classmethod
    def setUpTestData(cls):
        cls.user_a = User.objects.create_user(username='prawnik_a', password='x')
        cls.lawyer_a = Lawyer.objects.create(
            first_name='Prawnik', last_name='A',
            bar_number='TST/A/001', user=cls.user_a,
        )
        cls.user_b = User.objects.create_user(username='prawnik_b', password='x')
        cls.lawyer_b = Lawyer.objects.create(
            first_name='Prawnik', last_name='B',
            bar_number='TST/B/001', user=cls.user_b,
        )
        cls.staff_user = User.objects.create_user(username='admin', password='x', is_staff=True)

        cls.task_a = Task.objects.create(
            title='Zadanie A',
            assigned_lawyer=cls.lawyer_a, created_by=cls.lawyer_a,
            due_date=make_due(3), status='nowe',
        )
        cls.task_b = Task.objects.create(
            title='Zadanie B',
            assigned_lawyer=cls.lawyer_b, created_by=cls.lawyer_b,
            due_date=make_due(3), status='nowe',
        )

    def _get_dashboard(self, user):
        self.client.force_login(user)
        return self.client.get('/szkp/pulpit/')

    def test_prawnik_widzi_swoje_zadanie(self):
        response = self._get_dashboard(self.user_a)
        self.assertIn(self.task_a, response.context['upcoming_tasks'])

    def test_prawnik_nie_widzi_cudzego_zadania(self):
        response = self._get_dashboard(self.user_a)
        self.assertNotIn(self.task_b, response.context['upcoming_tasks'])

    def test_staff_widzi_zadania_wszystkich(self):
        response = self._get_dashboard(self.staff_user)
        self.assertIn(self.task_a, response.context['upcoming_tasks'])
        self.assertIn(self.task_b, response.context['upcoming_tasks'])


@tag('integration')
class DashboardBezProfiluPrawnikaTest(TestCase):
    """Dashboard: użytkownik bez profilu prawnika widzi puste dane."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='bez_prawnika', password='x')
        cls.lawyer = Lawyer.objects.create(
            first_name='Inny', last_name='Prawnik', bar_number='TST/X/001',
        )
        Task.objects.create(
            title='Czyjeś zadanie',
            assigned_lawyer=cls.lawyer, created_by=cls.lawyer,
            due_date=make_due(3), status='nowe',
        )

    def test_brak_profilu_prawnika_daje_puste_upcoming_tasks(self):
        self.client.force_login(self.user)
        response = self.client.get('/szkp/pulpit/')
        self.assertEqual(list(response.context['upcoming_tasks']), [])

    def test_brak_profilu_prawnika_daje_zerowe_liczniki_spraw(self):
        self.client.force_login(self.user)
        response = self.client.get('/szkp/pulpit/')
        self.assertEqual(response.context['total_cases'], 0)
