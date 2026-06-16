from unittest.mock import patch

from django.db import models as django_models
from django.test import SimpleTestCase, tag

from szkp.models import Task, TaskPriority, TaskStatus
from szkp.tests.base import StaffLawyerTestCase


@tag('unit')
class TaskDefaultsTest(SimpleTestCase):
    """Task model: wartości domyślne pól — bez zapisu do DB."""

    def test_domyslny_status_to_nowe(self):
        self.assertEqual(Task().status, TaskStatus.NOWE)

    def test_domyslny_priorytet_to_normalna(self):
        self.assertEqual(Task().priority, TaskPriority.NORMALNA)

    def test_completed_at_domyslnie_none(self):
        self.assertIsNone(Task().completed_at)

    def test_zadanie_moze_istniec_bez_sprawy(self):
        self.assertIsNone(Task(case=None).case)

    def test_parent_task_opcjonalne(self):
        self.assertIsNone(Task(parent_task=None).parent_task)


@tag('unit')
class TaskStrTest(SimpleTestCase):
    def test_str(self):
        task = Task(title='Przygotować pismo procesowe')
        self.assertEqual(str(task), 'Przygotować pismo procesowe')


@tag('integration')
class TaskSubtaskTest(StaffLawyerTestCase):
    """Task model: podzadania i relacja parent_task."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.parent = Task.objects.create(
            title='Zadanie nadrzędne',
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
        )
        cls.child = Task.objects.create(
            title='Podzadanie',
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
            parent_task=cls.parent,
        )

    def test_podzadanie_dostepne_przez_task_set(self):
        self.assertIn(self.child, self.parent.task_set.all())

    def test_podzadanie_ma_rodzica(self):
        self.assertEqual(self.child.parent_task, self.parent)


@tag('unit')
class TaskStatusBehaviorTest(SimpleTestCase):
    """Task model: logika save() — ustawianie completed_at."""

    def test_zmiana_statusu_na_zakonczone_ustawia_completed_at(self):
        task = Task(title='Do zakończenia')
        task.status = TaskStatus.ZAKOŃCZONE
        with patch.object(django_models.Model, 'save'):
            task.save()
        self.assertIsNotNone(task.completed_at)


@tag('integration')
class TaskHasUnfinishedSubtasksTest(StaffLawyerTestCase):
    """Task.has_unfinished_subtasks: wykrywa niezakończone podzadania."""

    def _make_task(self, **kwargs):
        return Task.objects.create(
            title='Zadanie', assigned_lawyer=self.lawyer, created_by=self.lawyer, **kwargs
        )

    def test_bez_podzadan_zwraca_false(self):
        parent = self._make_task()
        self.assertFalse(parent.has_unfinished_subtasks)

    def test_z_podzadaniem_nowe_zwraca_true(self):
        parent = self._make_task()
        self._make_task(parent_task=parent, status=TaskStatus.NOWE)
        self.assertTrue(parent.has_unfinished_subtasks)

    def test_z_podzadaniem_w_toku_zwraca_true(self):
        parent = self._make_task()
        self._make_task(parent_task=parent, status=TaskStatus.W_TOKU)
        self.assertTrue(parent.has_unfinished_subtasks)

    def test_z_podzadaniem_zakonczone_zwraca_false(self):
        parent = self._make_task()
        self._make_task(parent_task=parent, status=TaskStatus.ZAKOŃCZONE)
        self.assertFalse(parent.has_unfinished_subtasks)

    def test_mieszane_podzadania_zwraca_true(self):
        parent = self._make_task()
        self._make_task(parent_task=parent, status=TaskStatus.ZAKOŃCZONE)
        self._make_task(parent_task=parent, status=TaskStatus.NOWE)
        self.assertTrue(parent.has_unfinished_subtasks)
