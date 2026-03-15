from django.db import models
from .Client import Client

## Model Case
class CaseType(models.TextChoices):
    CYWILNA = 'cywilna', 'Cywilna'
    KARNA = 'karna', 'Karna'
    GOSPODARCZA = 'gospodarcza', 'Gospodarcza'
    ADMINISTRACYJNA = 'administracyjna', 'Administracyjna'
    RODZINNA = 'rodzinna', 'Rodzinna'
    PRACOWNICZA = 'pracownicza', 'Pracownicza'

class CaseStatus(models.TextChoices):
    NOWA = 'nowa', 'Nowa'
    W_TOKU = 'w_toku', 'W toku'
    ZAWIESZONA = 'zawieszona', 'Zawieszona'
    ZAKOŃCZONA = 'zakończona', 'Zakończona'
    ARCHIWALNA = 'archiwalna', 'Archiwalna'

class CasePriority(models.TextChoices):
    NISKA = 'niska', 'Niska'
    NORMALNA = 'normalna', 'Normalna'
    WYSOKA = 'wysoka', 'Wysoka'
    PILNA = 'pilna', 'Pilna'

class Case(models.Model):
    client = models.ForeignKey(Client, on_delete=models.RESTRICT, db_column='clientid')
    case_number = models.CharField(max_length=50, unique=True, null=False)
    court_case_number = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    title = models.CharField(max_length=300, null=False)
    description = models.TextField(blank=True)
    case_type = models.CharField(max_length=30, choices=CaseType.choices, null=False)
    status = models.CharField(max_length=20, choices=CaseStatus.choices, default=CaseStatus.NOWA)
    case_priority = models.CharField(max_length=10, choices=CasePriority.choices, default=CasePriority.NORMALNA)
    opened_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'CASES'
        indexes = [
            models.Index(fields=['court_case_number'], name='idx_cases_courtcase'),
        ]

    def __str__(self):
        return f"{self.case_number} - {self.title}"

