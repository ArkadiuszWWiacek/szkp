from django.test import tag
from django.urls import reverse

from szkp.models import Case, CaseLawyer, CaseLawyerRole, CaseType, Task, TaskPriority, TaskStatus
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class TaskFormParentTaskTest(StaffLawyerTestCase):
    """task_form: tworzenie podzadania z parent_task."""

    def test_post_z_parent_task_zapisuje_podzadanie(self):
        """POST z polem parent_task tworzy zadanie jako podzadanie wskazanego zadania nadrzędnego."""
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
        """POST bez pola parent_task tworzy samodzielne zadanie bez zadania nadrzędnego."""
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
        """Edycja zadania nadrzędnego przekazuje can_add_subtask=True do kontekstu."""
        task = Task.objects.create(
            title='Zadanie nadrzędne',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
        )
        response = self.client.get(reverse('szkp:task_edit', args=[task.pk]))
        self.assertTrue(response.context['can_add_subtask'])

    def test_edycja_podzadania_can_add_subtask_false(self):
        """Edycja podzadania przekazuje can_add_subtask=False do kontekstu."""
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
        """Parametr ?parent= w URL przekazuje parent_pk do kontekstu formularza tworzenia zadania."""
        parent = Task.objects.create(
            title='Nadrzędne',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
        )
        response = self.client.get(reverse('szkp:task_new') + f'?parent={parent.pk}')
        self.assertEqual(response.context['parent_pk'], str(parent.pk))

    def test_tworzenie_nowego_bez_parent_param_parent_pk_none(self):
        """Brak parametru ?parent= w URL powoduje, że parent_pk w kontekście ma wartość None."""
        response = self.client.get(reverse('szkp:task_new'))
        self.assertIsNone(response.context['parent_pk'])


@tag('integration')
class TaskFormCaseTaskTest(StaffLawyerTestCase):
    """task_form: tworzenie zadania powiązanego ze sprawą przez case_task_new."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-TASK-CASE-001',
            title='Sprawa do testów zadań', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=cls.sprawa, lawyer=cls.lawyer, role=CaseLawyerRole.PROWADZACY,
        )

    def _url_new(self):
        return reverse('szkp:case_task_new', kwargs={'case_pk': self.sprawa.pk})

    def test_get_zwraca_200_i_case_w_kontekscie(self):
        """GET na formularz nowego zadania sprawy zwraca kod 200 i sprawę w kontekście."""
        response = self.client.get(self._url_new())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['case'], self.sprawa)

    def test_post_ustawia_case_na_zadaniu(self):
        """POST na formularz zadania sprawy przypisuje sprawę do nowo utworzonego zadania."""
        self.client.post(self._url_new(), {
            'title': 'Zadanie sprawy',
            'priority': TaskPriority.NORMALNA,
        })
        task = Task.objects.filter(title='Zadanie sprawy').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.case, self.sprawa)

    def test_post_przekierowuje_na_szczegoly_sprawy(self):
        """Po zapisaniu zadania sprawy widok przekierowuje na zakładkę zadań w szczegółach sprawy."""
        response = self.client.post(self._url_new(), {
            'title': 'Zadanie przekierowania',
            'priority': TaskPriority.NORMALNA,
        })
        self.assertRedirects(
            response,
            reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=zadania',
        )
