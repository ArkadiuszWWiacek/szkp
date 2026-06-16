from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from szkp.forms import CourtHearingForm
from szkp.models import Case, CourtHearing, HearingStatus, HearingType
from szkp.permissions import require_case_access


def _form_context(case, hearing, form_data, errors):
    return {
        'case': case,
        'hearing': hearing,
        'form_data': form_data,
        'errors': errors,
        'hearing_type_choices': HearingType.choices,
        'status_choices': HearingStatus.choices,
    }


@login_required
def court_hearing_form(request, case_pk, pk=None):
    case = get_object_or_404(Case, pk=case_pk)
    hearing = get_object_or_404(CourtHearing, pk=pk, case=case) if pk else None

    require_case_access(request, case)

    redirect_url = (
        reverse('szkp:case_detail', kwargs={'pk': case_pk}) + '?tab=terminy'
    )

    if request.method == 'POST':
        form = CourtHearingForm(request.POST, is_new=(hearing is None))
        if form.is_valid():
            cd = form.cleaned_data
            obj = hearing or CourtHearing(case=case)
            obj.court_name              = cd['court_name']
            obj.hearing_type            = cd['hearing_type']
            obj.scheduled_at            = cd['scheduled_at']
            obj.courtroom               = cd.get('courtroom') or ''
            obj.judge_name              = cd.get('judge_name') or ''
            obj.notes                   = cd.get('notes') or ''
            obj.reminder_minutes_before = cd.get('reminder_minutes_before') or 1440
            obj.status = (
                cd.get('status') or HearingStatus.PLANOWANY
                if hearing else HearingStatus.PLANOWANY
            )
            obj.save()
            messages.success(request, 'Termin został zapisany.')
            return redirect(redirect_url)

        return render(
            request,
            'szkp/court_hearing_form.html',
            _form_context(case, hearing, request.POST, form.errors),
        )

    if hearing:
        form_data = {
            'court_name':              hearing.court_name,
            'hearing_type':            hearing.hearing_type,
            'scheduled_at':            timezone.localtime(hearing.scheduled_at).strftime('%Y-%m-%dT%H:%M'),
            'status':                  hearing.status,
            'reminder_minutes_before': hearing.reminder_minutes_before,
            'courtroom':               hearing.courtroom,
            'judge_name':              hearing.judge_name,
            'notes':                   hearing.notes,
        }
    else:
        form_data = {'reminder_minutes_before': 1440}

    return render(
        request,
        'szkp/court_hearing_form.html',
        _form_context(case, hearing, form_data, {}),
    )
