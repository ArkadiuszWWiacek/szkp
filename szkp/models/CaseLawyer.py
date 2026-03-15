from django.db import models
from .Case import Case
from .Lawyer import Lawyer

## Model CaseLawyer
class CaseLawyerRole(models.TextChoices):
    PROWADZACY = 'prowadzacy', 'Prowadzący'
    ASYSTENT = 'asystent', 'Asystent'
    DORADCA = 'doradca', 'Doradca'
        
class CaseLawyer(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, db_column='caseid')
    lawyer = models.ForeignKey(Lawyer, on_delete=models.RESTRICT, db_column='lawyerid')
    role = models.CharField(max_length=20, choices=CaseLawyerRole.choices, null=False)
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(blank=True, null=True)
    responsible_flag = models.BooleanField(default=False)

    class Meta:
        db_table = 'CASELAWYERS'
        unique_together = [('case', 'lawyer')]