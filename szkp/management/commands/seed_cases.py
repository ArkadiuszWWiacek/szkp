import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Python_Web.settings')
django.setup()


from datetime import timedelta
from random import choice, randint, random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker
from szkp.models import Client, Case, CaseType, CaseStatus, CasePriority

fake = Faker('pl_PL')

class Command(BaseCommand):
    help = "Tworzy testowe rekordy Case"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Liczba rekordów Case do utworzenia (domyślnie: 100).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuń istniejące rekordy Case przed seedowaniem.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker("pl_PL")
        count = options["count"]
        clear = options["clear"]

        if clear:
            deleted_count, _ = Case.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Usunięto {deleted_count} rekordów Case."))

        clients = list(Client.objects.all())
        if not clients:
            raise CommandError("Brak rekordów Client. Najpierw uruchom seed dla klientów.")

        case_types = [choice[0] for choice in CaseType.choices]
        statuses = [choice[0] for choice in CaseStatus.choices]
        priorities = [choice[0] for choice in CasePriority.choices]

        created = 0
        now = timezone.now()

        for i in range(count):
            client = choice(clients)
            opened_at = now - timedelta(days=randint(1, 900))

            status = choice(statuses)
            if status in {CaseStatus.ZAKOŃCZONA, CaseStatus.ARCHIWALNA}:
                closed_at = opened_at + timedelta(days=randint(7, 240))
                if closed_at > now:
                    closed_at = now - timedelta(days=randint(0, 10))
            else:
                closed_at = None

            if closed_at and closed_at < opened_at:
                closed_at = opened_at + timedelta(days=1)

            case_number = f"CASE/{now.year}/{i + 1:04d}/{fake.unique.bothify(text='??##')}"
            court_case_number = (
                f"{randint(1, 20)} C {randint(100, 9999)}/{randint(20, 26)}"
                if random() > 0.25
                else None
            )

            case = Case(
                client=client,
                case_number=case_number,
                court_case_number=court_case_number,
                title=fake.sentence(nb_words=5)[:300],
                description=fake.paragraph(nb_sentences=4),
                case_type=choice(case_types),
                status=status,
                case_priority=choice(priorities),
                opened_at=opened_at,
                closed_at=closed_at,
            )

            case.full_clean()
            case.save()
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Utworzono {created} rekordów Case.")
        )
