from .base import home
from .dashboard import dashboard
from .cases import case_list, case_detail, case_form, case_lawyer_delete, case_lawyer_add
from .clients import client_list, client_form, client_delete
from .court_hearings import court_hearing_form
from .invoice import invoice_form, invoice_list, invoice_mark_paid
from .documents import document_form, document_version_upload
from .tasks import my_tasks, task_detail, task_form, task_delete, task_change_status

__all__ = [
    'home',
    'dashboard',
    'case_list', 'case_detail', 'case_form', 'case_lawyer_delete', 'case_lawyer_add',
    'client_list', 'client_form', 'client_delete',
    'court_hearing_form',
    'document_form', 'document_version_upload',
    'invoice_form', 'invoice_list', 'invoice_mark_paid',
    'my_tasks', 'task_detail', 'task_form', 'task_delete', 'task_change_status',
]
