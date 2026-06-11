from django.db import models
from django.utils import timezone
from .Lawyer import Lawyer

## Model Task
class TaskPriority(models.TextChoices):
    NISKA = 'niska', 'Niska'
    NORMALNA = 'normalna', 'Normalna'
    WYSOKA = 'wysoka', 'Wysoka'
    PILNA = 'pilna', 'Pilna'

class TaskStatus(models.TextChoices):
    NOWE = 'nowe', 'Nowe'
    W_TOKU = 'w_toku', 'W toku'
    ZAWIESZONE = 'zawieszone', 'Zawieszone'
    ZAKOŃCZONE = 'zakończone', 'Zakończone'
    ARCHIWALNE = 'archiwalne', 'Archiwalne'

class Task(models.Model):
    case = models.ForeignKey('Case', on_delete=models.CASCADE, blank=True, null=True, db_column='caseid')
    assigned_lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE, related_name='assigned_tasks', db_column='assignedlawyerid')
    created_by = models.ForeignKey(Lawyer, on_delete=models.CASCADE, related_name='created_tasks', db_column='createdby')
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, db_column='parenttaskid')
    title = models.CharField(max_length=300, null=False)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=TaskPriority.choices, default=TaskPriority.NORMALNA)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.NOWE)
    due_date = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.status == TaskStatus.ZAKOŃCZONE and self.completed_at is None:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'TASKS'
