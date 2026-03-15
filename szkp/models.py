from django.db import models
from django.core.validators import RegexValidator
from django.forms import ValidationError
from decimal import Decimal



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

## Model Lawyer
class Lawyer(models.Model):
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


## Model Documents
class DocumentType(models.TextChoices):
    POZEW = 'pozew', 'Pozew'
    ODPOWIEDZ = 'odpowiedz', 'Odpowiedź'
    PISMO_SADOWE = 'pismo_sadowe', 'Pismo sądowe'
    NOTATKA = 'notatka', 'Notatka'
    UMOWA = 'umowa', 'Umowa'
    DOWOD = 'dowod', 'Dowód'
    WYROK = 'wyrok', 'Wyrok'
    UGODA = 'ugoda', 'Ugoda'

class Documents(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, db_column='caseid')
    title = models.CharField(max_length=300, null=False)
    document_type = models.CharField(max_length=30, choices=DocumentType.choices, null=False)
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'DOCUMENTS'

class DocumentVersion(models.Model):
    document = models.ForeignKey(Documents, on_delete=models.CASCADE, db_column='documentid')
    created_by_lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE, db_column='createdbylawyerid')
    version_number = models.IntegerField(null=False)
    file_path = models.CharField(max_length=500, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'DOCUMENTVERSIONS'

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
    hearing_type = models.CharField(max_length=20, choices=HearingType.choices, null=False)
    scheduled_at = models.DateTimeField(null=False)
    status = models.CharField(max_length=20, choices=HearingStatus.choices, default=HearingStatus.PLANOWANY)
    notes = models.TextField(blank=True)
    reminder_minutes_before = models.IntegerField(default=1440)
    reminder_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'COURTHEARINGS'

## Model Invoice
class InvoiceStatus(models.TextChoices):
    WYSTAWIONA = 'wystawiona', 'Wystawiona'
    OPŁACONA = 'opłacona', 'Opłacona'
    PRZETERMINOWANA = 'przeterminowana', 'Przeterminowana'

class Invoice(models.Model):
    case = models.ForeignKey('Case', on_delete=models.SET_NULL, blank=True, null=True, db_column='caseid')
    invoice_number = models.CharField(max_length=50, unique=True, null=False)
    currency = models.CharField(max_length=3, default='PLN')
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.23'))
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.WYSTAWIONA)
    issue_date = models.DateField(null=False)
    due_date = models.DateField(null=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.gross_amount = self.net_amount * (1 + self.vat_rate)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'INVOICES'

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

    class Meta:
        db_table = 'TASKS'
