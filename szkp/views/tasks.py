from django.contrib.auth.decorators import login_required
from django.db.models import Case as DbCase, IntegerField, Value, When
from django.shortcuts import render
from django.utils import timezone

from szkp.models import Task, TaskPriority, TaskStatus


@login_required
def my_tasks(request):
    today = timezone.localdate()
    status_filter = request.GET.get('status', '')
    period_filter = request.GET.get('period', '')

    priority_rank = DbCase(
        When(priority=TaskPriority.PILNA,    then=Value(0)),
        When(priority=TaskPriority.WYSOKA,   then=Value(1)),
        When(priority=TaskPriority.NORMALNA, then=Value(2)),
        When(priority=TaskPriority.NISKA,    then=Value(3)),
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
