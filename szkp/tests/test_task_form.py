from django.test import tag
from django.urls import reverse

from szkp.models import Task, TaskPriority, TaskStatus
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class TaskFormParentTaskTest(StaffLawyerTestCase):
    """task_form: tworzenie podzadania z parent_task."""

    def test_post_z_parent_task_zapisuje_podzadanie(self):
        parent = Task.objects.create(
            title='Zadanie nadrzędne',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
        )
        self.client.post(reverse('szkp:task_new'), {
            'title': 'Nowe podzadanie',
            'priority': TaskPriority.NORMALNA,
            'parent_task': parent.pk,
        })
        sub = Task.objects.filter(title='Nowe podzadanie').first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.parent_task, parent)

    def test_post_bez_parent_task_tworzy_samodzielne_zadanie(self):
        self.client.post(reverse('szkp:task_new'), {
            'title': 'Samodzielne zadanie',
            'priority': TaskPriority.NORMALNA,
        })
        task = Task.objects.filter(title='Samodzielne zadanie').first()
        self.assertIsNotNone(task)
        self.assertIsNone(task.parent_task)


@tag('integration')
class TaskFormCanAddSubtaskTest(StaffLawyerTestCase):
    """task_form: can_add_subtask i parent_pk w kontekście."""

    def test_edycja_zadania_nadrzednego_can_add_subtask_true(self):
        task = Task.objects.create(
            title='Zadanie nadrzędne',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
        )
        response = self.client.get(reverse('szkp:task_edit', args=[task.pk]))
        self.assertTrue(response.context['can_add_subtask'])

    def test_edycja_podzadania_can_add_subtask_false(self):
        parent = Task.objects.create(
            title='Nadrzędne',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
        )
        sub = Task.objects.create(
            title='Podzadanie',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=parent,
        )
        response = self.client.get(reverse('szkp:task_edit', args=[sub.pk]))
        self.assertFalse(response.context['can_add_subtask'])

    def test_tworzenie_nowego_z_parent_param_przekazuje_parent_pk(self):
        parent = Task.objects.create(
            title='Nadrzędne',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
        )
        response = self.client.get(reverse('szkp:task_new') + f'?parent={parent.pk}')
        self.assertEqual(response.context['parent_pk'], str(parent.pk))

    def test_tworzenie_nowego_bez_parent_param_parent_pk_none(self):
        response = self.client.get(reverse('szkp:task_new'))
        self.assertIsNone(response.context['parent_pk'])
