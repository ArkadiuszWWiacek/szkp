from datetime import timedelta

from django.test import TestCase, tag
from django.utils import timezone

from szkp.forms import TaskForm, TaskFormSU
from szkp.models import (
    Client, ClientType, Case, CaseType, CaseLawyer, CaseLawyerRole, Lawyer, Task,
)


def _make_case_with_lawyers(n=2):
    klient = Client.objects.create(
        type=ClientType.OSOBA_FIZYCZNA,
        first_name='Anna', last_name='Klientka', pesel='89010112345',
    )
    case = Case.objects.create(
        client=klient, case_number='TASK-ASSIGN-001', title='Sprawa', case_type=CaseType.CYWILNA,
    )
    lawyers = []
    for i in range(n):
        l = Lawyer.objects.create(
            first_name=f'Prawnik{i}', last_name=f'Testowy{i}', bar_number=f'PL{200 + i:03d}', activeflag=True,
        )
        CaseLawyer.objects.create(case=case, lawyer=l, role=CaseLawyerRole.ASYSTENT)
        lawyers.append(l)
    return case, lawyers


def _form_data(lawyer_pk=None):
    return {
        'title': 'Testowe zadanie',
        'description': '',
        'priority': '',
        'status': '',
        'due_date': '',
        'assigned_lawyer': lawyer_pk or '',
    }


@tag('unit')
class TaskFormCleanAssignedLawyerTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.case, cls.lawyers = _make_case_with_lawyers(2)
        cls.case_lawyer_pks = [l.pk for l in cls.lawyers]
        cls.outside_lawyer = Lawyer.objects.create(
            first_name='Obcy', last_name='Prawnik', bar_number='PL999', activeflag=True,
        )

    def _form(self, lawyer_pk=None, case_lawyer_pks=None):
        pks = case_lawyer_pks if case_lawyer_pks is not None else self.case_lawyer_pks
        return TaskForm(data=_form_data(lawyer_pk), case_lawyer_pks=pks)

    def test_valid_pk_returns_lawyer_instance(self):
        form = self._form(self.lawyers[0].pk)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsInstance(form.cleaned_data['assigned_lawyer'], Lawyer)
        self.assertEqual(form.cleaned_data['assigned_lawyer'], self.lawyers[0])

    def test_empty_assigned_lawyer_returns_none(self):
        form = self._form(None)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['assigned_lawyer'])

    def test_outside_lawyer_pk_is_rejected(self):
        form = self._form(self.outside_lawyer.pk)
        self.assertFalse(form.is_valid())
        self.assertIn('assigned_lawyer', form.errors)

    def test_no_case_context_accepts_any_lawyer(self):
        form = TaskForm(data=_form_data(self.outside_lawyer.pk), case_lawyer_pks=None)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsInstance(form.cleaned_data['assigned_lawyer'], Lawyer)


@tag('unit')
class TaskFormSUCleanAssignedLawyerTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.lawyer = Lawyer.objects.create(
            first_name='SU', last_name='Prawnik', bar_number='PL777', activeflag=True,
        )

    def test_clean_assigned_lawyer_returns_lawyer_instance_in_su_form(self):
        form = TaskFormSU(data={
            'title': 'Zadanie SU',
            'description': '',
            'priority': '',
            'status': '',
            'due_date': '',
            'assigned_lawyer': self.lawyer.pk,
            'created_by': '',
            'case': '',
            'parent_task': '',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsInstance(form.cleaned_data['assigned_lawyer'], Lawyer)
