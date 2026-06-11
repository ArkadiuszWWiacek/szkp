from django.urls import path
from . import views

app_name = 'szkp'

urlpatterns = [
    path('',                        views.home,         name='home'),
    path('pulpit/',                 views.dashboard,    name='dashboard'),
    path('sprawy/',                 views.case_list,    name='case_list'),
    path('sprawy/nowy/',            views.case_form,    name='case_new'),
    path('sprawy/<int:pk>/',        views.case_detail,  name='case_detail'),
    path('sprawy/<int:pk>/edytuj/', views.case_form,    name='case_edit'),
    path('klienci/',                views.client_list,  name='client_list'),
    path('klienci/nowy/',           views.client_form,  name='client_new'),
    path('klienci/<int:pk>/edytuj/',views.client_form,   name='client_edit'),
    path('klienci/<int:pk>/usun/', views.client_delete, name='client_delete'),
    path('sprawy/<int:case_pk>/terminy/nowy/',
         views.court_hearing_form, name='court_hearing_new'),
    path('sprawy/<int:case_pk>/terminy/<int:pk>/edytuj/',
         views.court_hearing_form, name='court_hearing_edit'),
    path('faktury/', views.invoice_list, name='invoice_list'),
    path('faktury/<int:pk>/oplacona/', views.invoice_mark_paid, name='invoice_mark_paid'),
    path('sprawy/<int:case_pk>/faktury/nowa/',
         views.invoice_form, name='invoice_new'),
    path('sprawy/<int:case_pk>/faktury/<int:pk>/edytuj/',
         views.invoice_form, name='invoice_edit'),
    path('zadania/',                      views.my_tasks,           name='my_tasks'),
    path('zadania/nowe/',                 views.task_form,          name='task_new'),
    path('zadania/<int:pk>/edytuj/',      views.task_form,          name='task_edit'),
    path('zadania/<int:pk>/usun/',         views.task_delete,        name='task_delete'),
    path('zadania/<int:pk>/status/',      views.task_change_status, name='task_change_status'),
]
