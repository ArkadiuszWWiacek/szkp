import sys
from itertools import chain

import django

from szkp.charts import generate_case_dist_chart
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from szkp.models import (
    Case, CaseStatus,
    CourtHearing, HearingStatus,
    Invoice, InvoiceStatus,
    Task, TaskPriority, TaskStatus,
)

User = get_user_model()


@login_required
def dashboard(request):
    today = timezone.localdate()

    if request.user.is_superuser:
        return _dashboard_superuser(request, today)

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
        .filter(scheduled_at__date__gte=today, status=HearingStatus.PLANOWANY)
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
        .filter(due_date__date=today, status__in=[TaskStatus.NOWE, TaskStatus.W_TOKU])
        .order_by('priority')
        .select_related('case')[:6]
    )

    upcoming_tasks = (
        task_qs
        .filter(
            due_date__date__gt=today,
            due_date__date__lte=today + timezone.timedelta(days=7),
            status__in=[TaskStatus.NOWE, TaskStatus.W_TOKU],
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


def _dashboard_superuser(request, today):
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now()).count()

    feed_cases    = list(Case.objects.select_related('client').order_by('-created_at')[:4])
    feed_invoices = list(Invoice.objects.select_related('case').order_by('-created_at')[:4])
    feed_tasks    = list(Task.objects.select_related('case').order_by('-created_at')[:4])

    feed_items = sorted(
        chain(
            [{'kind': 'case',    'obj': c, 'ts': c.created_at} for c in feed_cases],
            [{'kind': 'invoice', 'obj': i, 'ts': i.created_at} for i in feed_invoices],
            [{'kind': 'task',    'obj': t, 'ts': t.created_at} for t in feed_tasks],
        ),
        key=lambda x: x['ts'],
        reverse=True,
    )[:8]

    cases_by_status = dict(Case.objects.values_list('status').annotate(n=Count('id')))
    cases_total = Case.objects.count()

    context = {
        'today': today,
        'active_cases_count':     Case.objects.filter(
            status__in=[CaseStatus.NOWA, CaseStatus.W_TOKU]
        ).count(),
        'hearings_7d_count':      CourtHearing.objects.filter(
            scheduled_at__date__range=[today, today + timezone.timedelta(days=7)],
            status=HearingStatus.PLANOWANY,
        ).count(),
        'hearings_unassigned':    CourtHearing.objects.filter(
            scheduled_at__date__gte=today,
            status=HearingStatus.PLANOWANY,
            responsible_lawyer__isnull=True,
        ).count(),
        'users_count':            User.objects.filter(is_active=True).count(),
        'invoices_overdue_count': Invoice.objects.filter(
            status=InvoiceStatus.PRZETERMINOWANA
        ).count(),
        'tasks_open_count':       Task.objects.filter(
            status__in=[TaskStatus.NOWE, TaskStatus.W_TOKU]
        ).count(),
        'tasks_urgent_count':     Task.objects.filter(
            status__in=[TaskStatus.NOWE, TaskStatus.W_TOKU],
            priority=TaskPriority.PILNA,
        ).count(),
        'recent_cases':           Case.objects.select_related('client').order_by('-created_at')[:5],
        'recent_invoices':        Invoice.objects.select_related('case').order_by('-issue_date')[:5],
        'users':                  User.objects.select_related('lawyer').order_by('-last_login')[:5],
        'cases_total':            cases_total,
        'cases_by_status':        cases_by_status,
        'case_dist_chart':        generate_case_dist_chart(cases_by_status, cases_total),
        'active_sessions':        active_sessions,
        'django_version':         f'{django.VERSION[0]}.{django.VERSION[1]}.{django.VERSION[2]}',
        'python_version':         f'{sys.version_info.major}.{sys.version_info.minor}',
        'feed_items':             feed_items,
    }
    return render(request, 'szkp/dashboard_superuser.html', context)
