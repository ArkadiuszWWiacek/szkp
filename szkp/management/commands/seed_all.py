from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from szkp.models import (
    Case,
    CaseLawyer,
    Client,
    CourtHearing,
    Document,
    DocumentVersion,
    Invoice,
    Lawyer,
    Task,
)


class Command(BaseCommand):
    help = "Uruchamia wszystkie seedy w prawidłowej kolejności zależności FK"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Wyczyść wszystkie dane przed seedowaniem (idempotentne).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_all()

        steps = [
            ("seed_clients", {}),
            ("seed_lawyers", {}),
            ("seed_users", {}),
            ("seed_cases", {"count": 15}),
            ("seed_case_lawyers", {}),
            ("seed_court_hearings", {"count": 30}),
            ("seed_documents", {"count": 20}),
            ("seed_invoices", {"count": 20}),
            ("seed_tasks", {"count": 30, "with_subtasks": True}),
        ]

        for name, kwargs in steps:
            self.stdout.write(f"\n{'─' * 40}\n→ {name}")
            call_command(name, stdout=self.stdout, **kwargs)

        self.stdout.write(self.style.SUCCESS("\nWszystkie seedy wykonane pomyślnie."))

    @transaction.atomic
    def _clear_all(self):
        counts = {}

        for model in (Task, DocumentVersion, Document, CourtHearing, Invoice, CaseLawyer, Case, Client, Lawyer):
            n, _ = model.objects.all().delete()
            counts[model.__name__] = n

        n, _ = User.objects.filter(is_superuser=False).delete()
        counts["User"] = n

        for name, n in counts.items():
            if n:
                self.stdout.write(self.style.WARNING(f"  Usunięto {n} × {name}"))

        self.stdout.write(self.style.WARNING("Baza wyczyszczona.\n"))
