from datetime import timedelta
from random import choice, randint, random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker

from szkp.models import (
    Case,
    Lawyer,
    Task,
    TaskPriority,
    TaskStatus,
)


class Command(BaseCommand):
    help = "Tworzy testowe rekordy Task"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Liczba zadań głównych do utworzenia (domyślnie: 100).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuń istniejące rekordy Task przed seedowaniem.",
        )
        parser.add_argument(
            "--with-subtasks",
            action="store_true",
            help="Utwórz też podzadania dla części rekordów.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker("pl_PL")
        count = options["count"]
        clear = options["clear"]
        with_subtasks = options["with_subtasks"]

        if clear:
            deleted_count, _ = Task.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Usunięto {deleted_count} rekordów Task."))

        lawyers = list(Lawyer.objects.all())
        cases = list(Case.objects.all())

        if not lawyers:
            raise CommandError("Brak rekordów Lawyer. Najpierw uruchom seed dla prawników.")

        priorities = [item[0] for item in TaskPriority.choices]
        statuses = [item[0] for item in TaskStatus.choices]

        created = 0
        parent_tasks = []
        now = timezone.now()

        for i in range(count):
            assigned_lawyer = choice(lawyers)
            created_by = choice(lawyers)
            case = choice(cases) if cases and random() > 0.15 else None

            due_date = None
            if random() > 0.2:
                due_date = now + timedelta(days=randint(-30, 60), hours=randint(0, 23))

            status = choice(statuses)
            completed_at = None

            if status in [TaskStatus.ZAKOŃCZONE, TaskStatus.ARCHIWALNE]:
                completed_at = now - timedelta(days=randint(1, 20))
                if due_date and completed_at < due_date and random() > 0.5:
                    completed_at = due_date + timedelta(hours=randint(1, 72))

            task = Task(
                case=case,
                assigned_lawyer=assigned_lawyer,
                created_by=created_by,
                parent_task=None,
                title=fake.sentence(nb_words=5)[:300],
                description=fake.paragraph(nb_sentences=3) if random() > 0.25 else "",
                priority=choice(priorities),
                status=status,
                due_date=due_date,
                completed_at=completed_at,
            )
            task.full_clean()
            task.save()

            parent_tasks.append(task)
            created += 1

        if with_subtasks and parent_tasks:
            subtasks_created = 0

            for parent in parent_tasks:
                if random() > 0.35:
                    continue

                subtasks_count = randint(1, 3)

                for _ in range(subtasks_count):
                    assigned_lawyer = choice(lawyers)
                    created_by = choice(lawyers)

                    due_date = None
                    if random() > 0.15:
                        base_date = parent.due_date if parent.due_date else now
                        due_date = base_date + timedelta(days=randint(-5, 10))

                    status = choice(statuses)
                    completed_at = None

                    if status in [TaskStatus.ZAKOŃCZONE, TaskStatus.ARCHIWALNE]:
                        completed_at = now - timedelta(days=randint(1, 15))

                    subtask = Task(
                        case=parent.case,
                        assigned_lawyer=assigned_lawyer,
                        created_by=created_by,
                        parent_task=parent,
                        title=f"Podzadanie: {fake.sentence(nb_words=4)[:260]}",
                        description=fake.paragraph(nb_sentences=2) if random() > 0.4 else "",
                        priority=choice(priorities),
                        status=status,
                        due_date=due_date,
                        completed_at=completed_at,
                    )
                    subtask.full_clean()
                    subtask.save()
                    subtasks_created += 1

            created += subtasks_created
            self.stdout.write(
                self.style.SUCCESS(
                    f"Utworzono {count} zadań głównych i {subtasks_created} podzadań. Łącznie: {created}."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Utworzono {created} rekordów Task.")
            )