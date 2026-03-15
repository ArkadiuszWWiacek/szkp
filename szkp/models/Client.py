from django.db import models
from django.core.validators import RegexValidator
from django.forms import ValidationError

## Model Client
class ClientType(models.TextChoices):
    OSOBA_FIZYCZNA = 'osobafizyczna', 'Osoba fizyczna'
    FIRMA = 'firma', 'Firma'

class Client(models.Model):
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    companyname = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=20, choices=ClientType.choices, null=False)
    pesel = models.CharField(max_length=11, blank=True, null=True, validators=[RegexValidator(r'^\d{11}$')])
    nip = models.CharField(max_length=13, blank=True, null=True, validators=[RegexValidator(r'^\d{13}$')])
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address_street = models.CharField(max_length=200, blank=True, null=True)
    address_city = models.CharField(max_length=100, blank=True, null=True)
    address_zip = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, default='Polska', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'CLIENTS'

    def clean(self):
        if self.type == 'osobafizyczna':
            if not self.pesel:
                raise ValidationError('PESEL wymagany dla osoby fizycznej.')
            self.nip = None
            self.companyname = None
        elif self.type == 'firma':
            if not self.nip:
                raise ValidationError('NIP wymagany dla firmy.')
            self.pesel = None

