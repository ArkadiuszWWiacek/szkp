from django.test import tag
from django.urls import reverse
from django.utils import timezone

from szkp.models import Task, TaskPriority, TaskStatus
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class TaskListFiltersTest(StaffLawyerTestCase):
    """my_tasks: filtry okresu (dziś, tydzień, przeterminowane)."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        today = timezone.localdate()
        cls.task_wczoraj = Task.objects.create(
            title='Zadanie wczoraj',
            priority=TaskPriority.NORMALNA,
            status=TaskStatus.NOWE,
            due_date=timezone.make_aware(
                timezone.datetime.combine(today - timezone.timedelta(days=1),
                                          timezone.datetime.min.time())
            ),
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
        )
        cls.task_dzisiaj = Task.objects.create(
            title='Zadanie dzisiaj',
            priority=TaskPriority.NORMALNA,
            status=TaskStatus.NOWE,
            due_date=timezone.make_aware(
                timezone.datetime.combine(today, timezone.datetime.min.time())
            ),
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
        )
        cls.task_zakonczone_przeterminowane = Task.objects.create(
            title='Zadanie zakończone przeterminowane',
            priority=TaskPriority.NORMALNA,
            status=TaskStatus.ZAKOŃCZONE,
            due_date=timezone.make_aware(
                timezone.datetime.combine(today - timezone.timedelta(days=2),
                                          timezone.datetime.min.time())
            ),
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
        )

    def _url(self, **params):
        url = reverse('szkp:my_tasks')
        if params:
            url += '?' + '&'.join(f'{k}={v}' for k, v in params.items())
        return url

    def _titles(self, r):
        return [t.title for t in r.context['tasks']]

    def test_filtr_overdue_zwraca_tylko_przeterminowane_niezakonczone(self):
        r = self.client.get(self._url(period='overdue'))
        titles = self._titles(r)
        self.assertIn('Zadanie wczoraj', titles)
        self.assertNotIn('Zadanie dzisiaj', titles)
        self.assertNotIn('Zadanie zakończone przeterminowane', titles)

    def test_filtr_today_nie_zwraca_przeterminowanych(self):
        r = self.client.get(self._url(period='today'))
        titles = self._titles(r)
        self.assertIn('Zadanie dzisiaj', titles)
        self.assertNotIn('Zadanie wczoraj', titles)

    def test_kontekst_zawiera_period_filter_overdue(self):
        r = self.client.get(self._url(period='overdue'))
        self.assertEqual(r.context['period_filter'], 'overdue')
