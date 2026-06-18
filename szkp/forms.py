from decimal import Decimal

from django import forms
from django.utils import timezone

from szkp.models import (
    Case, CaseLawyerRole, CasePriority, CaseStatus, CaseType,
    Client, ClientType,
    CourtHearing, Document, DocumentType, HearingStatus, HearingType,
    Invoice, InvoiceStatus,
    Task, TaskPriority, TaskStatus,
)


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'type', 'first_name', 'last_name', 'company_name',
            'pesel', 'nip', 'phone', 'email',
            'address_street', 'address_city', 'address_zip',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and 'type' not in self.initial:
            self.initial['type'] = ClientType.OSOBA_FIZYCZNA

    def clean(self):
        cleaned_data = super().clean()
        client_type = cleaned_data.get('type', '')
        if client_type == ClientType.OSOBA_FIZYCZNA:
            if not (cleaned_data.get('first_name') or '').strip():
                self.add_error('first_name', 'Imię jest wymagane.')
            if not (cleaned_data.get('last_name') or '').strip():
                self.add_error('last_name', 'Nazwisko jest wymagane.')
            pesel = cleaned_data.get('pesel') or ''
            if not pesel or not (len(pesel) == 11 and pesel.isdigit()):
                self.add_error('pesel', 'PESEL musi zawierać dokładnie 11 cyfr.')
        elif client_type == ClientType.FIRMA:
            if not (cleaned_data.get('company_name') or '').strip():
                self.add_error('company_name', 'Nazwa firmy jest wymagana.')
            if not (cleaned_data.get('nip') or '').strip():
                self.add_error('nip', 'NIP jest wymagany.')
        return cleaned_data


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            'case_number', 'title', 'client', 'case_type',
            'status', 'case_priority', 'court_case_number', 'description',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [('', '---------')] + list(CaseStatus.choices)
        self.fields['status'].required = False
        self.fields['case_priority'].choices = [('', '---------')] + list(CasePriority.choices)
        self.fields['case_priority'].required = False

    def clean_status(self):
        return self.cleaned_data.get('status') or CaseStatus.NOWA

    def clean_case_priority(self):
        return self.cleaned_data.get('case_priority') or CasePriority.NORMALNA


class CourtHearingForm(forms.ModelForm):
    class Meta:
        model = CourtHearing
        fields = [
            'court_name', 'hearing_type', 'scheduled_at', 'status',
            'reminder_minutes_before', 'courtroom', 'judge_name', 'notes',
        ]
        widgets = {
            'scheduled_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, is_new=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_new = is_new
        self.fields['status'].required = False
        if self.instance.pk and self.instance.scheduled_at:
            self.initial['scheduled_at'] = timezone.localtime(self.instance.scheduled_at)
        if not self.instance.pk:
            self.initial.setdefault('reminder_minutes_before', 1440)

    def clean(self):
        cleaned_data = super().clean()
        if self.is_new:
            scheduled_at = cleaned_data.get('scheduled_at')
            if scheduled_at and scheduled_at <= timezone.now():
                self.add_error('scheduled_at', 'Data terminu musi być w przyszłości.')
        return cleaned_data

    def clean_status(self):
        return self.cleaned_data.get('status') or HearingStatus.PLANOWANY


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'issue_date', 'due_date',
            'net_amount', 'vat_rate', 'currency', 'status',
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'due_date':   forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, instance_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance_pk = instance_pk
        self.fields['vat_rate'].required = False
        self.fields['currency'].required = False
        self.fields['status'].required = False
        if not self.instance.pk:
            self.initial.setdefault('status', InvoiceStatus.WYSTAWIONA)
            self.initial.setdefault('currency', 'PLN')

    def clean_invoice_number(self):
        number = self.cleaned_data.get('invoice_number')
        qs = Invoice.objects.filter(invoice_number=number)
        exclude_pk = self._instance_pk if self._instance_pk is not None else self.instance.pk
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        if qs.exists():
            raise forms.ValidationError('Faktura o tym numerze już istnieje.')
        return number

    def clean_vat_rate(self):
        val = self.cleaned_data.get('vat_rate')
        return val if val is not None else (
            self.instance.vat_rate if self.instance.pk else Decimal('0.23')
        )

    def clean_currency(self):
        return self.cleaned_data.get('currency') or 'PLN'

    def clean_status(self):
        return self.cleaned_data.get('status') or InvoiceStatus.WYSTAWIONA


class TaskForm(forms.ModelForm):
    assigned_lawyer = forms.IntegerField(required=False)

    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'status', 'due_date']
        widgets = {
            'due_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, case_lawyer_pks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._case_lawyer_pks = case_lawyer_pks
        self.fields['priority'].required = False
        self.fields['status'].required = False
        if self.instance.pk:
            if self.instance.due_date:
                self.initial['due_date'] = self.instance.due_date
            self.initial['assigned_lawyer'] = self.instance.assigned_lawyer_id

    def clean_assigned_lawyer(self):
        pk = self.cleaned_data.get('assigned_lawyer')
        if self._case_lawyer_pks is not None and pk is not None:
            if pk not in self._case_lawyer_pks:
                raise forms.ValidationError('Wybrany prawnik nie jest przypisany do tej sprawy.')
        return pk

    def clean_priority(self):
        return self.cleaned_data.get('priority') or TaskPriority.NORMALNA

    def clean_status(self):
        return self.cleaned_data.get('status') or TaskStatus.NOWE


class DocumentForm(forms.ModelForm):
    file = forms.FileField(required=False)

    class Meta:
        model = Document
        fields = ['title', 'document_type', 'is_internal']

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


# ─── Formularze dla superużytkownika (pełny dostęp do pól modelu) ───────────

class CaseFormSU(CaseForm):
    class Meta(CaseForm.Meta):
        fields = CaseForm.Meta.fields + ['opened_at', 'closed_at']
        widgets = {
            'opened_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M',
            ),
            'closed_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['opened_at'].required = False
        self.fields['closed_at'].required = False
        if self.instance.pk:
            if self.instance.opened_at:
                self.initial['opened_at'] = timezone.localtime(self.instance.opened_at)
            if self.instance.closed_at:
                self.initial['closed_at'] = timezone.localtime(self.instance.closed_at)


class ClientFormSU(ClientForm):
    class Meta(ClientForm.Meta):
        fields = ClientForm.Meta.fields + ['country']
        widgets = {
            'type': forms.RadioSelect,
        }


class CourtHearingFormSU(CourtHearingForm):
    class Meta(CourtHearingForm.Meta):
        fields = CourtHearingForm.Meta.fields + ['responsible_lawyer', 'reminder_sent_at']
        widgets = {
            **CourtHearingForm.Meta.widgets,
            'reminder_sent_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsible_lawyer'].required = False
        self.fields['reminder_sent_at'].required = False
        self.fields['reminder_minutes_before'].required = False
        if self.instance.pk and self.instance.reminder_sent_at:
            self.initial['reminder_sent_at'] = timezone.localtime(self.instance.reminder_sent_at)

    def clean_reminder_minutes_before(self):
        val = self.cleaned_data.get('reminder_minutes_before')
        return val if val is not None else 1440


class InvoiceFormSU(InvoiceForm):
    class Meta(InvoiceForm.Meta):
        fields = InvoiceForm.Meta.fields + ['paid_at']
        widgets = {
            **InvoiceForm.Meta.widgets,
            'paid_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paid_at'].required = False
        if self.instance.pk and self.instance.paid_at:
            self.initial['paid_at'] = timezone.localtime(self.instance.paid_at)


class TaskFormSU(TaskForm):
    created_by  = forms.IntegerField(required=False)
    case        = forms.IntegerField(required=False)
    parent_task = forms.IntegerField(required=False)


class CaseLawyerFormSU(CaseLawyerForm):
    role = forms.ChoiceField(choices=CaseLawyerRole.choices)
    responsible_flag = forms.BooleanField(required=False)
    unassigned_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M',
        ),
    )

    def clean_role(self):
        return self.cleaned_data.get('role')
