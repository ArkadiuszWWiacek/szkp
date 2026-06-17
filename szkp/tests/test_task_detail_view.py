from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from szkp.models import Lawyer, Task, TaskPriority, TaskStatus
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class TaskDetailViewTest(StaffLawyerTestCase):
    """task_detail: wyświetlanie szczegółów zadania."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.task = Task.objects.create(
            title='Testowe zadanie',
            description='Opis testowego zadania',
            priority=TaskPriority.WYSOKA,
            status=TaskStatus.NOWE,
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
        )
        cls.subtask = Task.objects.create(
            title='Podzadanie',
            description='Opis podzadania',
            priority=TaskPriority.NORMALNA,
            status=TaskStatus.NOWE,
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
            parent_task=cls.task,
        )

    def _url(self, pk=None):
        return reverse('szkp:task_detail', kwargs={'pk': pk or self.task.pk})

    def test_zwraca_200_dla_istniejacego_zadania(self):
        """GET na istniejące zadanie zwraca kod 200."""
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_zwraca_404_dla_nieistniejacego_zadania(self):
        """GET na nieistniejące zadanie zwraca kod 404."""
        r = self.client.get(self._url(pk=99999))
        self.assertEqual(r.status_code, 404)

    def test_kontekst_zawiera_zadanie(self):
        """Kontekst szablonu zawiera obiekt wyświetlanego zadania."""
        r = self.client.get(self._url())
        self.assertEqual(r.context['task'], self.task)

    def test_szablon_pokazuje_tytul_i_opis(self):
        """Szablon wyświetla tytuł i opis zadania."""
        r = self.client.get(self._url())
        self.assertContains(r, 'Testowe zadanie')
        self.assertContains(r, 'Opis testowego zadania')

    def test_kontekst_zawiera_podzadania(self):
        """Kontekst szablonu zawiera listę podzadań przypisanych do zadania."""
        r = self.client.get(self._url())
        subtasks = list(r.context['subtasks'])
        self.assertIn(self.subtask, subtasks)

    def test_wymaga_logowania(self):
        """Widok wymaga zalogowania — niezalogowany użytkownik jest przekierowywany."""
        self.client.logout()
        r = self.client.get(self._url())
        self.assertRedirects(r, f'/accounts/login/?next={self._url()}')

    def test_szablon_pokazuje_opis_podzadania(self):
        """Szablon wyświetla opis podzadania na stronie szczegółów zadania nadrzędnego."""
        r = self.client.get(self._url())
        self.assertContains(r, 'Opis podzadania')

    def test_my_tasks_nie_pokazuje_zadania_innego_prawnika(self):
        """Lista zadań nie zawiera zadań przypisanych do innego prawnika."""
        inny_user = User.objects.create_user('innyprawnik2', password='x')
        inny_prawnik = Lawyer.objects.create(
            user=inny_user, first_name='Inny', last_name='Prawnik', bar_number='PL998',
        )
        Task.objects.create(
            title='Zadanie innego prawnika 2',
            priority=TaskPriority.NORMALNA,
            status=TaskStatus.NOWE,
            assigned_lawyer=inny_prawnik,
            created_by=inny_prawnik,
        )
        r = self.client.get(reverse('szkp:my_tasks'))
        self.assertNotContains(r, 'Zadanie innego prawnika 2')
