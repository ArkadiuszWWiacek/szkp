from django.contrib import admin
from . import models


admin.site.register(models.Document)
admin.site.register(models.Invoice)
admin.site.register(models.Task)

@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'pesel', 'company_name', 'nip', 'email', 'phone', 'type', 'address_street', 'address_city', 'address_zip', 'country')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('type',)

@admin.register(models.Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'bar_number', 'specialization', 'email', 'phone')
    search_fields = ('first_name', 'last_name', 'bar_number', 'specialization', 'email')
    list_filter = ('specialization', 'activeflag')
    
@admin.register(models.Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'title', 'client', 'case_type', 'status', 'case_priority', 'opened_at', 'closed_at')
    search_fields = ('case_number', 'title', 'court_case_number')
    list_filter = ('case_type', 'status', 'case_priority')
    
@admin.register(models.CaseLawyer)
class CaseLawyerAdmin(admin.ModelAdmin):
    list_display = ('case', 'lawyer', 'role', 'assigned_at', 'unassigned_at')
    search_fields = ('case__case_number', 'lawyer__first_name', 'lawyer__last_name')
    list_filter = ('role',)
    
@admin.register(models.CourtHearing)
class CourtHearingAdmin(admin.ModelAdmin):
    list_display = ('case', 'responsible_lawyer', 'court_name', 'courtroom', 'judge_name', 'hearing_type', 'scheduled_at', 'status')
    search_fields = ('case__case_number', 'court_name', 'judge_name')
    list_filter = ('status', 'hearing_type', 'court_name', 'judge_name')