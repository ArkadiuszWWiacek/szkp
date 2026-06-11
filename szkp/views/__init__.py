from .base import home
from .dashboard import dashboard
from .cases import case_list, case_detail, case_form
from .clients import client_list, client_form, client_delete
from .court_hearings import court_hearing_form
from .invoice import invoice_form
from .tasks import my_tasks, task_form

__all__ = [
    'home',
    'dashboard',
    'case_list', 'case_detail', 'case_form',
    'client_list', 'client_form', 'client_delete',
    'court_hearing_form',
    'invoice_form',
    'my_tasks', 'task_form',
]
