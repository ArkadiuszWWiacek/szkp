from django.test import tag
from django.urls import reverse

from szkp.models import Task, TaskStatus
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class TaskChangeStatusViewTest(StaffLawyerTestCase):
    """View task_change_status: zmiana statusu zadania przez POST."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.task = Task.objects.create(
            title='Zadanie testowe',
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
            status=TaskStatus.NOWE,
        )
        cls.url = reverse('szkp:task_change_status', args=[cls.task.pk])

    def test_zmiana_statusu_na_w_toku(self):
        self.client.post(self.url, {'status': TaskStatus.W_TOKU})
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.W_TOKU)

    def test_zmiana_statusu_na_zakonczone_ustawia_completed_at(self):
        self.client.post(self.url, {'status': TaskStatus.ZAKOŃCZONE})
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.ZAKOŃCZONE)
        self.assertIsNotNone(self.task.completed_at)

    def test_niepoprawny_status_jest_ignorowany(self):
        self.client.post(self.url, {'status': 'nieistniejacy'})
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.NOWE)

    def test_archiwalne_nie_jest_akceptowane(self):
        self.client.post(self.url, {'status': 'archiwalne'})
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.NOWE)

    def test_redirect_po_zmianie(self):
        response = self.client.post(self.url, {'status': TaskStatus.W_TOKU})
        self.assertRedirects(response, reverse('szkp:my_tasks'))

    def test_redirect_do_next(self):
        response = self.client.post(
            self.url, {'status': TaskStatus.W_TOKU, 'next': '/szkp/zadania/?status=nowe'}
        )
        self.assertRedirects(response, '/szkp/zadania/?status=nowe', fetch_redirect_response=False)

    def test_get_niedozwolony(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_wymaga_logowania(self):
        self.client.logout()
        response = self.client.post(self.url, {'status': TaskStatus.W_TOKU})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/', response['Location'])

    def test_zakonczone_blokowane_gdy_podzadanie_niezakonczone(self):
        Task.objects.create(
            title='Podzadanie', assigned_lawyer=self.lawyer, created_by=self.lawyer,
            parent_task=self.task, status=TaskStatus.NOWE,
        )
        self.client.post(self.url, {'status': TaskStatus.ZAKOŃCZONE})
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.NOWE)

    def test_zakonczone_blokowane_komunikat_bledu(self):
        Task.objects.create(
            title='Podzadanie', assigned_lawyer=self.lawyer, created_by=self.lawyer,
            parent_task=self.task, status=TaskStatus.W_TOKU,
        )
        response = self.client.post(self.url, {'status': TaskStatus.ZAKOŃCZONE}, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('podzadania' in str(m) for m in messages))

    def test_zakonczone_dozwolone_gdy_wszystkie_podzadania_zakonczone(self):
        Task.objects.create(
            title='Podzadanie', assigned_lawyer=self.lawyer, created_by=self.lawyer,
            parent_task=self.task, status=TaskStatus.ZAKOŃCZONE,
        )
        self.client.post(self.url, {'status': TaskStatus.ZAKOŃCZONE})
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.ZAKOŃCZONE)
