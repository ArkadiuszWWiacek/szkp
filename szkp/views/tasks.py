from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case as DbCase, IntegerField, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from szkp.forms import TaskForm
from szkp.models import Lawyer, Task, TaskPriority, TaskStatus


@login_required
def my_tasks(request):
    today = timezone.localdate()
    status_filter = request.GET.get('status', '')
    period_filter = request.GET.get('period', '')

    lawyer = get_object_or_404(Lawyer, user=request.user)

    priority_rank = DbCase(
        When(priority=TaskPriority.PILNA,    then=Value(0)),
        When(priority=TaskPriority.WYSOKA,   then=Value(1)),
        When(priority=TaskPriority.NORMALNA, then=Value(2)),
        When(priority=TaskPriority.NISKA,    then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )

    qs = (Task.objects
          .filter(assigned_lawyer=lawyer, parent_task__isnull=True)
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


def _task_context(task, form_data, errors, parent_pk=None):
    return {
        'task': task,
        'form_data': form_data,
        'errors': errors,
        'priority_choices': TaskPriority.choices,
        'status_choices': TaskStatus.choices,
        'can_add_subtask': task is not None and task.parent_task_id is None,
        'parent_pk': parent_pk,
    }


@login_required
def task_form(request, pk=None):
    task = get_object_or_404(Task, pk=pk) if pk else None
    lawyer = get_object_or_404(Lawyer, user=request.user)
    redirect_url = reverse('szkp:my_tasks')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            obj = task or Task(assigned_lawyer=lawyer, created_by=lawyer)
            obj.title       = cd['title']
            obj.description = cd.get('description', '')
            obj.priority    = cd.get('priority') or TaskPriority.NORMALNA
            obj.due_date    = cd.get('due_date')
            if pk:
                new_status = cd.get('status') or TaskStatus.NOWE
                if new_status == TaskStatus.ZAKOŃCZONE and obj.has_unfinished_subtasks:
                    errors = {'status': ['Nie można zakończyć zadania — najpierw zakończ wszystkie podzadania.']}
                    return render(request, 'szkp/task_form.html', _task_context(task, request.POST, errors))
                obj.status = new_status
            else:
                parent_pk = request.POST.get('parent_task')
                if parent_pk:
                    obj.parent_task_id = int(parent_pk)
            obj.save()
            messages.success(request, 'Zadanie zostało zapisane.')
            return redirect(redirect_url)

        parent_pk = request.POST.get('parent_task')
        return render(
            request,
            'szkp/task_form.html',
            _task_context(task, request.POST, form.errors, parent_pk=parent_pk),
        )

    parent_pk = request.GET.get('parent')
    if task:
        form_data = {
            'title':       task.title,
            'description': task.description,
            'priority':    task.priority,
            'status':      task.status,
            'due_date':    task.due_date.strftime('%Y-%m-%dT%H:%M') if task.due_date else '',
        }
    else:
        form_data = {
            'priority': TaskPriority.NORMALNA,
            'status':   TaskStatus.NOWE,
        }

    return render(
        request,
        'szkp/task_form.html',
        _task_context(task, form_data, {}, parent_pk=parent_pk),
    )


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Zadanie zostało usunięte.')
        return redirect(reverse('szkp:my_tasks'))
    return render(request, 'szkp/task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def task_change_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    new_status = request.POST.get('status', '')
    next_url = request.POST.get('next') or reverse('szkp:my_tasks')
    if new_status in dict(TaskStatus.choices):
        if new_status == TaskStatus.ZAKOŃCZONE and task.has_unfinished_subtasks:
            messages.error(request, 'Nie można zakończyć zadania — najpierw zakończ wszystkie podzadania.')
            return redirect(next_url)
        task.status = new_status
        task.save()
        messages.success(request, f'Status zadania zmieniony na: {task.get_status_display()}')
    return redirect(next_url)
