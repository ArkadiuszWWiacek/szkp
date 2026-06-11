from .base import home
from .dashboard import dashboard
from .cases import case_list, case_detail
from .clients import client_list, client_form, client_delete
from .tasks import my_tasks

__all__ = [
    'home',
    'dashboard',
    'case_list', 'case_detail',
    'client_list', 'client_form', 'client_delete',
    'my_tasks',
]
