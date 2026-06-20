from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Case as DbCase, IntegerField, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from szkp.forms import TaskForm, TaskFormSU, SubtaskInlineFormSet
from szkp.models import Case, CaseLawyer, Lawyer, Task, TaskPriority, TaskStatus


@login_required
def my_tasks(request):
    if request.user.is_superuser:
        q = request.GET.get('q', '').strip()
        sort = request.GET.get('sort', 'due_date')
        direction = request.GET.get('dir', 'asc')

        valid_sort_fields = {
            'assigned_lawyer': 'assigned_lawyer__last_name',
            'case':            'case__case_number',
            'due_date':        'due_date',
            'status':          'status',
        }
        sort_field = valid_sort_fields.get(sort, 'due_date')
        if direction == 'desc':
            sort_field = f'-{sort_field}'

        tasks = (Task.objects
                 .filter(parent_task__isnull=True)
                 .select_related('case', 'assigned_lawyer')
                 .prefetch_related('task_set__assigned_lawyer', 'task_set__case'))
        if q:
            tasks = tasks.filter(title__icontains=q)
        tasks = tasks.order_by(sort_field)

        return render(request, 'szkp/task_list_su.html', {
            'tasks': tasks,
            'q': q,
            'sort': sort,
            'direction': direction,
        })

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


def _task_context(task, form, parent_pk=None, case=None, lawyer_choices=None, formset=None):
    return {
        'task': task,
        'form': form,
        'priority_choices': TaskPriority.choices,
        'status_choices': TaskStatus.choices,
        'can_add_subtask': task is not None and task.parent_task_id is None,
        'parent_pk': parent_pk,
        'case': case,
        'lawyer_choices': lawyer_choices,
        'formset': formset,
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

    is_su = request.user.is_superuser
    FormClass = TaskFormSU if is_su else TaskForm
    template = 'szkp/task_form_su.html' if is_su else 'szkp/task_form.html'
    is_parent_task = task is not None and task.parent_task_id is None

    if request.method == 'POST':
        if is_su:
            form = TaskFormSU(
                request.POST, instance=task,
                case_lawyer_pks=case_lawyer_pks,
                exclude_pk=task.pk if task else None,
            )
            formset = SubtaskInlineFormSet(request.POST, instance=task) if is_parent_task else None
        else:
            form = TaskForm(request.POST, instance=task, case_lawyer_pks=case_lawyer_pks)
            formset = None

        if form.is_valid() and (formset is None or formset.is_valid()):
            obj = form.save(commit=False)

            if is_su:
                assigned = form.cleaned_data.get('assigned_lawyer')
                if assigned:
                    obj.assigned_lawyer = assigned
                created = form.cleaned_data.get('created_by')
                if created:
                    obj.created_by = created
                elif not task:
                    obj.created_by = lawyer
                case_obj = form.cleaned_data.get('case')
                if case_obj is not None:
                    obj.case = case_obj
                if not task:
                    parent_obj = form.cleaned_data.get('parent_task')
                    if parent_obj:
                        obj.parent_task = parent_obj
            else:
                assigned_pk = form.cleaned_data.get('assigned_lawyer')
                if case and assigned_pk:
                    obj.assigned_lawyer_id = assigned_pk
                elif not task:
                    obj.assigned_lawyer = lawyer
                if not task:
                    obj.created_by = lawyer
                    parent_pk_val = request.POST.get('parent_task')
                    if parent_pk_val:
                        obj.parent_task_id = int(parent_pk_val)
                    if case:
                        obj.case = case

            if pk and obj.status == TaskStatus.ZAKOŃCZONE and obj.has_unfinished_subtasks:
                form.add_error('status', 'Nie można zakończyć zadania — najpierw zakończ wszystkie podzadania.')
                return render(request, template,
                              _task_context(task, form, case=case, lawyer_choices=lawyer_choices,
                                            formset=formset))

            obj.save()

            if formset:
                new_instances = formset.save(commit=False)
                for inst in new_instances:
                    if not inst.pk:
                        inst.created_by = lawyer
                        if not inst.assigned_lawyer_id:
                            inst.assigned_lawyer = obj.assigned_lawyer
                    inst.save()
                for deleted in formset.deleted_objects:
                    deleted.delete()

            messages.success(request, 'Zadanie zostało zapisane.')
            return redirect(redirect_url)

        parent_pk = request.POST.get('parent_task') if not is_su else None
        return render(
            request,
            template,
            _task_context(task, form, parent_pk=parent_pk, case=case, lawyer_choices=lawyer_choices,
                          formset=formset),
        )

    parent_pk = request.GET.get('parent') if not is_su else None
    initial = {} if task else ({'assigned_lawyer': lawyer.pk} if not is_su else {})
    if is_su:
        form = TaskFormSU(
            instance=task, case_lawyer_pks=case_lawyer_pks,
            exclude_pk=task.pk if task else None, initial=initial,
        )
        formset = SubtaskInlineFormSet(instance=task) if is_parent_task else None
    else:
        form = TaskForm(instance=task, case_lawyer_pks=case_lawyer_pks, initial=initial)
        formset = None

    return render(
        request,
        template,
        _task_context(task, form, parent_pk=parent_pk, case=case, lawyer_choices=lawyer_choices,
                      formset=formset),
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
