from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, RestrictedError
from django.shortcuts import get_object_or_404, redirect, render

from szkp.forms import ClientForm, ClientFormSU
from szkp.models import Client


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
    ctx = {
        'page_obj':  page_obj,
        'q':         q,
        'sort':      sort,
        'direction': direction,
    }
    if request.user.is_superuser:
        return render(request, 'szkp/client_list_su.html', ctx)
    return render(request, 'szkp/client_list.html', ctx)


@login_required
def client_form(request, pk=None):
    client = get_object_or_404(Client, pk=pk) if pk else None
    is_su = request.user.is_superuser
    FormClass = ClientFormSU if is_su else ClientForm
    template = 'szkp/client_form_su.html' if is_su else 'szkp/client_form.html'

    if request.method == 'POST':
        form = FormClass(request.POST, instance=client)
        if form.is_valid():
            form.save()
            verb = 'zaktualizowany' if client else 'dodany'
            messages.success(request, f'Klient został {verb}.')
            return redirect('szkp:client_list')
        return render(request, template, {'client': client, 'form': form})

    form = FormClass(instance=client)
    return render(request, template, {'client': client, 'form': form})


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
