from django.contrib import admin
from . import models


admin.site.register(models.Client)
admin.site.register(models.Lawyer)
admin.site.register(models.Case)
admin.site.register(models.CaseLawyer)
admin.site.register(models.Document)
admin.site.register(models.CourtHearing)
admin.site.register(models.Invoice)
admin.site.register(models.Task)