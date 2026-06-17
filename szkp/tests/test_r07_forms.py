"""
Testy jednostkowe R-07: Zamiana forms.Form na ModelForm.

IDs: TU-R07-01 … TU-R07-23

Zidentyfikowane jednostki do przetestowania:
  1. ClientForm       – ModelForm z clean() dla PESEL/NIP
  2. CaseForm         – ModelForm z __init__ (empty choices dla status/priority)
  3. CourtHearingForm – ModelForm z is_new= kwarg i clean() (walidacja daty przyszłej)
  4. InvoiceForm      – ModelForm z instance_pk= i clean_invoice_number() (unikalność)
  5. TaskForm         – ModelForm z case_lawyer_pks= i clean_assigned_lawyer()
  6. DocumentForm     – ModelForm z is_new= i clean_file() (plik wymagany tylko dla nowych)

Testy RED (wymagają ModelForm — których nie ma):
  TU-R07-01 … TU-R07-06  issubclass(Xxx, forms.ModelForm) → AssertionError
  TU-R07-07 … TU-R07-12  Xxx.Meta.model / Xxx.Meta.fields → AttributeError
  TU-R07-13 … TU-R07-15  hasattr(Xxx, 'save') → AssertionError (forms.Form nie ma save)
  TU-R07-16 … TU-R07-18  Xxx(instance=None) → TypeError (forms.Form nie przyjmuje instance=)

Testy GREEN (safety-net: logika clean() już istnieje na forms.Form):
  TU-R07-19 … TU-R07-23  Walidacja clean() identyczna po refaktoryzacji
"""

from datetime import timedelta

from django import forms
from django.test import SimpleTestCase, tag
from django.utils import timezone

from szkp.forms import (
    ClientForm, CaseForm, CourtHearingForm,
    InvoiceForm, TaskForm, DocumentForm,
)
from szkp.models import Client, Case, CourtHearing, Invoice, Document
from szkp.models import ClientType


# ===========================================================================
# TU-R07-01 … TU-R07-06  Struktura dziedziczenia — wszystkie 6 formularzy
# ===========================================================================

@tag('unit')
class R07FormInheritanceTest(SimpleTestCase):
    """Każdy formularz musi dziedziczyć po forms.ModelForm (nie forms.Form)."""

    # TU-R07-01
    def test_clientform_dziedziczy_po_modelform(self):
        self.assertTrue(
            issubclass(ClientForm, forms.ModelForm),
            'ClientForm musi dziedziczyć po forms.ModelForm',
        )

    # TU-R07-02
    def test_caseform_dziedziczy_po_modelform(self):
        self.assertTrue(
            issubclass(CaseForm, forms.ModelForm),
            'CaseForm musi dziedziczyć po forms.ModelForm',
        )

    # TU-R07-03
    def test_courthearingform_dziedziczy_po_modelform(self):
        self.assertTrue(
            issubclass(CourtHearingForm, forms.ModelForm),
            'CourtHearingForm musi dziedziczyć po forms.ModelForm',
        )

    # TU-R07-04
    def test_invoiceform_dziedziczy_po_modelform(self):
        self.assertTrue(
            issubclass(InvoiceForm, forms.ModelForm),
            'InvoiceForm musi dziedziczyć po forms.ModelForm',
        )

    # TU-R07-05
    def test_taskform_dziedziczy_po_modelform(self):
        self.assertTrue(
            issubclass(TaskForm, forms.ModelForm),
            'TaskForm musi dziedziczyć po forms.ModelForm',
        )

    # TU-R07-06
    def test_documentform_dziedziczy_po_modelform(self):
        self.assertTrue(
            issubclass(DocumentForm, forms.ModelForm),
            'DocumentForm musi dziedziczyć po forms.ModelForm',
        )


# ===========================================================================
# TU-R07-07 … TU-R07-12  Klasa Meta — model i pola
# ===========================================================================

@tag('unit')
class R07FormMetaTest(SimpleTestCase):
    """Każdy ModelForm musi mieć Meta.model i Meta.fields."""

    # TU-R07-07
    def test_clientform_meta_model_jest_client(self):
        self.assertEqual(
            ClientForm.Meta.model, Client,
            'ClientForm.Meta.model musi wskazywać na model Client',
        )

    # TU-R07-08
    def test_clientform_meta_fields_zawiera_wymagane_pola(self):
        wymagane = {
            'type', 'first_name', 'last_name', 'company_name',
            'pesel', 'nip', 'phone', 'email',
            'address_street', 'address_city', 'address_zip',
        }
        self.assertTrue(
            wymagane.issubset(set(ClientForm.Meta.fields)),
            f'ClientForm.Meta.fields musi zawierać wszystkie pola klienta: {wymagane}',
        )

    # TU-R07-09
    def test_invoiceform_meta_model_jest_invoice(self):
        self.assertEqual(
            InvoiceForm.Meta.model, Invoice,
            'InvoiceForm.Meta.model musi wskazywać na model Invoice',
        )

    # TU-R07-10
    def test_invoiceform_meta_fields_zawiera_wymagane_pola(self):
        wymagane = {
            'invoice_number', 'issue_date', 'due_date',
            'net_amount', 'vat_rate', 'currency', 'status',
        }
        self.assertTrue(
            wymagane.issubset(set(InvoiceForm.Meta.fields)),
            f'InvoiceForm.Meta.fields musi zawierać: {wymagane}',
        )

    # TU-R07-11
    def test_courthearingform_meta_model_jest_courthearing(self):
        self.assertEqual(
            CourtHearingForm.Meta.model, CourtHearing,
            'CourtHearingForm.Meta.model musi wskazywać na model CourtHearing',
        )

    # TU-R07-12
    def test_documentform_meta_model_jest_document(self):
        self.assertEqual(
            DocumentForm.Meta.model, Document,
            'DocumentForm.Meta.model musi wskazywać na model Document',
        )


# ===========================================================================
# TU-R07-13 … TU-R07-15  Metoda save() — dziedziczona z ModelForm
# ===========================================================================

@tag('unit')
class R07FormSaveMethodTest(SimpleTestCase):
    """Każdy ModelForm musi posiadać metodę save() (odziedziczoną z BaseModelForm)."""

    # TU-R07-13
    def test_clientform_ma_metode_save(self):
        self.assertTrue(
            hasattr(ClientForm, 'save'),
            'ClientForm musi posiadać metodę save() odziedziczoną z ModelForm',
        )

    # TU-R07-14
    def test_invoiceform_ma_metode_save(self):
        self.assertTrue(
            hasattr(InvoiceForm, 'save'),
            'InvoiceForm musi posiadać metodę save() odziedziczoną z ModelForm',
        )

    # TU-R07-15
    def test_documentform_ma_metode_save(self):
        self.assertTrue(
            hasattr(DocumentForm, 'save'),
            'DocumentForm musi posiadać metodę save() odziedziczoną z ModelForm',
        )


# ===========================================================================
# TU-R07-16 … TU-R07-18  Inicjalizacja z instance= — interface ModelForm
# ===========================================================================

@tag('unit')
class R07FormInstanceKwargTest(SimpleTestCase):
    """Formularze muszą akceptować kwarg instance= bez TypeError."""

    # TU-R07-16
    def test_clientform_przyjmuje_instance_none(self):
        """ClientForm(instance=None) nie może zgłaszać TypeError."""
        try:
            ClientForm(instance=None)
        except TypeError as exc:
            self.fail(
                f'ClientForm musi akceptować kwarg instance=None (ModelForm API), '
                f'ale zgłosił TypeError: {exc}'
            )

    # TU-R07-17
    def test_courthearingform_przyjmuje_instance_none_i_is_new(self):
        """CourtHearingForm(is_new=True, instance=None) nie może zgłaszać TypeError."""
        try:
            CourtHearingForm(is_new=True, instance=None)
        except TypeError as exc:
            self.fail(
                f'CourtHearingForm musi akceptować is_new= i instance= jednocześnie: {exc}'
            )

    # TU-R07-18
    def test_documentform_przyjmuje_instance_none_i_is_new(self):
        """DocumentForm(is_new=True, instance=None) nie może zgłaszać TypeError."""
        try:
            DocumentForm(is_new=True, instance=None)
        except TypeError as exc:
            self.fail(
                f'DocumentForm musi akceptować is_new= i instance= jednocześnie: {exc}'
            )


# ===========================================================================
# TU-R07-19 … TU-R07-23  Logika clean() — safety-net (GREEN)
# Walidacja musi być identyczna po przejściu na ModelForm.
# Te testy PRZECHODZĄ już teraz i muszą nadal przechodzić po R-07.
# ===========================================================================

@tag('unit')
class R07FormValidationLogicTest(SimpleTestCase):
    """Logika clean() i clean_pole() musi być zachowana 1:1 po refaktoryzacji."""

    # TU-R07-19 (SAFETY-NET — GREEN)
    def test_clientform_clean_odrzuca_osobe_bez_pesel(self):
        """Osoba fizyczna bez PESEL: is_valid() == False, błąd na polu 'pesel'."""
        form = ClientForm(data={
            'type': ClientType.OSOBA_FIZYCZNA,
            'first_name': 'Jan',
            'last_name': 'Kowalski',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('pesel', form.errors)

    # TU-R07-20 (SAFETY-NET — GREEN)
    def test_clientform_clean_odrzuca_firme_bez_nip(self):
        """Firma bez NIP: is_valid() == False, błąd na polu 'nip'."""
        form = ClientForm(data={
            'type': ClientType.FIRMA,
            'company_name': 'ACME Sp. z o.o.',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('nip', form.errors)

    # TU-R07-21 (SAFETY-NET — GREEN)
    def test_courthearingform_clean_odrzuca_przeszla_date_gdy_nowy(self):
        """Nowy termin z datą w przeszłości: is_valid() == False, błąd na 'scheduled_at'."""
        przeszla = (timezone.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
        form = CourtHearingForm(
            data={
                'court_name': 'Sąd Testowy',
                'hearing_type': 'rozprawa',
                'scheduled_at': przeszla,
                'reminder_minutes_before': 1440,
            },
            is_new=True,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_at', form.errors)

    # TU-R07-22 (SAFETY-NET — GREEN)
    def test_courthearingform_clean_akceptuje_przeszla_date_przy_edycji(self):
        """Edycja terminu (is_new=False): data w przeszłości nie powoduje błędu 'scheduled_at'."""
        przeszla = (timezone.now() - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
        form = CourtHearingForm(
            data={
                'court_name': 'Sąd Testowy',
                'hearing_type': 'rozprawa',
                'scheduled_at': przeszla,
                'reminder_minutes_before': 1440,
            },
            is_new=False,
        )
        form.is_valid()
        self.assertNotIn(
            'scheduled_at', form.errors,
            'Edycja terminu (is_new=False) nie powinna dawać błędu daty w przeszłości',
        )

    # TU-R07-23 (SAFETY-NET — GREEN)
    def test_documentform_clean_file_wymaga_pliku_dla_nowego(self):
        """Nowy dokument bez pliku: is_valid() == False, błąd na polu 'file'."""
        form = DocumentForm(
            data={'title': 'Dokument', 'document_type': 'notatka'},
            files={},
            is_new=True,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)
