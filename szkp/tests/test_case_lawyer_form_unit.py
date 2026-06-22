from django.test import TestCase, tag

from szkp.forms import CaseLawyerForm, CaseLawyerFormSU
from szkp.models import (
    Client, ClientType, Case, CaseType, CaseLawyerRole, Lawyer,
)


def _make_lawyers(n=2):
    lawyers = []
    for i in range(n):
        lawyers.append(Lawyer.objects.create(
            first_name=f'Prawnik{i}',
            last_name=f'Testowy{i}',
            bar_number=f'PL{100 + i:03d}',
            activeflag=True,
        ))
    return lawyers


@tag('unit')
class CaseLawyerFormModelChoiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.lawyers = _make_lawyers(3)
        cls.available = cls.lawyers[:2]   # pierwsze dwa dostępne
        cls.unavailable = cls.lawyers[2]  # trzeci niedostępny
        cls.available_pks = [l.pk for l in cls.available]

    def _form(self, data=None, available_pks=None):
        pks = available_pks if available_pks is not None else self.available_pks
        return CaseLawyerForm(data=data, available_lawyer_pks=pks)

    def test_valid_lawyer_pk_is_accepted(self):
        form = self._form({'lawyer': self.available[0].pk, 'role': CaseLawyerRole.ASYSTENT})
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_lawyer_returns_lawyer_instance(self):
        form = self._form({'lawyer': self.available[0].pk, 'role': CaseLawyerRole.ASYSTENT})
        form.is_valid()
        self.assertIsInstance(form.cleaned_data['lawyer'], Lawyer)
        self.assertEqual(form.cleaned_data['lawyer'], self.available[0])

    def test_unavailable_lawyer_pk_is_rejected(self):
        form = self._form({'lawyer': self.unavailable.pk, 'role': CaseLawyerRole.ASYSTENT})
        self.assertFalse(form.is_valid())
        self.assertIn('lawyer', form.errors)

    def test_empty_lawyer_is_rejected(self):
        form = self._form({'lawyer': '', 'role': CaseLawyerRole.ASYSTENT})
        self.assertFalse(form.is_valid())
        self.assertIn('lawyer', form.errors)

    def test_prowadzacy_role_is_rejected(self):
        form = self._form({'lawyer': self.available[0].pk, 'role': CaseLawyerRole.PROWADZACY})
        self.assertFalse(form.is_valid())
        self.assertIn('role', form.errors)

    def test_asystent_role_is_accepted(self):
        form = self._form({'lawyer': self.available[0].pk, 'role': CaseLawyerRole.ASYSTENT})
        self.assertTrue(form.is_valid(), form.errors)

    def test_doradca_role_is_accepted(self):
        form = self._form({'lawyer': self.available[0].pk, 'role': CaseLawyerRole.DORADCA})
        self.assertTrue(form.is_valid(), form.errors)

    def test_no_clean_lawyer_method_in_form(self):
        """Po refaktoryzacji clean_lawyer nie powinno istnieć."""
        self.assertFalse(hasattr(CaseLawyerForm, 'clean_lawyer'))


@tag('unit')
class CaseLawyerFormSUModelChoiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.lawyers = _make_lawyers(2)
        cls.available_pks = [l.pk for l in cls.lawyers]

    def _form(self, data):
        return CaseLawyerFormSU(data=data, available_lawyer_pks=self.available_pks)

    def test_prowadzacy_role_accepted_by_su_form(self):
        form = self._form({'lawyer': self.lawyers[0].pk, 'role': CaseLawyerRole.PROWADZACY})
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_lawyer_returns_lawyer_instance_in_su_form(self):
        form = self._form({'lawyer': self.lawyers[0].pk, 'role': CaseLawyerRole.ASYSTENT})
        form.is_valid()
        self.assertIsInstance(form.cleaned_data['lawyer'], Lawyer)
