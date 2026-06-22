from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, tag

from szkp.forms import InvoiceForm
from szkp.models import Client, ClientType, Case, CaseType, Invoice, InvoiceStatus


def _make_case():
    klient = Client.objects.create(
        type=ClientType.OSOBA_FIZYCZNA,
        first_name='Anna', last_name='Klientka', pesel='89010112345',
    )
    return Case.objects.create(
        client=klient, case_number='INV-UNIT-001', title='Sprawa testowa', case_type=CaseType.CYWILNA,
    )


def _make_invoice(case, number='FV/TEST/001'):
    return Invoice.objects.create(
        case=case,
        invoice_number=number,
        net_amount=Decimal('1000.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        status=InvoiceStatus.WYSTAWIONA,
    )


def _form_data(number='FV/TEST/001', **overrides):
    data = {
        'invoice_number': number,
        'net_amount': '1000.00',
        'vat_rate': '0.23',
        'currency': 'PLN',
        'status': InvoiceStatus.WYSTAWIONA,
        'issue_date': date.today().strftime('%Y-%m-%d'),
        'due_date': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
    }
    data.update(overrides)
    return data


@tag('unit')
class InvoiceFormInstancePkTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.case = _make_case()
        cls.invoice = _make_invoice(cls.case, 'FV/TEST/001')
        cls.other_invoice = _make_invoice(cls.case, 'FV/TEST/002')

    def test_edit_same_number_is_valid(self):
        """Edycja faktury z tym samym numerem (jej własnym) powinna być valid."""
        form = InvoiceForm(data=_form_data('FV/TEST/001'), instance=self.invoice)
        self.assertTrue(form.is_valid(), form.errors)

    def test_edit_with_other_existing_number_is_invalid(self):
        """Edycja faktury z numerem należącym do innej faktury powinna być invalid."""
        form = InvoiceForm(data=_form_data('FV/TEST/002'), instance=self.invoice)
        self.assertFalse(form.is_valid())
        self.assertIn('invoice_number', form.errors)

    def test_new_invoice_with_unique_number_is_valid(self):
        """Nowa faktura z unikalnym numerem powinna być valid."""
        form = InvoiceForm(data=_form_data('FV/TEST/NOWY'))
        self.assertTrue(form.is_valid(), form.errors)

    def test_new_invoice_with_duplicate_number_is_invalid(self):
        """Nowa faktura z numerem który już istnieje powinna być invalid."""
        form = InvoiceForm(data=_form_data('FV/TEST/001'))
        self.assertFalse(form.is_valid())
        self.assertIn('invoice_number', form.errors)

    def test_instance_pk_parameter_not_required(self):
        """InvoiceForm nie wymaga parametru instance_pk."""
        form = InvoiceForm(data=_form_data('FV/TEST/001'), instance=self.invoice)
        self.assertFalse(hasattr(form, '_instance_pk'))
