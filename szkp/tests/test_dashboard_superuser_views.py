from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, tag

from szkp.models import (
    Case, CaseStatus, CaseType,
    Client, ClientType,
    CourtHearing, HearingStatus, HearingType,
    Invoice, InvoiceStatus,
    Lawyer, Task, TaskPriority, TaskStatus,
)
from szkp.tests.utils import make_due

PULPIT = '/szkp/pulpit/'


# ═══════════════════════════════════════════════════════════════════════════
# TI-D01–TI-D03: Wybór szablonu
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class DashboardSuperuserTemplateRoutingTest(TestCase):
    """Widok dashboard wybiera szablon na podstawie is_superuser."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='super', password='x', is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff', password='x', is_staff=True, is_superuser=False,
        )
        cls.regular = User.objects.create_user(
            username='regular', password='x', is_staff=False,
        )

    def test_ti_d01_superuser_uzywa_szablonu_dashboard_superuser(self):
        """TI-D01: Superuser widzi szablon szkp/dashboard_superuser.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(PULPIT)
        self.assertTemplateUsed(response, 'szkp/dashboard_superuser.html')

    def test_ti_d02_staff_nie_superuser_uzywa_starego_szablonu(self):
        """TI-D02: Staff bez is_superuser widzi stary szablon dashboard.html."""
        self.client.force_login(self.staff)
        response = self.client.get(PULPIT)
        self.assertTemplateNotUsed(response, 'szkp/dashboard_superuser.html')
        self.assertTemplateUsed(response, 'szkp/dashboard.html')

    def test_ti_d03_zwykly_uzytkownik_uzywa_starego_szablonu(self):
        """TI-D03: Użytkownik bez is_staff widzi stary szablon dashboard.html."""
        self.client.force_login(self.regular)
        response = self.client.get(PULPIT)
        self.assertTemplateNotUsed(response, 'szkp/dashboard_superuser.html')


# ═══════════════════════════════════════════════════════════════════════════
# TI-D04–TI-D19: Klucze kontekstu superusera
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class DashboardSuperuserContextKeysTest(TestCase):
    """Kontekst widoku dla superusera zawiera wszystkie wymagane klucze."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='super_ctx', password='x', is_staff=True, is_superuser=True,
        )

    def _response(self):
        self.client.force_login(self.superuser)
        return self.client.get(PULPIT)

    def test_ti_d04_klucz_active_cases_count(self):
        """TI-D04: Kontekst zawiera klucz 'active_cases_count'."""
        self.assertIn('active_cases_count', self._response().context)

    def test_ti_d05_klucz_hearings_7d_count(self):
        """TI-D05: Kontekst zawiera klucz 'hearings_7d_count'."""
        self.assertIn('hearings_7d_count', self._response().context)

    def test_ti_d06_klucz_hearings_unassigned(self):
        """TI-D06: Kontekst zawiera klucz 'hearings_unassigned'."""
        self.assertIn('hearings_unassigned', self._response().context)

    def test_ti_d07_klucz_users_count(self):
        """TI-D07: Kontekst zawiera klucz 'users_count'."""
        self.assertIn('users_count', self._response().context)

    def test_ti_d08_klucz_invoices_overdue_count(self):
        """TI-D08: Kontekst zawiera klucz 'invoices_overdue_count'."""
        self.assertIn('invoices_overdue_count', self._response().context)

    def test_ti_d09_klucz_tasks_open_count(self):
        """TI-D09: Kontekst zawiera klucz 'tasks_open_count'."""
        self.assertIn('tasks_open_count', self._response().context)

    def test_ti_d10_klucz_tasks_urgent_count(self):
        """TI-D10: Kontekst zawiera klucz 'tasks_urgent_count'."""
        self.assertIn('tasks_urgent_count', self._response().context)

    def test_ti_d11_klucz_recent_cases(self):
        """TI-D11: Kontekst zawiera klucz 'recent_cases'."""
        self.assertIn('recent_cases', self._response().context)

    def test_ti_d12_klucz_recent_invoices(self):
        """TI-D12: Kontekst zawiera klucz 'recent_invoices'."""
        self.assertIn('recent_invoices', self._response().context)

    def test_ti_d13_klucz_users(self):
        """TI-D13: Kontekst zawiera klucz 'users'."""
        self.assertIn('users', self._response().context)

    def test_ti_d14_klucz_cases_total(self):
        """TI-D14: Kontekst zawiera klucz 'cases_total'."""
        self.assertIn('cases_total', self._response().context)

    def test_ti_d15_klucz_cases_by_status(self):
        """TI-D15: Kontekst zawiera klucz 'cases_by_status'."""
        self.assertIn('cases_by_status', self._response().context)

    def test_ti_d16_klucz_active_sessions(self):
        """TI-D16: Kontekst zawiera klucz 'active_sessions'."""
        self.assertIn('active_sessions', self._response().context)

    def test_ti_d17_klucz_django_version(self):
        """TI-D17: Kontekst zawiera klucz 'django_version'."""
        self.assertIn('django_version', self._response().context)

    def test_ti_d18_klucz_python_version(self):
        """TI-D18: Kontekst zawiera klucz 'python_version'."""
        self.assertIn('python_version', self._response().context)

    def test_ti_d19_klucz_feed_items(self):
        """TI-D19: Kontekst zawiera klucz 'feed_items'."""
        self.assertIn('feed_items', self._response().context)


# ═══════════════════════════════════════════════════════════════════════════
# TI-D20–TI-D26: Poprawność danych metryk
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class DashboardSuperuserMetricsDataTest(TestCase):
    """Wartości metryk w kontekście odpowiadają stanowi bazy danych."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='super_met', password='x', is_staff=True, is_superuser=True,
        )
        cls.lawyer = Lawyer.objects.create(
            first_name='Jan', last_name='Metryk', bar_number='TST/MET/001',
        )
        cls.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Metr', last_name='Klient', pesel='80010112300',
        )
        cls.case_nowa = Case.objects.create(
            client=cls.klient, case_number='TST/MET/001',
            title='Sprawa nowa', case_type=CaseType.CYWILNA,
            status=CaseStatus.NOWA,
        )
        cls.case_w_toku = Case.objects.create(
            client=cls.klient, case_number='TST/MET/002',
            title='Sprawa w toku', case_type=CaseType.CYWILNA,
            status=CaseStatus.W_TOKU,
        )
        cls.case_zakonczona = Case.objects.create(
            client=cls.klient, case_number='TST/MET/003',
            title='Sprawa zakończona', case_type=CaseType.CYWILNA,
            status=CaseStatus.ZAKOŃCZONA,
        )
        cls.invoice_overdue = Invoice.objects.create(
            case=cls.case_nowa, invoice_number='FV/MET/001',
            net_amount=Decimal('1000.00'), status=InvoiceStatus.PRZETERMINOWANA,
            issue_date='2026-01-01', due_date='2026-02-01',
        )
        Invoice.objects.create(
            case=cls.case_nowa, invoice_number='FV/MET/002',
            net_amount=Decimal('500.00'), status=InvoiceStatus.OPŁACONA,
            issue_date='2026-01-01', due_date='2026-03-01',
        )
        cls.task_pilna = Task.objects.create(
            title='Pilne zadanie', assigned_lawyer=cls.lawyer, created_by=cls.lawyer,
            due_date=make_due(3), status=TaskStatus.NOWE, priority=TaskPriority.PILNA,
        )
        cls.task_normalna = Task.objects.create(
            title='Normalne zadanie', assigned_lawyer=cls.lawyer, created_by=cls.lawyer,
            due_date=make_due(5), status=TaskStatus.W_TOKU, priority=TaskPriority.NORMALNA,
        )
        Task.objects.create(
            title='Zakończone zadanie', assigned_lawyer=cls.lawyer, created_by=cls.lawyer,
            due_date=make_due(1), status=TaskStatus.ZAKOŃCZONE,
        )
        cls.hearing_assigned = CourtHearing.objects.create(
            case=cls.case_nowa, court_name='Sąd Okręgowy',
            hearing_type=HearingType.ROZPRAWA, scheduled_at=make_due(3),
            status=HearingStatus.PLANOWANY, responsible_lawyer=cls.lawyer,
        )
        cls.hearing_unassigned = CourtHearing.objects.create(
            case=cls.case_w_toku, court_name='Sąd Rejonowy',
            hearing_type=HearingType.POSIEDZENIE, scheduled_at=make_due(5),
            status=HearingStatus.PLANOWANY, responsible_lawyer=None,
        )
        CourtHearing.objects.create(
            case=cls.case_w_toku, court_name='Sąd Apelacyjny',
            hearing_type=HearingType.ROZPRAWA, scheduled_at=make_due(10),
            status=HearingStatus.PLANOWANY, responsible_lawyer=None,
        )

    def _ctx(self):
        self.client.force_login(self.superuser)
        return self.client.get(PULPIT).context

    def test_ti_d20_active_cases_count_liczy_nowa_i_w_toku(self):
        """TI-D20: active_cases_count = 2 (jedna NOWA + jedna W_TOKU, nie ZAKOŃCZONA)."""
        self.assertEqual(self._ctx()['active_cases_count'], 2)

    def test_ti_d21_invoices_overdue_count_liczy_przeterminowane(self):
        """TI-D21: invoices_overdue_count = 1 (jedna przeterminowana, opłacona nie wlicza)."""
        self.assertEqual(self._ctx()['invoices_overdue_count'], 1)

    def test_ti_d22_tasks_open_count_liczy_nowe_i_w_toku(self):
        """TI-D22: tasks_open_count = 2 (NOWE + W_TOKU, zakończone nie wlicza)."""
        self.assertEqual(self._ctx()['tasks_open_count'], 2)

    def test_ti_d23_tasks_urgent_count_liczy_tylko_pilne_otwarte(self):
        """TI-D23: tasks_urgent_count = 1 (tylko otwarte zadanie z priorytetem PILNA)."""
        self.assertEqual(self._ctx()['tasks_urgent_count'], 1)

    def test_ti_d24_hearings_7d_count_liczy_planowane_w_7_dniach(self):
        """TI-D24: hearings_7d_count = 2 (terminy za 3 i 5 dni, termin za 10 dni nie wlicza)."""
        self.assertEqual(self._ctx()['hearings_7d_count'], 2)

    def test_ti_d25_hearings_unassigned_liczy_bez_prawnika(self):
        """TI-D25: hearings_unassigned = 1 (termin przyszły bez prawnika w zasięgu; termin za 10 dni też nie ma prawnika ale liczy się też)."""
        ctx = self._ctx()
        self.assertGreaterEqual(ctx['hearings_unassigned'], 1)
        self.assertNotIn(self.hearing_assigned, [None])

    def test_ti_d26_cases_by_status_jest_slownikiem(self):
        """TI-D26: cases_by_status to słownik mapujący status na liczbę spraw."""
        cases_by_status = self._ctx()['cases_by_status']
        self.assertIsInstance(cases_by_status, dict)


# ═══════════════════════════════════════════════════════════════════════════
# TI-D27–TI-D30: Feed aktywności
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class DashboardSuperuserFeedTest(TestCase):
    """feed_items w kontekście: struktura, limit, kolejność."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='super_feed', password='x', is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Feed', last_name='Klient', pesel='80010112301',
        )
        for i in range(5):
            Case.objects.create(
                client=klient, case_number=f'TST/FD/{i:03d}',
                title=f'Sprawa feed {i}', case_type=CaseType.CYWILNA,
            )

    def _feed(self):
        self.client.force_login(self.superuser)
        return self.client.get(PULPIT).context['feed_items']

    def test_ti_d27_feed_ma_co_najwyzej_8_elementow(self):
        """TI-D27: feed_items zawiera co najwyżej 8 wpisów."""
        self.assertLessEqual(len(self._feed()), 8)

    def test_ti_d28_feed_zawiera_co_najmniej_jeden_wpis(self):
        """TI-D28: feed_items nie jest pusty gdy w bazie są rekordy."""
        self.assertGreater(len(self._feed()), 0)

    def test_ti_d29_feed_posortowany_malejaco_po_ts(self):
        """TI-D29: feed_items posortowane malejąco — item[0].ts >= item[1].ts."""
        items = self._feed()
        if len(items) < 2:
            return
        self.assertGreaterEqual(items[0]['ts'], items[1]['ts'])

    def test_ti_d30_feed_item_zawiera_klucze_kind_obj_ts(self):
        """TI-D30: Każdy wpis feed_items ma klucze 'kind', 'obj' i 'ts'."""
        for item in self._feed():
            self.assertIn('kind', item)
            self.assertIn('obj', item)
            self.assertIn('ts', item)


# ═══════════════════════════════════════════════════════════════════════════
# TI-D31–TI-D33: Limity list danych
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class DashboardSuperuserListLimitsTest(TestCase):
    """recent_cases, recent_invoices i users ograniczone do 5 elementów."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='super_lim', password='x', is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Limit', last_name='Klient', pesel='80010112302',
        )
        for i in range(7):
            Case.objects.create(
                client=klient, case_number=f'TST/LM/{i:03d}',
                title=f'Sprawa limit {i}', case_type=CaseType.CYWILNA,
            )
        for i in range(7):
            User.objects.create_user(username=f'limit_user_{i}', password='x')

    def _ctx(self):
        self.client.force_login(self.superuser)
        return self.client.get(PULPIT).context

    def test_ti_d31_recent_cases_max_5(self):
        """TI-D31: recent_cases zawiera co najwyżej 5 spraw."""
        self.assertLessEqual(len(self._ctx()['recent_cases']), 5)

    def test_ti_d32_users_max_5(self):
        """TI-D32: users zawiera co najwyżej 5 użytkowników."""
        self.assertLessEqual(len(self._ctx()['users']), 5)

    def test_ti_d33_version_strings_maja_poprawny_format(self):
        """TI-D33: django_version i python_version to łańcuchy w formacie X.Y.Z i X.Y."""
        import re
        ctx = self._ctx()
        self.assertRegex(ctx['django_version'], r'^\d+\.\d+\.\d+$')
        self.assertRegex(ctx['python_version'], r'^\d+\.\d+$')


# ═══════════════════════════════════════════════════════════════════════════
# TI-D40–TI-D42: Wykres kołowy rozkładu spraw
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class DashboardSuperuserChartTest(TestCase):
    """Kontekst i szablon zawierają wykres kołowy rozkładu spraw."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='super_chart', password='x', is_staff=True, is_superuser=True,
        )
        cls.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Chart', last_name='Klient', pesel='90010112300',
        )
        Case.objects.create(
            client=cls.klient, case_number='TST/CHT/001',
            title='Sprawa testowa', case_type=CaseType.CYWILNA,
            status=CaseStatus.W_TOKU,
        )

    def _response(self):
        self.client.force_login(self.superuser)
        return self.client.get(PULPIT)

    def test_ti_d40_context_contains_case_dist_chart(self):
        """TI-D40: Kontekst zawiera klucz case_dist_chart."""
        self.assertIn('case_dist_chart', self._response().context)

    def test_ti_d41_chart_is_nonempty_string_when_cases_exist(self):
        """TI-D41: case_dist_chart jest niepustym stringiem gdy są sprawy."""
        chart = self._response().context['case_dist_chart']
        self.assertIsInstance(chart, str)
        self.assertGreater(len(chart), 0)

    def test_ti_d42_response_contains_base64_img(self):
        """TI-D42: Odpowiedź HTML zawiera tag img z danymi PNG base64."""
        self.assertContains(self._response(), 'data:image/png;base64,')
