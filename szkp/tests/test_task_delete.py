from django.test import tag
from django.urls import reverse

from szkp.models import Task, TaskStatus
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class TaskDeleteViewTest(StaffLawyerTestCase):
    """View task_delete: usuwanie zadania z potwierdzeniem."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.task = Task.objects.create(
            title='Zadanie do usunięcia',
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
        )
        cls.url = reverse('szkp:task_delete', args=[cls.task.pk])

    def test_get_renderuje_strone_potwierdzenia(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'szkp/task_confirm_delete.html')

    def test_get_zawiera_tytul_zadania(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Zadanie do usunięcia')

    def test_post_usuwa_zadanie(self):
        self.client.post(self.url)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_post_przekierowuje_na_liste(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('szkp:my_tasks'))

    def test_post_usuwa_podzadania_kaskadowo(self):
        sub = Task.objects.create(
            title='Podzadanie',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=self.task,
        )
        self.client.post(self.url)
        self.assertFalse(Task.objects.filter(pk=sub.pk).exists())

    def test_wymaga_logowania(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/', response['Location'])

    def test_get_bez_podzadan_brak_ostrzezenia_o_kaskadzie(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'podzadań')

    def test_get_z_podzadaniami_zawiera_ostrzezenie(self):
        Task.objects.create(
            title='Podzadanie',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=self.task,
        )
        response = self.client.get(self.url)
        self.assertContains(response, 'podzadań')
