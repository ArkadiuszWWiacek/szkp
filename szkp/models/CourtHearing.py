from django.db import models
from .Case import Case
from .Lawyer import Lawyer

## Model CourtHearing
class HearingStatus(models.TextChoices):
    PLANOWANY = 'planowany', 'Planowany'
    ODBYTY = 'odbyty', 'Odbyty'
    ODROCZONY = 'odroczony', 'Odroczony'
    ODWOŁANY = 'odwołany', 'Odwołany'

class HearingType(models.TextChoices):
    ROZPRAWA = 'rozprawa', 'Rozprawa'
    POSIEDZENIE = 'posiedzenie', 'Posiedzenie'
    MEDIACJA = 'mediacja', 'Mediacja'

class CourtHearing(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, db_column='caseid')
    responsible_lawyer = models.ForeignKey(Lawyer, on_delete=models.SET_NULL, blank=True, null=True, db_column='responsiblawyerid')
    court_name = models.CharField(max_length=200, null=False)
    courtroom = models.CharField(max_length=50, blank=True)
    judge_name = models.CharField(max_length=100, blank=True)
    hearing_type = models.CharField(max_length=20, choices=HearingType.choices, null=False)
    scheduled_at = models.DateTimeField(null=False)
    status = models.CharField(max_length=20, choices=HearingStatus.choices, default=HearingStatus.PLANOWANY)
    notes = models.TextField(blank=True)
    reminder_minutes_before = models.IntegerField(default=1440)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.case} / {self.scheduled_at:%Y-%m-%d} / {self.court_name}"

    class Meta:
        db_table = 'COURTHEARINGS'