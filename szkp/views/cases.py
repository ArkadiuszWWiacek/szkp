from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from szkp.forms import CaseForm, CaseLawyerForm, CaseFormSU, CaseLawyerFormSU
from szkp.permissions import require_case_access, require_case_access_by_pk
from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CasePriority, CaseStatus, CaseType,
    Client, CourtHearing, Document, Invoice, Lawyer, Task,
)


@login_required
def case_list(request):
    qs = Case.objects.select_related('client').prefetch_related('caselawyer_set__lawyer')

    if not request.user.is_staff:
        qs = qs.filter(caselawyer__lawyer__user=request.user).distinct()

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(case_number__icontains=q)
            | Q(court_case_number__icontains=q)
            | Q(client__last_name__icontains=q)
            | Q(client__company_name__icontains=q)
            | Q(title__icontains=q)
        )

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    case_type = request.GET.get('type', '')
    if case_type:
        qs = qs.filter(case_type=case_type)

    sort = request.GET.get('sort', 'case_number')
    direction = request.GET.get('dir', 'asc')
    valid_sort_fields = {
        'case_number':   'case_number',
        'client':        'client__last_name',
        'case_type':     'case_type',
        'status':        'status',
        'case_priority': 'case_priority',
    }
    sort_field = valid_sort_fields.get(sort, 'case_number')
    if direction == 'desc':
        sort_field = f'-{sort_field}'
    qs = qs.order_by(sort_field)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'case_type': case_type,
        'sort': sort,
        'direction': direction,
        'status_choices': CaseStatus.choices,
        'type_choices': CaseType.choices,
    }
    if request.user.is_superuser:
        return render(request, 'szkp/case_list_su.html', context)
    return render(request, 'szkp/case_list.html', context)


@login_required
def case_detail(request, pk):
    case = get_object_or_404(Case.objects.select_related('client'), pk=pk)

    require_case_access(request, case)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_status':
            new_status = request.POST.get('status')
            if new_status in dict(CaseStatus.choices):
                case.status = new_status
                if new_status == CaseStatus.ZAKOŃCZONA and not case.closed_at:
                    case.closed_at = timezone.now()
                case.save()
                messages.success(request, f'Status zmieniony na: {case.get_status_display()}')
            return redirect('szkp:case_detail', pk=pk)
        elif action == 'close_case':
            case.status = CaseStatus.ZAKOŃCZONA
            case.closed_at = timezone.now()
            case.save()
            messages.success(request, 'Sprawa została zamknięta.')
            return redirect('szkp:case_detail', pk=pk)

    hearings = case.courthearing_set.order_by('scheduled_at')
    documents = case.document_set.prefetch_related('documentversion_set').order_by('-created_at')
    tasks = (case.task_set
             .filter(parent_task__isnull=True)
             .prefetch_related('task_set__assigned_lawyer')
             .select_related('assigned_lawyer')
             .order_by('priority'))
    invoices = case.invoice_set.order_by('-issue_date')
    lawyers = case.caselawyer_set.select_related('lawyer').order_by('role')
    lead_lawyer = case.caselawyer_set.filter(role=CaseLawyerRole.PROWADZACY).select_related('lawyer').first()

    active_tab = request.GET.get('tab', 'terminy')

    context = {
        'case': case,
        'hearings': hearings,
        'documents': documents,
        'tasks': tasks,
        'invoices': invoices,
        'lawyers': lawyers,
        'lead_lawyer': lead_lawyer,
        'status_choices': CaseStatus.choices,
        'active_tab': active_tab,
        'tab_counts': {
            'terminy':   hearings.count(),
            'dokumenty': documents.count(),
            'zadania':   tasks.count(),
            'faktury':   invoices.count(),
            'prawnicy':  lawyers.count(),
        },
    }
    return render(request, 'szkp/case_detail.html', context)


@login_required
def case_lawyer_delete(request, case_pk, pk):
    cl = get_object_or_404(CaseLawyer, pk=pk, case_id=case_pk)

    require_case_access_by_pk(request, case_pk)

    if cl.role == CaseLawyerRole.PROWADZACY:
        raise PermissionDenied

    if request.method == 'POST':
        cl.delete()
        messages.success(request, 'Prawnik został usunięty ze sprawy.')
        return redirect(f"{reverse('szkp:case_detail', args=[case_pk])}?tab=prawnicy")

    return render(request, 'szkp/case_lawyer_confirm_delete.html', {'cl': cl})


@login_required
def case_lawyer_add(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)

    require_case_access(request, case)

    is_su = request.user.is_superuser
    already_assigned_pks = list(
        CaseLawyer.objects.filter(case=case).values_list('lawyer_id', flat=True)
    )
    available_lawyers = Lawyer.objects.filter(activeflag=True).exclude(
        pk__in=already_assigned_pks
    ).order_by('last_name', 'first_name')
    available_lawyer_pks = list(available_lawyers.values_list('pk', flat=True))

    role_choices = [
        (CaseLawyerRole.ASYSTENT, CaseLawyerRole.ASYSTENT.label),
        (CaseLawyerRole.DORADCA,  CaseLawyerRole.DORADCA.label),
    ]
    redirect_url = reverse('szkp:case_detail', args=[case_pk]) + '?tab=prawnicy'

    if request.method == 'POST':
        if is_su:
            form = CaseLawyerFormSU(request.POST, available_lawyer_pks=available_lawyer_pks)
        else:
            form = CaseLawyerForm(request.POST, available_lawyer_pks=available_lawyer_pks)
        if form.is_valid():
            cd = form.cleaned_data
            CaseLawyer.objects.create(
                case=case,
                lawyer=Lawyer.objects.get(pk=cd['lawyer']),
                role=cd['role'],
            )
            messages.success(request, 'Prawnik został przypisany do sprawy.')
            return redirect(redirect_url)
        if is_su:
            return render(request, 'szkp/case_lawyer_add_su.html', {
                'case': case,
                'form': form,
                'available_lawyers': available_lawyers,
            })
        return render(request, 'szkp/case_lawyer_add.html', {
            'case': case,
            'form_data': request.POST,
            'errors': form.errors,
            'available_lawyers': available_lawyers,
            'role_choices': role_choices,
        })

    if is_su:
        form = CaseLawyerFormSU(available_lawyer_pks=available_lawyer_pks)
        return render(request, 'szkp/case_lawyer_add_su.html', {
            'case': case,
            'form': form,
            'available_lawyers': available_lawyers,
        })
    return render(request, 'szkp/case_lawyer_add.html', {
        'case': case,
        'form_data': {},
        'errors': {},
        'available_lawyers': available_lawyers,
        'role_choices': role_choices,
    })


def _case_form_context(case, form):
    return {
        'case': case,
        'form': form,
        'clients': Client.objects.order_by('last_name', 'company_name'),
        'type_choices': CaseType.choices,
        'status_choices': CaseStatus.choices,
        'priority_choices': CasePriority.choices,
    }


@login_required
def case_form(request, pk=None):
    case = get_object_or_404(Case, pk=pk) if pk else None
    is_su = request.user.is_superuser
    FormClass = CaseFormSU if is_su else CaseForm
    template = 'szkp/case_form_su.html' if is_su else 'szkp/case_form.html'

    if request.method == 'POST':
        form = FormClass(request.POST, instance=case)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.status == CaseStatus.ZAKOŃCZONA and not obj.closed_at:
                obj.closed_at = timezone.now()
            obj.save()

            if not pk and hasattr(request.user, 'lawyer'):
                CaseLawyer.objects.get_or_create(
                    case=obj, lawyer=request.user.lawyer,
                    defaults={'role': CaseLawyerRole.PROWADZACY},
                )

            messages.success(request, 'Sprawa została zapisana.')
            return redirect('szkp:case_detail', pk=obj.pk)

        return render(request, template, _case_form_context(case, form))

    form = FormClass(instance=case)
    return render(request, template, _case_form_context(case, form))
