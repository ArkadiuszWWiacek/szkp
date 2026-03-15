from django.urls import path
from . import views

app_name = 'szkp'

urlpatterns = [
    path('', views.home, name='home'),
]