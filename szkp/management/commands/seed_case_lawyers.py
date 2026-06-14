from datetime import timedelta
from random import sample, randint, choice

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from szkp.models import Case, Lawyer, CaseLawyer, CaseLawyerRole


class Command(BaseCommand):
    help = "Tworzy testowe rekordy CaseLawyer"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuń istniejące rekordy CaseLawyer przed seedowaniem.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clear = options["clear"]

        if clear:
            deleted_count, _ = CaseLawyer.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Usunięto {deleted_count} rekordów CaseLawyer."))

        cases = list(Case.objects.all())
        lawyers = list(Lawyer.objects.filter(activeflag=True))

        if not cases:
            raise CommandError("Brak rekordów Case. Najpierw uruchom seed dla spraw.")
        if not lawyers:
            raise CommandError("Brak rekordów Lawyer. Najpierw uruchom seed dla adwokatów.")

        created = 0
        now = timezone.now()

        for case in cases:
            available_lawyers = [l for l in lawyers if not CaseLawyer.objects.filter(case=case, lawyer=l).exists()]
            if not available_lawyers:
                continue

            assign_count = min(randint(1, 3), len(available_lawyers))
            assigned_lawyers = sample(available_lawyers, assign_count)

            has_prowadzacy = CaseLawyer.objects.filter(
                case=case, role=CaseLawyerRole.PROWADZACY
            ).exists()
            responsible_lawyer = None if has_prowadzacy else choice(assigned_lawyers)

            for lawyer in assigned_lawyers:
                if responsible_lawyer is not None and lawyer == responsible_lawyer:
                    role = CaseLawyerRole.PROWADZACY
                else:
                    role = choice([CaseLawyerRole.ASYSTENT, CaseLawyerRole.DORADCA])

                unassigned_at = None
                if role != CaseLawyerRole.PROWADZACY and randint(1, 10) == 1:
                    unassigned_at = now - timedelta(days=randint(1, 30))

                obj = CaseLawyer(
                    case=case,
                    lawyer=lawyer,
                    role=role,
                    unassigned_at=unassigned_at,
                    responsible_flag=(responsible_lawyer is not None and lawyer == responsible_lawyer),
                )
                obj.full_clean()
                obj.save()
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Utworzono {created} rekordów CaseLawyer.")
        )