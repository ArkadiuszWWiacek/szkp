from decimal import Decimal

from django import forms
from django.utils import timezone

from szkp.models import (
    CaseLawyerRole, CasePriority, CaseStatus, CaseType, Client, ClientType,
    DocumentType, HearingStatus, HearingType, Invoice, InvoiceStatus,
    TaskPriority, TaskStatus,
)


class ClientForm(forms.Form):
    type = forms.ChoiceField(choices=ClientType.choices)
    first_name    = forms.CharField(required=False, max_length=100)
    last_name     = forms.CharField(required=False, max_length=100)
    company_name  = forms.CharField(required=False, max_length=200)
    pesel         = forms.CharField(required=False, max_length=11)
    nip           = forms.CharField(required=False, max_length=10)
    phone         = forms.CharField(required=False, max_length=20)
    email         = forms.EmailField(required=False, max_length=255)
    address_street = forms.CharField(required=False, max_length=200)
    address_city  = forms.CharField(required=False, max_length=100)
    address_zip   = forms.CharField(required=False, max_length=10)

    def clean(self):
        cleaned_data = super().clean()
        client_type = cleaned_data.get('type', '')
        if client_type == ClientType.OSOBA_FIZYCZNA:
            if not cleaned_data.get('first_name', '').strip():
                self.add_error('first_name', 'Imię jest wymagane.')
            if not cleaned_data.get('last_name', '').strip():
                self.add_error('last_name', 'Nazwisko jest wymagane.')
            pesel = cleaned_data.get('pesel', '')
            if not pesel or not (len(pesel) == 11 and pesel.isdigit()):
                self.add_error('pesel', 'PESEL musi zawierać dokładnie 11 cyfr.')
        elif client_type == ClientType.FIRMA:
            if not cleaned_data.get('company_name', '').strip():
                self.add_error('company_name', 'Nazwa firmy jest wymagana.')
            if not cleaned_data.get('nip', '').strip():
                self.add_error('nip', 'NIP jest wymagany.')
        return cleaned_data


class CourtHearingForm(forms.Form):
    court_name              = forms.CharField(max_length=200)
    hearing_type            = forms.ChoiceField(choices=HearingType.choices)
    scheduled_at            = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
    )
    status                  = forms.ChoiceField(choices=HearingStatus.choices, required=False)
    reminder_minutes_before = forms.IntegerField(initial=1440, min_value=1)
    courtroom               = forms.CharField(required=False, max_length=50)
    judge_name              = forms.CharField(required=False, max_length=100)
    notes                   = forms.CharField(required=False)

    def __init__(self, *args, is_new=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_new = is_new

    def clean(self):
        cleaned_data = super().clean()
        if self.is_new:
            scheduled_at = cleaned_data.get('scheduled_at')
            if scheduled_at and scheduled_at <= timezone.now():
                self.add_error('scheduled_at', 'Data terminu musi być w przyszłości.')
        return cleaned_data


class InvoiceForm(forms.Form):
    invoice_number = forms.CharField(max_length=50)
    issue_date     = forms.DateField(input_formats=['%Y-%m-%d'])
    due_date       = forms.DateField(input_formats=['%Y-%m-%d'])
    net_amount     = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0'))
    vat_rate       = forms.DecimalField(
        max_digits=5, decimal_places=4, min_value=Decimal('0'),
        initial=Decimal('0.23'), required=False,
    )
    currency       = forms.CharField(max_length=3, required=False)
    status         = forms.ChoiceField(choices=InvoiceStatus.choices, required=False)

    def __init__(self, *args, instance_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance_pk = instance_pk

    def clean_invoice_number(self):
        number = self.cleaned_data.get('invoice_number')
        qs = Invoice.objects.filter(invoice_number=number)
        if self.instance_pk:
            qs = qs.exclude(pk=self.instance_pk)
        if qs.exists():
            raise forms.ValidationError('Faktura o tym numerze już istnieje.')
        return number


class TaskForm(forms.Form):
    title           = forms.CharField(max_length=300)
    description     = forms.CharField(required=False)
    priority        = forms.ChoiceField(choices=TaskPriority.choices, required=False)
    status          = forms.ChoiceField(choices=TaskStatus.choices, required=False)
    due_date        = forms.DateTimeField(
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
    )
    assigned_lawyer = forms.IntegerField(required=False)

    def __init__(self, *args, case_lawyer_pks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._case_lawyer_pks = case_lawyer_pks

    def clean_assigned_lawyer(self):
        pk = self.cleaned_data.get('assigned_lawyer')
        if self._case_lawyer_pks is not None and pk is not None:
            if pk not in self._case_lawyer_pks:
                raise forms.ValidationError('Wybrany prawnik nie jest przypisany do tej sprawy.')
        return pk


class CaseForm(forms.Form):
    case_number      = forms.CharField(max_length=50)
    title            = forms.CharField(max_length=300)
    client           = forms.ModelChoiceField(queryset=Client.objects.all())
    case_type        = forms.ChoiceField(choices=CaseType.choices)
    status           = forms.ChoiceField(
        choices=[('', '---------')] + list(CaseStatus.choices), required=False,
    )
    case_priority    = forms.ChoiceField(
        choices=[('', '---------')] + list(CasePriority.choices), required=False,
    )
    court_case_number = forms.CharField(max_length=100, required=False)
    description      = forms.CharField(required=False)


class DocumentForm(forms.Form):
    title         = forms.CharField(max_length=300)
    document_type = forms.ChoiceField(choices=DocumentType.choices)
    is_internal   = forms.BooleanField(required=False)
    file          = forms.FileField(required=False)

    def __init__(self, *args, is_new=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_new = is_new

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if self.is_new and not f:
            raise forms.ValidationError('Plik jest wymagany.')
        return f


class DocumentVersionForm(forms.Form):
    file = forms.FileField()


class CaseLawyerForm(forms.Form):
    lawyer = forms.IntegerField()
    role   = forms.ChoiceField(choices=[
        (CaseLawyerRole.ASYSTENT, CaseLawyerRole.ASYSTENT.label),
        (CaseLawyerRole.DORADCA,  CaseLawyerRole.DORADCA.label),
    ])

    def __init__(self, *args, available_lawyer_pks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._available_lawyer_pks = available_lawyer_pks or []

    def clean_lawyer(self):
        pk = self.cleaned_data.get('lawyer')
        if pk not in self._available_lawyer_pks:
            raise forms.ValidationError(
                'Wybrany prawnik jest już przypisany do tej sprawy lub nie istnieje.'
            )
        return pk

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role == CaseLawyerRole.PROWADZACY:
            raise forms.ValidationError(
                'Nie można przypisać roli Prowadzący przez ten formularz.'
            )
        return role
