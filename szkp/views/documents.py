import os

import markdown as md_lib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from szkp.forms import DocumentForm, DocumentVersionForm
from szkp.models import Case, Document, DocumentType, DocumentVersion, Lawyer
from szkp.permissions import require_case_access


def _save_file(uploaded_file, case_pk):
    """Zapisuje plik do media/documents/case_<pk>/ i zwraca ścieżkę względną."""
    directory = os.path.join(settings.MEDIA_ROOT, 'documents', f'case_{case_pk}')
    os.makedirs(directory, exist_ok=True)
    name = uploaded_file.name
    filepath = os.path.join(directory, name)
    base, ext = os.path.splitext(name)
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(directory, f'{base}_{counter}{ext}')
        counter += 1
    with open(filepath, 'wb+') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return os.path.relpath(filepath, settings.MEDIA_ROOT)


def _next_version_number(document):
    max_ver = document.documentversion_set.aggregate(m=Max('version_number'))['m']
    return (max_ver or 0) + 1


def _form_context(case, document, form):
    return {
        'case': case,
        'document': document,
        'form': form,
        'document_type_choices': DocumentType.choices,
    }


@login_required
def document_detail(request, case_pk, pk):
    case = get_object_or_404(Case, pk=case_pk)
    document = get_object_or_404(Document, pk=pk, case=case)
    require_case_access(request, case)
    versions = document.documentversion_set.select_related('created_by_lawyer').order_by('version_number')
    try:
        ver_num = int(request.GET.get('wersja', 0))
    except ValueError:
        ver_num = 0
    selected = versions.filter(version_number=ver_num).first() or versions.last()
    file_ext = os.path.splitext(selected.file_path)[1].lower() if selected else ''

    preview_content = None
    preview_html = None
    if selected and file_ext in ('.txt', '.md'):
        abs_path = os.path.join(settings.MEDIA_ROOT, selected.file_path)
        try:
            with open(abs_path, encoding='utf-8') as f:
                raw = f.read()
            if file_ext == '.md':
                preview_html = md_lib.markdown(raw, extensions=['tables', 'fenced_code'])
            else:
                preview_content = raw
        except (OSError, UnicodeDecodeError):
            pass

    return render(request, 'szkp/document_detail.html', {
        'case': case,
        'document': document,
        'versions': versions,
        'selected_version': selected,
        'file_ext': file_ext,
        'preview_content': preview_content,
        'preview_html': preview_html,
    })


@login_required
def document_form(request, case_pk, pk=None):
    case = get_object_or_404(Case, pk=case_pk)
    document = get_object_or_404(Document, pk=pk, case=case) if pk else None
    require_case_access(request, case)

    redirect_url = reverse('szkp:case_detail', kwargs={'pk': case_pk}) + '?tab=dokumenty'

    is_su = request.user.is_superuser
    template = 'szkp/document_form_su.html' if is_su else 'szkp/document_form.html'

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document, is_new=(document is None))
        if form.is_valid():
            obj = form.save(commit=False)
            if not document:
                obj.case = case
            obj.save()

            uploaded = form.cleaned_data.get('file')
            if uploaded:
                lawyer = get_object_or_404(Lawyer, user=request.user)
                DocumentVersion.objects.create(
                    document=obj,
                    created_by_lawyer=lawyer,
                    version_number=_next_version_number(obj),
                    file_path=_save_file(uploaded, case_pk),
                )

            messages.success(request, 'Dokument został zapisany.')
            return redirect(redirect_url)

        return render(request, template, _form_context(case, document, form))

    form = DocumentForm(instance=document, is_new=(document is None))
    return render(request, template, _form_context(case, document, form))


@login_required
def document_version_upload(request, case_pk, document_pk):
    case = get_object_or_404(Case, pk=case_pk)
    document = get_object_or_404(Document, pk=document_pk, case=case)
    require_case_access(request, case)

    redirect_url = reverse('szkp:case_detail', kwargs={'pk': case_pk}) + '?tab=dokumenty'

    if request.method == 'POST':
        form = DocumentVersionForm(request.POST, request.FILES)
        if form.is_valid():
            lawyer = get_object_or_404(Lawyer, user=request.user)
            DocumentVersion.objects.create(
                document=document,
                created_by_lawyer=lawyer,
                version_number=_next_version_number(document),
                file_path=_save_file(form.cleaned_data['file'], case_pk),
            )
            messages.success(request, 'Nowa wersja została dodana.')
            return redirect(redirect_url)

        return render(
            request,
            'szkp/document_version_upload.html',
            {'case': case, 'document': document, 'form': form},
        )

    form = DocumentVersionForm()
    return render(
        request,
        'szkp/document_version_upload.html',
        {'case': case, 'document': document, 'form': form},
    )
