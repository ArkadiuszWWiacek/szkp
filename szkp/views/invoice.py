from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from szkp.forms import InvoiceForm
from szkp.models import Case, CaseLawyer, Invoice, InvoiceStatus
from szkp.permissions import require_case_access


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

    require_case_access(request, case)

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


@login_required
def invoice_list(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status')
    sort = request.GET.get('sort', 'issue_date')
    direction = request.GET.get('dir', 'desc')
    valid_sort_fields = {
        'invoice_number': 'invoice_number',
        'case':           'case__case_number',
        'issue_date':     'issue_date',
        'due_date':       'due_date',
        'gross_amount':   'gross_amount',
        'status':         'status',
    }
    sort_field = valid_sort_fields.get(sort, 'issue_date')
    if direction == 'desc':
        sort_field = f'-{sort_field}'
    qs = Invoice.objects.select_related('case').order_by(sort_field)
    if not request.user.is_staff:
        assigned = CaseLawyer.objects.filter(
            lawyer__user=request.user
        ).values_list('case_id', flat=True)
        qs = qs.filter(case__in=assigned)
    if status in dict(InvoiceStatus.choices):
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(invoice_number__icontains=q)
            | Q(case__case_number__icontains=q)
        )
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'szkp/invoice_list.html', {
        'page_obj':       page_obj,
        'invoices':       page_obj,
        'status_choices': InvoiceStatus.choices,
        'current_status': status or '',
        'sort':           sort,
        'direction':      direction,
        'q':              q,
    })


@login_required
@require_POST
def invoice_mark_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if not request.user.is_staff:
        if not invoice.case or not CaseLawyer.objects.filter(
            case=invoice.case, lawyer__user=request.user
        ).exists():
            raise PermissionDenied
    invoice.status = InvoiceStatus.OPŁACONA
    invoice.save()
    messages.success(request, 'Status faktury zmieniony na: Opłacona')
    next_url = request.POST.get('next') or reverse('szkp:invoice_list')
    return redirect(next_url)
