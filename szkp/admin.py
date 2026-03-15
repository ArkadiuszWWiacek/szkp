from django.contrib import admin
from . import models



admin.site.register(models.Case)
admin.site.register(models.CaseLawyer)
admin.site.register(models.Document)
admin.site.register(models.CourtHearing)
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