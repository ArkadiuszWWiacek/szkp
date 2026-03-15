from django.db import models
from .Case import Case
from .Lawyer import Lawyer

## Model Document
class DocumentType(models.TextChoices):
    POZEW = 'pozew', 'Pozew'
    ODPOWIEDZ = 'odpowiedz', 'Odpowiedź'
    PISMO_SADOWE = 'pismo_sadowe', 'Pismo sądowe'
    NOTATKA = 'notatka', 'Notatka'
    UMOWA = 'umowa', 'Umowa'
    DOWOD = 'dowod', 'Dowód'
    WYROK = 'wyrok', 'Wyrok'
    UGODA = 'ugoda', 'Ugoda'

class Document(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, db_column='caseid')
    title = models.CharField(max_length=300, null=False)
    document_type = models.CharField(max_length=30, choices=DocumentType.choices, null=False)
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'DOCUMENTS'

class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, db_column='documentid')
    created_by_lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE, db_column='createdbylawyerid')
    version_number = models.IntegerField(null=False)
    file_path = models.CharField(max_length=500, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'DOCUMENTVERSIONS'