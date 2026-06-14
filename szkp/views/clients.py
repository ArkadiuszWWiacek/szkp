from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, RestrictedError
from django.shortcuts import get_object_or_404, redirect, render

from szkp.forms import ClientForm
from szkp.models import Client, ClientType


@login_required
def client_list(request):
    q = request.GET.get('q', '').strip()
    qs = Client.objects.all()
    if q:
        qs = qs.filter(
            Q(last_name__icontains=q)
            | Q(first_name__icontains=q)
            | Q(company_name__icontains=q)
            | Q(pesel__icontains=q)
            | Q(nip__icontains=q)
        )
    sort = request.GET.get('sort', 'last_name')
    direction = request.GET.get('dir', 'asc')
    valid_sort_fields = {
        'last_name':  'last_name',
        'type':       'type',
        'created_at': 'created_at',
    }
    sort_field = valid_sort_fields.get(sort, 'last_name')
    if direction == 'desc':
        sort_field = f'-{sort_field}'
    qs = qs.order_by(sort_field)
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'szkp/client_list.html', {
        'page_obj':  page_obj,
        'q':         q,
        'sort':      sort,
        'direction': direction,
    })


@login_required
def client_form(request, pk=None):
    client = get_object_or_404(Client, pk=pk) if pk else None

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            obj = client or Client()
            obj.type         = cd['type']
            obj.first_name   = cd.get('first_name') or None
            obj.last_name    = cd.get('last_name') or None
            obj.company_name = cd.get('company_name') or None
            obj.pesel        = cd.get('pesel') if cd['type'] == ClientType.OSOBA_FIZYCZNA else None
            obj.nip          = cd.get('nip') if cd['type'] == ClientType.FIRMA else None
            obj.phone        = cd.get('phone') or None
            obj.email        = cd.get('email') or None
            obj.address_street = cd.get('address_street') or None
            obj.address_city   = cd.get('address_city') or None
            obj.address_zip    = cd.get('address_zip') or None
            obj.save()
            verb = 'zaktualizowany' if client else 'dodany'
            messages.success(request, f'Klient został {verb}.')
            return redirect('szkp:client_list')
        return render(request, 'szkp/client_form.html', {
            'client': client,
            'form_data': request.POST,
            'errors': form.errors,
        })

    form_data = {}
    if client:
        form_data = {
            'type':           client.type,
            'first_name':     client.first_name or '',
            'last_name':      client.last_name or '',
            'company_name':   client.company_name or '',
            'pesel':          client.pesel or '',
            'nip':            client.nip or '',
            'phone':          client.phone or '',
            'email':          client.email or '',
            'address_street': client.address_street or '',
            'address_city':   client.address_city or '',
            'address_zip':    client.address_zip or '',
        }
    return render(request, 'szkp/client_form.html', {
        'client': client,
        'form_data': form_data,
        'errors': {},
    })


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    error = None
    if request.method == 'POST':
        try:
            client.delete()
            messages.success(request, 'Klient został usunięty.')
            return redirect('szkp:client_list')
        except RestrictedError:
            error = 'Nie można usunąć klienta, który ma przypisane sprawy.'
    return render(request, 'szkp/client_confirm_delete.html', {
        'client': client,
        'error': error,
    })
