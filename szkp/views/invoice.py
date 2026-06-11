from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from szkp.forms import InvoiceForm
from szkp.models import Case, CaseLawyer, Invoice, InvoiceStatus


def _form_context(case, invoice, form_data, errors):
    return {
        'case': case,
        'invoice': invoice,
        'form_data': form_data,
        'errors': errors,
        'status_choices': InvoiceStatus.choices,
    }


@login_required
def invoice_form(request, case_pk, pk=None):
    case = get_object_or_404(Case, pk=case_pk)
    invoice = get_object_or_404(Invoice, pk=pk, case=case) if pk else None

    if not request.user.is_staff:
        if not CaseLawyer.objects.filter(case=case, lawyer__user=request.user).exists():
            raise PermissionDenied

    redirect_url = (
        reverse('szkp:case_detail', kwargs={'pk': case_pk}) + '?tab=faktury'
    )

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance_pk=invoice.pk if invoice else None)
        if form.is_valid():
            cd = form.cleaned_data
            obj = invoice or Invoice(case=case)
            obj.invoice_number = cd['invoice_number']
            obj.issue_date     = cd['issue_date']
            obj.due_date       = cd['due_date']
            obj.net_amount     = cd['net_amount']
            obj.vat_rate       = cd.get('vat_rate') or obj.vat_rate
            obj.currency       = cd.get('currency') or 'PLN'
            obj.status         = cd.get('status') or InvoiceStatus.WYSTAWIONA
            obj.save()
            messages.success(request, 'Faktura została zapisana.')
            return redirect(redirect_url)

        return render(
            request,
            'szkp/invoice_form.html',
            _form_context(case, invoice, request.POST, form.errors),
        )

    if invoice:
        form_data = {
            'invoice_number': invoice.invoice_number,
            'issue_date':     invoice.issue_date.strftime('%Y-%m-%d'),
            'due_date':       invoice.due_date.strftime('%Y-%m-%d'),
            'net_amount':     str(invoice.net_amount),
            'vat_rate':       str(invoice.vat_rate),
            'currency':       invoice.currency,
            'status':         invoice.status,
        }
    else:
        form_data = {
            'status':   InvoiceStatus.WYSTAWIONA,
            'currency': 'PLN',
            'vat_rate': '0.23',
        }

    return render(
        request,
        'szkp/invoice_form.html',
        _form_context(case, invoice, form_data, {}),
    )
