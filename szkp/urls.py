from django.urls import path
from . import views

app_name = 'szkp'

urlpatterns = [
    path('',                        views.home,         name='home'),
    path('pulpit/',                 views.dashboard,    name='dashboard'),
    path('sprawy/',                 views.case_list,    name='case_list'),
    path('sprawy/<int:pk>/',        views.case_detail,  name='case_detail'),
    path('klienci/',                views.client_list,  name='client_list'),
    path('klienci/nowy/',           views.client_form,  name='client_new'),
    path('klienci/<int:pk>/edytuj/',views.client_form,  name='client_edit'),
    path('zadania/',                views.my_tasks,     name='my_tasks'),
]
