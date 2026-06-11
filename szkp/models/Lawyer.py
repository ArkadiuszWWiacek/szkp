from django.conf import settings
from django.db import models

## Model Lawyer
class Lawyer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='lawyer',
    )
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    bar_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    activeflag = models.BooleanField(default=True)
    defaultrate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'LAWYERS'
