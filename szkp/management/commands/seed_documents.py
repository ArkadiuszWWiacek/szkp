import json
import shutil
from pathlib import Path
from random import choice, randint, random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from szkp.models import (
    Case,
    Lawyer,
    Document,
    DocumentVersion,
    DocumentType,
)


class Command(BaseCommand):
    help = "Tworzy testowe rekordy Document i DocumentVersion"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Liczba dokumentów do utworzenia (domyślnie: 100).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuń istniejące rekordy DocumentVersion i Document przed seedowaniem.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]

        lorem_path = Path(settings.BASE_DIR) / "docs" / "lorem_docs_merged.json"
        with lorem_path.open(encoding="utf-8") as f:
            lorem_docs = list(json.load(f).values())

        if clear:
            deleted_versions, _ = DocumentVersion.objects.all().delete()
            deleted_documents, _ = Document.objects.all().delete()
            docs_dir = Path(settings.MEDIA_ROOT) / "documents"
            if docs_dir.exists():
                shutil.rmtree(docs_dir)
            self.stdout.write(
                self.style.WARNING(
                    f"Usunięto {deleted_versions} rekordów DocumentVersion i {deleted_documents} rekordów Document."
                )
            )

        cases = list(Case.objects.all())
        lawyers = list(Lawyer.objects.all())

        if not cases:
            raise CommandError("Brak rekordów Case. Najpierw uruchom seed dla spraw.")
        if not lawyers:
            raise CommandError("Brak rekordów Lawyer. Najpierw uruchom seed dla prawników.")

        document_types = [item[0] for item in DocumentType.choices]

        document_titles = {
            DocumentType.POZEW: [
                "Pozew o zapłatę",
                "Pozew o rozwód",
                "Pozew o odszkodowanie",
                "Pozew o ustalenie",
            ],
            DocumentType.ODPOWIEDZ: [
                "Odpowiedź na pozew",
                "Odpowiedź na wezwanie",
                "Odpowiedź procesowa",
            ],
            DocumentType.PISMO_SADOWE: [
                "Pismo procesowe",
                "Wniosek dowodowy",
                "Wniosek o odroczenie rozprawy",
                "Pismo przygotowawcze",
            ],
            DocumentType.NOTATKA: [
                "Notatka ze spotkania z klientem",
                "Notatka wewnętrzna",
                "Notatka z analizy akt",
            ],
            DocumentType.UMOWA: [
                "Projekt umowy",
                "Umowa współpracy",
                "Umowa zlecenia",
            ],
            DocumentType.DOWOD: [
                "Załącznik dowodowy",
                "Dowód z dokumentu",
                "Materiał dowodowy",
            ],
            DocumentType.WYROK: [
                "Odpis wyroku",
                "Wyrok sądu I instancji",
                "Wyrok z uzasadnieniem",
            ],
            DocumentType.UGODA: [
                "Projekt ugody",
                "Ugoda pozasądowa",
                "Ugoda mediacyjna",
            ],
        }

        created_documents = 0
        created_versions = 0

        for i in range(count):
            case = choice(cases)
            document_type = choice(document_types)
            title = choice(document_titles[document_type])

            document = Document(
                case=case,
                title=f"{title} #{i + 1}",
                document_type=document_type,
                is_internal=document_type == DocumentType.NOTATKA or random() < 0.2,
            )
            document.full_clean()
            document.save()
            created_documents += 1

            versions_count = randint(1, 3)
            used_version_numbers = set()

            for version_no in range(1, versions_count + 1):
                created_by_lawyer = choice(lawyers)

                safe_type = document_type.replace("ą", "a").replace("ł", "l")
                file_path = (
                    f"documents/case_{document.case_id}/"
                    f"{safe_type}_{document.id}_v{version_no}.md"
                )

                abs_path = Path(settings.MEDIA_ROOT) / file_path
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_text(choice(lorem_docs), encoding="utf-8")

                version = DocumentVersion(
                    document=document,
                    created_by_lawyer=created_by_lawyer,
                    version_number=version_no,
                    file_path=file_path,
                )
                version.full_clean()
                version.save()
                created_versions += 1
                used_version_numbers.add(version_no)

        self.stdout.write(
            self.style.SUCCESS(
                f"Utworzono {created_documents} rekordów Document i {created_versions} rekordów DocumentVersion."
            )
        )