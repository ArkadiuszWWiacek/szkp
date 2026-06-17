from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

User = get_user_model()


@login_required
def user_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    users = User.objects.order_by('username')
    return render(request, 'szkp/user_list_su.html', {'users': users})


@login_required
def user_toggle_active(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    return redirect('szkp:user_list')
