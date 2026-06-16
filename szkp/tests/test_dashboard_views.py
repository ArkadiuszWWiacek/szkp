from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.utils import timezone

from szkp.models import (
    Case, CaseStatus, CaseType,
    Client, ClientType,
    CourtHearing, HearingStatus, HearingType,
    Lawyer, CaseLawyer, CaseLawyerRole,
    Task, TaskStatus,
)
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

    def test_upcoming_tasks_zawiera_w_toku(self):
        """TC-R03-07: zadanie W_TOKU w ciągu 1-7 dni pojawia się w upcoming_tasks."""
        task = Task.objects.create(
            title='Task W_TOKU w zakresie',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(3), status=TaskStatus.W_TOKU,
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


@tag('integration')
class DashboardUpcomingHearingsViewTest(TestCase):
    """Dashboard: queryset upcoming_hearings filtrowany po statusie PLANOWANY i dacie."""

    @classmethod
    def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username='admin_hearings', password='x', is_staff=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA, first_name='Jan', last_name='Test',
        )
        cls.case = Case.objects.create(
            case_number='TEST/HRG/001', title='Sprawa testowa',
            client=klient, case_type=CaseType.CYWILNA,
        )

    def _get_dashboard(self):
        self.client.force_login(self.staff_user)
        return self.client.get('/szkp/pulpit/')

    def test_upcoming_hearings_zawiera_planowane_przyszle(self):
        """TC-R03-01: termin PLANOWANY jutro pojawia się w upcoming_hearings."""
        hearing = CourtHearing.objects.create(
            case=self.case, court_name='Sąd Okręgowy',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=make_due(1),
            status=HearingStatus.PLANOWANY,
        )
        response = self._get_dashboard()
        self.assertIn(hearing, response.context['upcoming_hearings'])

    def test_upcoming_hearings_wyklucza_odbyte(self):
        """TC-R03-02: termin ODBYTY jutro nie pojawia się w upcoming_hearings."""
        hearing = CourtHearing.objects.create(
            case=self.case, court_name='Sąd Okręgowy',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=make_due(1),
            status=HearingStatus.ODBYTY,
        )
        response = self._get_dashboard()
        self.assertNotIn(hearing, response.context['upcoming_hearings'])

    def test_upcoming_hearings_wyklucza_przeszle_planowane(self):
        """TC-R03-03: termin PLANOWANY wczoraj nie pojawia się w upcoming_hearings."""
        hearing = CourtHearing.objects.create(
            case=self.case, court_name='Sąd Okręgowy',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=make_due(-1),
            status=HearingStatus.PLANOWANY,
        )
        response = self._get_dashboard()
        self.assertNotIn(hearing, response.context['upcoming_hearings'])


@tag('integration')
class DashboardTodayTasksViewTest(TestCase):
    """Dashboard: queryset today_tasks filtrowany po statusie NOWE i W_TOKU."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test_today_tasks', password='x')
        cls.lawyer = Lawyer.objects.create(
            first_name='Test', last_name='Today',
            bar_number='TST/TD/001', user=cls.user,
        )

    def _get_dashboard(self):
        self.client.force_login(self.user)
        return self.client.get('/szkp/pulpit/')

    def test_today_tasks_zawiera_nowe_na_dzis(self):
        """TC-R03-04: zadanie NOWE na dziś pojawia się w today_tasks."""
        task = Task.objects.create(
            title='Nowe na dziś',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(0), status=TaskStatus.NOWE,
        )
        response = self._get_dashboard()
        self.assertIn(task, response.context['today_tasks'])

    def test_today_tasks_zawiera_w_toku_na_dzis(self):
        """TC-R03-05: zadanie W_TOKU na dziś pojawia się w today_tasks."""
        task = Task.objects.create(
            title='W toku na dziś',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(0), status=TaskStatus.W_TOKU,
        )
        response = self._get_dashboard()
        self.assertIn(task, response.context['today_tasks'])

    def test_today_tasks_wyklucza_zakonczone_na_dzis(self):
        """TC-R03-06: zadanie ZAKOŃCZONE na dziś nie pojawia się w today_tasks."""
        task = Task.objects.create(
            title='Zakończone na dziś',
            assigned_lawyer=self.lawyer, created_by=self.lawyer,
            due_date=make_due(0), status=TaskStatus.ZAKOŃCZONE,
        )
        response = self._get_dashboard()
        self.assertNotIn(task, response.context['today_tasks'])
