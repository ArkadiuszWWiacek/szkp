from django.contrib import admin
from . import models


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
    
@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'created_at', 'updated_at', 'case', 'is_internal')
    search_fields = ('title', 'description', 'case__case_number')
    list_filter = ('document_type',)
    
@admin.register(models.DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'created_by_lawyer', 'created_at')
    search_fields = ('document__title', 'created_by_lawyer__first_name', 'created_by_lawyer__last_name')
    list_filter = ('created_at',)
    
@admin.register(models.Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'case', 'status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'case__case_number',)
    list_filter = ('status', 'issue_date', 'due_date')