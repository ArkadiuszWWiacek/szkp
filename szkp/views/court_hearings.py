from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from szkp.forms import CourtHearingForm
from szkp.models import Case, CourtHearing, HearingStatus, HearingType
from szkp.permissions import require_case_access


def _form_context(case, hearing, form):
    return {
        'case': case,
        'hearing': hearing,
        'form': form,
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
        form = CourtHearingForm(request.POST, instance=hearing, is_new=(hearing is None))
        if form.is_valid():
            obj = form.save(commit=False)
            if not hearing:
                obj.case = case
                obj.status = HearingStatus.PLANOWANY
            obj.save()
            messages.success(request, 'Termin został zapisany.')
            return redirect(redirect_url)

        return render(
            request,
            'szkp/court_hearing_form.html',
            _form_context(case, hearing, form),
        )

    form = CourtHearingForm(instance=hearing, is_new=(hearing is None))
    return render(
        request,
        'szkp/court_hearing_form.html',
        _form_context(case, hearing, form),
    )
