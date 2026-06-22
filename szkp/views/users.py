from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from szkp.forms import UserFormSU
from szkp.view_utils import apply_sorting, apply_pagination

User = get_user_model()


@login_required
def user_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    qs = User.objects.all()

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )

    sort = request.GET.get('sort', 'username')
    direction = request.GET.get('dir', 'asc')
    qs = apply_sorting(qs, sort, direction, {
        'username':    'username',
        'email':       'email',
        'date_joined': 'date_joined',
        'last_login':  'last_login',
        'is_staff':    'is_staff',
    }, 'username')
    page_obj = apply_pagination(qs, request.GET.get('page', 1))

    return render(request, 'szkp/user_list_su.html', {
        'page_obj':  page_obj,
        'users':     page_obj,
        'q':         q,
        'sort':      sort,
        'direction': direction,
    })


@login_required
def user_toggle_active(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    return redirect('szkp:user_list')


@login_required
def user_form(request, pk=None):
    if not request.user.is_superuser:
        raise PermissionDenied

    instance = get_object_or_404(User, pk=pk) if pk else None
    is_new = instance is None

    if request.method == 'POST':
        form = UserFormSU(request.POST, is_new=is_new)
        if form.is_valid():
            data = form.cleaned_data
            qs = User.objects.filter(username=data['username'])
            if pk:
                qs = qs.exclude(pk=pk)
            if qs.exists():
                form.add_error('username', 'Użytkownik o tym loginie już istnieje.')
            else:
                if is_new:
                    User.objects.create_user(
                        username=data['username'],
                        email=data.get('email', ''),
                        password=data['password'],
                        first_name=data.get('first_name', ''),
                        last_name=data.get('last_name', ''),
                        is_staff=data.get('is_staff', False),
                        is_active=data.get('is_active', True),
                    )
                else:
                    instance.username = data['username']
                    instance.email = data.get('email', '')
                    instance.first_name = data.get('first_name', '')
                    instance.last_name = data.get('last_name', '')
                    instance.is_staff = data.get('is_staff', False)
                    instance.is_active = data.get('is_active', True)
                    if data.get('password'):
                        instance.set_password(data['password'])
                    instance.save()
                return redirect('szkp:user_list')
    else:
        form = UserFormSU(is_new=is_new, initial={
            'username':   instance.username   if instance else '',
            'email':      instance.email      if instance else '',
            'first_name': instance.first_name if instance else '',
            'last_name':  instance.last_name  if instance else '',
            'is_staff':   instance.is_staff   if instance else False,
            'is_active':  instance.is_active  if instance else True,
        })

    return render(request, 'szkp/user_form_su.html', {
        'form':     form,
        'instance': instance,
        'is_new':   is_new,
    })
