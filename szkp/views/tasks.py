from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Case as DbCase, IntegerField, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from szkp.forms import TaskForm
from szkp.models import Case, CaseLawyer, Lawyer, Task, TaskPriority, TaskStatus


@login_required
def my_tasks(request):
    today = timezone.localdate()
    status_filter = request.GET.get('status', '')
    period_filter = request.GET.get('period', '')
    case_number_filter = request.GET.get('case_number', '')

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
    elif period_filter == 'overdue':
        qs = qs.filter(due_date__date__lt=today).exclude(status=TaskStatus.ZAKOŃCZONE)

    if case_number_filter:
        qs = qs.filter(case__case_number__icontains=case_number_filter)

    qs = qs.annotate(priority_rank=priority_rank).order_by('priority_rank', 'due_date')

    context = {
        'tasks': qs,
        'status_filter': status_filter,
        'period_filter': period_filter,
        'case_number_filter': case_number_filter,
        'status_choices': TaskStatus.choices,
        'today': today,
    }
    return render(request, 'szkp/my_tasks.html', context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not request.user.is_staff:
        lawyer = get_object_or_404(Lawyer, user=request.user)
        if task.assigned_lawyer != lawyer:
            raise PermissionDenied
    subtasks = task.task_set.select_related('assigned_lawyer__user').order_by('created_at')
    return render(request, 'szkp/task_detail.html', {
        'task': task,
        'subtasks': subtasks,
    })


def _task_context(task, form, parent_pk=None, case=None, lawyer_choices=None):
    return {
        'task': task,
        'form': form,
        'priority_choices': TaskPriority.choices,
        'status_choices': TaskStatus.choices,
        'can_add_subtask': task is not None and task.parent_task_id is None,
        'parent_pk': parent_pk,
        'case': case,
        'lawyer_choices': lawyer_choices,
    }


@login_required
def task_form(request, pk=None, case_pk=None):
    task = get_object_or_404(Task.objects.select_related('case'), pk=pk) if pk else None
    lawyer = get_object_or_404(Lawyer, user=request.user)

    case = None
    if case_pk:
        case = get_object_or_404(Case, pk=case_pk)
        if not request.user.is_staff:
            if not CaseLawyer.objects.filter(case=case, lawyer=lawyer).exists():
                raise PermissionDenied

    if task and task.case and not case:
        case = task.case
        if not request.user.is_staff:
            if not CaseLawyer.objects.filter(case=case, lawyer=lawyer).exists():
                raise PermissionDenied

    lawyer_choices = None
    case_lawyer_pks = None
    if case:
        case_lawyers = case.caselawyer_set.select_related('lawyer').order_by('role')
        lawyer_choices = [
            (cl.lawyer.pk, f"{cl.lawyer.first_name} {cl.lawyer.last_name} ({cl.get_role_display()})")
            for cl in case_lawyers
        ]
        case_lawyer_pks = [cl.lawyer.pk for cl in case_lawyers]

    redirect_url = (
        reverse('szkp:case_detail', kwargs={'pk': case.pk}) + '?tab=zadania'
        if case else reverse('szkp:my_tasks')
    )

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, case_lawyer_pks=case_lawyer_pks)
        if form.is_valid():
            obj = form.save(commit=False)
            assigned_pk = form.cleaned_data.get('assigned_lawyer')
            if case and assigned_pk:
                obj.assigned_lawyer_id = assigned_pk
            elif not task:
                obj.assigned_lawyer = lawyer
            if not task:
                obj.created_by = lawyer
            if pk:
                if obj.status == TaskStatus.ZAKOŃCZONE and obj.has_unfinished_subtasks:
                    form.add_error('status', 'Nie można zakończyć zadania — najpierw zakończ wszystkie podzadania.')
                    return render(request, 'szkp/task_form.html',
                                  _task_context(task, form, case=case, lawyer_choices=lawyer_choices))
            else:
                parent_pk_val = request.POST.get('parent_task')
                if parent_pk_val:
                    obj.parent_task_id = int(parent_pk_val)
                if case:
                    obj.case = case
            obj.save()
            messages.success(request, 'Zadanie zostało zapisane.')
            return redirect(redirect_url)

        parent_pk = request.POST.get('parent_task')
        return render(
            request,
            'szkp/task_form.html',
            _task_context(task, form, parent_pk=parent_pk, case=case, lawyer_choices=lawyer_choices),
        )

    parent_pk = request.GET.get('parent')
    initial = {} if task else {'assigned_lawyer': lawyer.pk}
    form = TaskForm(instance=task, case_lawyer_pks=case_lawyer_pks, initial=initial)
    return render(
        request,
        'szkp/task_form.html',
        _task_context(task, form, parent_pk=parent_pk, case=case, lawyer_choices=lawyer_choices),
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
