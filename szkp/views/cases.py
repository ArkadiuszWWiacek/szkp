from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from szkp.models import (
    Case, CaseLawyer, CasePriority, CaseStatus, CaseType,
    CourtHearing, Document, Invoice, Task,
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
    return render(request, 'szkp/case_list.html', context)


@login_required
def case_detail(request, pk):
    case = get_object_or_404(Case.objects.select_related('client'), pk=pk)

    if not request.user.is_staff:
        if not CaseLawyer.objects.filter(case=case, lawyer__user=request.user).exists():
            raise PermissionDenied

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
    documents = case.document_set.order_by('-created_at')
    tasks = (case.task_set
             .filter(parent_task__isnull=True)
             .prefetch_related('task_set__assigned_lawyer')
             .select_related('assigned_lawyer')
             .order_by('priority'))
    invoices = case.invoice_set.order_by('-issue_date')
    lawyers = case.caselawyer_set.select_related('lawyer').order_by('role')

    active_tab = request.GET.get('tab', 'terminy')

    context = {
        'case': case,
        'hearings': hearings,
        'documents': documents,
        'tasks': tasks,
        'invoices': invoices,
        'lawyers': lawyers,
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
