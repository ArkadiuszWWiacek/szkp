from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count, When, Case as DbCase, IntegerField, Value
from django.utils import timezone

from .models import (
    Case, CaseStatus, CaseType, CasePriority,
    Client, ClientType,
    CourtHearing,
    Document,
    Invoice, InvoiceStatus,
    Task, TaskStatus, TaskPriority,
    CaseLawyer, CaseLawyerRole,
)


def home(request):
    return render(request, 'szkp/home.html')


@login_required
def dashboard(request):
    today = timezone.localdate()

    status_counts = {row['status']: row['cnt'] for row in
                     Case.objects.values('status').annotate(cnt=Count('id'))}

    upcoming_hearings = (
        CourtHearing.objects
        .filter(scheduled_at__date__gte=today, status='planowany')
        .order_by('scheduled_at')
        .select_related('case')[:5]
    )

    overdue_invoices = (
        Invoice.objects
        .filter(status=InvoiceStatus.PRZETERMINOWANA)
        .order_by('due_date')
        .select_related('case')[:5]
    )

    today_tasks = (
        Task.objects
        .filter(due_date__date=today, status__in=['nowe', 'w_toku'])
        .order_by('priority')
        .select_related('case')[:6]
    )

    context = {
        'today': today,
        'counts': status_counts,
        'total_cases': Case.objects.count(),
        'upcoming_hearings': upcoming_hearings,
        'overdue_invoices': overdue_invoices,
        'today_tasks': today_tasks,
    }
    return render(request, 'szkp/dashboard.html', context)


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
        'case_number':       'case_number',
        'client':            'client__last_name',
        'case_type':         'case_type',
        'status':            'status',
        'case_priority':     'case_priority',
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
                old_display = case.get_status_display()
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


@login_required
def client_list(request):
    q = request.GET.get('q', '').strip()
    qs = Client.objects.all()
    if q:
        qs = qs.filter(
            Q(last_name__icontains=q)
            | Q(first_name__icontains=q)
            | Q(company_name__icontains=q)
        )
    qs = qs.order_by('last_name', 'company_name')
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'szkp/client_list.html', {'page_obj': page_obj, 'q': q})


@login_required
def client_form(request, pk=None):
    client = get_object_or_404(Client, pk=pk) if pk else None
    errors = {}

    if request.method == 'POST':
        data = request.POST
        client_type = data.get('type', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        company_name = data.get('company_name', '').strip()
        pesel = data.get('pesel', '').strip()
        nip = data.get('nip', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address_street = data.get('address_street', '').strip()
        address_city = data.get('address_city', '').strip()
        address_zip = data.get('address_zip', '').strip()

        if not client_type:
            errors['type'] = 'Wybierz typ klienta.'
        elif client_type == 'osobafizyczna':
            if not first_name:
                errors['first_name'] = 'Imię jest wymagane.'
            if not last_name:
                errors['last_name'] = 'Nazwisko jest wymagane.'
            if not pesel or not (len(pesel) == 11 and pesel.isdigit()):
                errors['pesel'] = 'PESEL musi zawierać dokładnie 11 cyfr.'
        elif client_type == 'firma':
            if not company_name:
                errors['company_name'] = 'Nazwa firmy jest wymagana.'
            if not nip:
                errors['nip'] = 'NIP jest wymagany.'

        if not errors:
            obj = client or Client()
            obj.type = client_type
            obj.first_name = first_name or None
            obj.last_name = last_name or None
            obj.company_name = company_name or None
            obj.pesel = pesel if client_type == 'osobafizyczna' else None
            obj.nip = nip if client_type == 'firma' else None
            obj.phone = phone or None
            obj.email = email or None
            obj.address_street = address_street or None
            obj.address_city = address_city or None
            obj.address_zip = address_zip or None
            obj.save()
            verb = 'zaktualizowany' if client else 'dodany'
            messages.success(request, f'Klient został {verb}.')
            return redirect('szkp:client_list')

        form_data = data
    else:
        if client:
            form_data = {
                'type': client.type,
                'first_name': client.first_name or '',
                'last_name': client.last_name or '',
                'company_name': client.company_name or '',
                'pesel': client.pesel or '',
                'nip': client.nip or '',
                'phone': client.phone or '',
                'email': client.email or '',
                'address_street': client.address_street or '',
                'address_city': client.address_city or '',
                'address_zip': client.address_zip or '',
            }
        else:
            form_data = {}

    context = {
        'client': client,
        'form_data': form_data,
        'errors': errors,
    }
    return render(request, 'szkp/client_form.html', context)


@login_required
def my_tasks(request):
    today = timezone.localdate()
    status_filter = request.GET.get('status', '')
    period_filter = request.GET.get('period', '')

    priority_rank = DbCase(
        When(priority='pilna',    then=Value(0)),
        When(priority='wysoka',   then=Value(1)),
        When(priority='normalna', then=Value(2)),
        When(priority='niska',    then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )

    qs = (Task.objects
          .filter(parent_task__isnull=True)
          .select_related('case', 'assigned_lawyer')
          .prefetch_related('task_set__assigned_lawyer'))

    if status_filter:
        qs = qs.filter(status=status_filter)

    if period_filter == 'today':
        qs = qs.filter(due_date__date=today)
    elif period_filter == 'week':
        qs = qs.filter(due_date__date__lte=today + timezone.timedelta(days=7),
                       due_date__date__gte=today)

    qs = qs.annotate(priority_rank=priority_rank).order_by('priority_rank', 'due_date')

    context = {
        'tasks': qs,
        'status_filter': status_filter,
        'period_filter': period_filter,
        'status_choices': TaskStatus.choices,
        'today': today,
    }
    return render(request, 'szkp/my_tasks.html', context)
