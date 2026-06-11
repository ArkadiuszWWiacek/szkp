from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from szkp.models import (
    Case, CaseStatus,
    CourtHearing,
    Invoice, InvoiceStatus,
    Task,
)


@login_required
def dashboard(request):
    today = timezone.localdate()

    case_qs    = Case.objects.all()
    hearing_qs = CourtHearing.objects.all()
    invoice_qs = Invoice.objects.all()
    task_qs    = Task.objects.all()

    if not request.user.is_staff:
        if hasattr(request.user, 'lawyer'):
            lawyer = request.user.lawyer
            case_qs    = case_qs.filter(caselawyer__lawyer=lawyer).distinct()
            hearing_qs = hearing_qs.filter(case__caselawyer__lawyer=lawyer).distinct()
            invoice_qs = invoice_qs.filter(
                Q(case__isnull=True) | Q(case__caselawyer__lawyer=lawyer)
            ).distinct()
            task_qs    = task_qs.filter(assigned_lawyer=lawyer)
        else:
            case_qs    = Case.objects.none()
            hearing_qs = CourtHearing.objects.none()
            invoice_qs = Invoice.objects.none()
            task_qs    = Task.objects.none()

    status_counts = {row['status']: row['cnt'] for row in
                     case_qs.values('status').annotate(cnt=Count('id'))}

    upcoming_hearings = (
        hearing_qs
        .filter(scheduled_at__date__gte=today, status='planowany')
        .order_by('scheduled_at')
        .select_related('case')[:5]
    )

    overdue_invoices = (
        invoice_qs
        .filter(status=InvoiceStatus.PRZETERMINOWANA)
        .order_by('due_date')
        .select_related('case')[:5]
    )

    today_tasks = (
        task_qs
        .filter(due_date__date=today, status__in=['nowe', 'w_toku'])
        .order_by('priority')
        .select_related('case')[:6]
    )

    upcoming_tasks = (
        task_qs
        .filter(
            due_date__date__gt=today,
            due_date__date__lte=today + timezone.timedelta(days=7),
            status__in=['nowe', 'w_toku'],
        )
        .order_by('due_date', 'priority')
        .select_related('case')[:8]
    )

    context = {
        'today': today,
        'counts': status_counts,
        'total_cases': case_qs.count(),
        'upcoming_hearings': upcoming_hearings,
        'overdue_invoices': overdue_invoices,
        'today_tasks': today_tasks,
        'upcoming_tasks': upcoming_tasks,
    }
    return render(request, 'szkp/dashboard.html', context)
