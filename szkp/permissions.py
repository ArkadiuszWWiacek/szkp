from django.core.exceptions import PermissionDenied

from szkp.models import CaseLawyer


def require_case_access(request, case):
    if not request.user.is_staff:
        if not CaseLawyer.objects.filter(case=case, lawyer__user=request.user).exists():
            raise PermissionDenied


def require_case_access_by_pk(request, case_pk):
    if not request.user.is_staff:
        if not CaseLawyer.objects.filter(case_id=case_pk, lawyer__user=request.user).exists():
            raise PermissionDenied
