from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count

from szkp.models import (
    Case, CaseStatus,
    CourtHearing,
    Invoice, InvoiceStatus,
    Task,
)


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

    upcoming_tasks = (
        Task.objects
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
        'total_cases': Case.objects.count(),
        'upcoming_hearings': upcoming_hearings,
        'overdue_invoices': overdue_invoices,
        'today_tasks': today_tasks,
        'upcoming_tasks': upcoming_tasks,
    }
    return render(request, 'szkp/dashboard.html', context)
