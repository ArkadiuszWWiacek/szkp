from django import forms

from szkp.models import CasePriority, CaseStatus, CaseType, Client, ClientType


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
