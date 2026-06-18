"""Testy jednostkowe: Klasy formularzy SU — TU-SU-01 – TU-SU-15.

Weryfikują strukturę (pola, choices) nowych klas SU bez dostępu do bazy danych.
Testy są RED: klasy CaseFormSU, ClientFormSU, itp. nie istnieją jeszcze w szkp.forms.

Zidentyfikowane jednostki:
  1. CaseFormSU       — rozszerza CaseForm o opened_at, closed_at
  2. ClientFormSU     — rozszerza ClientForm o country
  3. CourtHearingFormSU — rozszerza CourtHearingForm o responsible_lawyer, reminder_sent_at
  4. InvoiceFormSU    — rozszerza InvoiceForm o paid_at
  5. TaskFormSU       — rozszerza TaskForm o created_by, case, parent_task
  6. CaseLawyerFormSU — rozszerza CaseLawyerForm: PROWADZĄCY w choices, responsible_flag, unassigned_at
"""
from django import forms
from django.test import SimpleTestCase, tag

try:
    from szkp.forms import (
        CaseFormSU,
        ClientFormSU,
        CourtHearingFormSU,
        InvoiceFormSU,
        TaskFormSU,
        CaseLawyerFormSU,
    )
    _imports_ok = True
except ImportError:
    CaseFormSU = ClientFormSU = CourtHearingFormSU = None
    InvoiceFormSU = TaskFormSU = CaseLawyerFormSU = None
    _imports_ok = False

from szkp.forms import CaseForm, ClientForm, CourtHearingForm, InvoiceForm, TaskForm
from szkp.models import CaseLawyerRole


def _require(test_case, cls, name):
    """Pomocnik: kończy test z FAIL jeśli klasa SU nie istnieje."""
    if cls is None:
        test_case.fail(f'{name} nie istnieje w szkp.forms — RED: klasa jeszcze nie zaimplementowana')


# ═══════════════════════════════════════════════════════════════════════════
# TU-SU-01 – TU-SU-03: CaseFormSU
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class CaseFormSUStructureTest(SimpleTestCase):
    """Struktura CaseFormSU: pola opened_at, closed_at, dziedziczenie po CaseForm."""

    def test_tu_su_01_caseformsu_ma_pole_opened_at(self):
        """TU-SU-01: CaseFormSU zawiera pole opened_at."""
        _require(self, CaseFormSU, 'CaseFormSU')
        form = CaseFormSU()
        self.assertIn(
            'opened_at', form.fields,
            'CaseFormSU nie zawiera pola opened_at',
        )

    def test_tu_su_02_caseformsu_ma_pole_closed_at(self):
        """TU-SU-02: CaseFormSU zawiera pole closed_at."""
        _require(self, CaseFormSU, 'CaseFormSU')
        form = CaseFormSU()
        self.assertIn(
            'closed_at', form.fields,
            'CaseFormSU nie zawiera pola closed_at',
        )

    def test_tu_su_03_caseformsu_dziedziczy_po_caseform(self):
        """TU-SU-03: CaseFormSU jest podklasą CaseForm (dziedziczy walidację)."""
        _require(self, CaseFormSU, 'CaseFormSU')
        self.assertTrue(
            issubclass(CaseFormSU, CaseForm),
            'CaseFormSU musi dziedziczyć po CaseForm',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SU-04 – TU-SU-05: ClientFormSU
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class ClientFormSUStructureTest(SimpleTestCase):
    """Struktura ClientFormSU: pole country, dziedziczenie po ClientForm."""

    def test_tu_su_04_clientformsu_ma_pole_country(self):
        """TU-SU-04: ClientFormSU zawiera pole country."""
        _require(self, ClientFormSU, 'ClientFormSU')
        form = ClientFormSU()
        self.assertIn(
            'country', form.fields,
            'ClientFormSU nie zawiera pola country',
        )

    def test_tu_su_05_clientformsu_dziedziczy_po_clientform(self):
        """TU-SU-05: ClientFormSU jest podklasą ClientForm."""
        _require(self, ClientFormSU, 'ClientFormSU')
        self.assertTrue(
            issubclass(ClientFormSU, ClientForm),
            'ClientFormSU musi dziedziczyć po ClientForm',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SU-06 – TU-SU-07: CourtHearingFormSU
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class CourtHearingFormSUStructureTest(SimpleTestCase):
    """Struktura CourtHearingFormSU: responsible_lawyer, reminder_sent_at."""

    def test_tu_su_06_courthearingformsu_ma_pole_responsible_lawyer(self):
        """TU-SU-06: CourtHearingFormSU zawiera pole responsible_lawyer."""
        _require(self, CourtHearingFormSU, 'CourtHearingFormSU')
        form = CourtHearingFormSU()
        self.assertIn(
            'responsible_lawyer', form.fields,
            'CourtHearingFormSU nie zawiera pola responsible_lawyer',
        )

    def test_tu_su_07_courthearingformsu_ma_pole_reminder_sent_at(self):
        """TU-SU-07: CourtHearingFormSU zawiera pole reminder_sent_at."""
        _require(self, CourtHearingFormSU, 'CourtHearingFormSU')
        form = CourtHearingFormSU()
        self.assertIn(
            'reminder_sent_at', form.fields,
            'CourtHearingFormSU nie zawiera pola reminder_sent_at',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SU-08: InvoiceFormSU
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class InvoiceFormSUStructureTest(SimpleTestCase):
    """Struktura InvoiceFormSU: pole paid_at."""

    def test_tu_su_08_invoiceformsu_ma_pole_paid_at(self):
        """TU-SU-08: InvoiceFormSU zawiera pole paid_at."""
        _require(self, InvoiceFormSU, 'InvoiceFormSU')
        form = InvoiceFormSU()
        self.assertIn(
            'paid_at', form.fields,
            'InvoiceFormSU nie zawiera pola paid_at',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SU-09 – TU-SU-11: TaskFormSU
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class TaskFormSUStructureTest(SimpleTestCase):
    """Struktura TaskFormSU: pola created_by, case, parent_task."""

    def test_tu_su_09_taskformsu_ma_pole_created_by(self):
        """TU-SU-09: TaskFormSU zawiera pole created_by."""
        _require(self, TaskFormSU, 'TaskFormSU')
        form = TaskFormSU()
        self.assertIn(
            'created_by', form.fields,
            'TaskFormSU nie zawiera pola created_by',
        )

    def test_tu_su_10_taskformsu_ma_pole_case(self):
        """TU-SU-10: TaskFormSU zawiera pole case (opcjonalne — zmiana sprawy zadania)."""
        _require(self, TaskFormSU, 'TaskFormSU')
        form = TaskFormSU()
        self.assertIn(
            'case', form.fields,
            'TaskFormSU nie zawiera pola case',
        )

    def test_tu_su_11_taskformsu_ma_pole_parent_task(self):
        """TU-SU-11: TaskFormSU zawiera pole parent_task (opcjonalne)."""
        _require(self, TaskFormSU, 'TaskFormSU')
        form = TaskFormSU()
        self.assertIn(
            'parent_task', form.fields,
            'TaskFormSU nie zawiera pola parent_task',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SU-12 – TU-SU-15: CaseLawyerFormSU
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class CaseLawyerFormSUStructureTest(SimpleTestCase):
    """Struktura CaseLawyerFormSU: PROWADZĄCY w choices, responsible_flag, unassigned_at, brak blokady PROWADZĄCY."""

    def test_tu_su_12_caselawyer_formsu_role_zawiera_prowadzacy(self):
        """TU-SU-12: CaseLawyerFormSU.role choices zawierają CaseLawyerRole.PROWADZACY."""
        _require(self, CaseLawyerFormSU, 'CaseLawyerFormSU')
        form = CaseLawyerFormSU(available_lawyer_pks=[])
        role_field = form.fields.get('role')
        self.assertIsNotNone(role_field, 'CaseLawyerFormSU nie zawiera pola role')
        choices_values = [v for v, _ in role_field.choices]
        self.assertIn(
            CaseLawyerRole.PROWADZACY,
            choices_values,
            f'Rola PROWADZACY ({CaseLawyerRole.PROWADZACY}) nie jest w choices pola role. '
            f'Dostępne: {choices_values}',
        )

    def test_tu_su_13_caselawyer_formsu_clean_role_akceptuje_prowadzacy(self):
        """TU-SU-13: CaseLawyerFormSU.clean_role() nie odrzuca roli PROWADZĄCY."""
        _require(self, CaseLawyerFormSU, 'CaseLawyerFormSU')
        form = CaseLawyerFormSU(available_lawyer_pks=[1])
        form.cleaned_data = {'role': CaseLawyerRole.PROWADZACY}
        try:
            result = form.clean_role()
            self.assertEqual(
                result, CaseLawyerRole.PROWADZACY,
                'clean_role() powinno zwrócić CaseLawyerRole.PROWADZACY',
            )
        except forms.ValidationError:
            self.fail(
                'CaseLawyerFormSU.clean_role() niepoprawnie odrzuca rolę PROWADZĄCY '
                '(powinna być dozwolona dla SU)'
            )

    def test_tu_su_14_caselawyer_formsu_ma_pole_responsible_flag(self):
        """TU-SU-14: CaseLawyerFormSU zawiera pole responsible_flag."""
        _require(self, CaseLawyerFormSU, 'CaseLawyerFormSU')
        form = CaseLawyerFormSU(available_lawyer_pks=[])
        self.assertIn(
            'responsible_flag', form.fields,
            'CaseLawyerFormSU nie zawiera pola responsible_flag',
        )

    def test_tu_su_15_caselawyer_formsu_ma_pole_unassigned_at(self):
        """TU-SU-15: CaseLawyerFormSU zawiera pole unassigned_at (opcjonalne)."""
        _require(self, CaseLawyerFormSU, 'CaseLawyerFormSU')
        form = CaseLawyerFormSU(available_lawyer_pks=[])
        self.assertIn(
            'unassigned_at', form.fields,
            'CaseLawyerFormSU nie zawiera pola unassigned_at',
        )
