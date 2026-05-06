from datetime import timedelta
from random import choice, randint

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker

from szkp.models import Case, Lawyer, CourtHearing, HearingStatus, HearingType


class Command(BaseCommand):
    help = "Tworzy testowe rekordy CourtHearing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=200,
            help="Liczba rekordów CourtHearing do utworzenia (domyślnie: 100).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuń istniejące rekordy CourtHearing przed seedowaniem.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker('pl_PL')
        count = options["count"]
        clear = options["clear"]

        if clear:
            deleted_count, _ = CourtHearing.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Usunięto {deleted_count} rekordów CourtHearing."))

        cases = list(Case.objects.all())
        lawyers = list(Lawyer.objects.filter(activeflag=True))
        
        if not cases:
            raise CommandError("Brak rekordów Case. Najpierw uruchom seed dla spraw.")
        if not lawyers:
            self.stdout.write(self.style.WARNING("Brak aktywnych Lawyer - responsible_lawyer będzie NULL."))

        courts = [
            "Sąd Okręgowy w Warszawie", "Sąd Rejonowy dla Warszawy-Mokotowa", 
            "Sąd Okręgowy w Krakowie", "Sąd Rejonowy w Gdańsku",
            "Sąd Okręgowy we Wrocławiu", "Sąd Apelacyjny w Warszawie"
        ]
        
        hearing_types = [choice[0] for choice in HearingType.choices]

        created = 0
        now = timezone.now()

        for i in range(count):
            case = choice(cases)
            responsible_lawyer = choice(lawyers) if lawyers else None
            
            case_opened = case.opened_at or now - timedelta(days=30)
            scheduled_at = case_opened + timedelta(
                days=randint(1, 90), 
                hours=randint(0, 23), 
                minutes=randint(0, 59)
            )
            
            if scheduled_at < now - timedelta(hours=2):
                status = choice([HearingStatus.ODBYTY, HearingStatus.ODROCZONY])
            elif scheduled_at < now + timedelta(days=1):
                status = HearingStatus.PLANOWANY
            else:
                status = choice([HearingStatus.PLANOWANY, HearingStatus.ODWOŁANY])

            hearing = CourtHearing(
                case=case,
                responsible_lawyer=responsible_lawyer,
                court_name=choice(courts),
                courtroom=f"Sala {randint(1, 10)}",
                judge_name=fake.first_name() + ' ' + fake.last_name() if randint(1, 3) == 1 else '',
                hearing_type=choice(hearing_types),
                scheduled_at=scheduled_at,
                status=status,
                notes=fake.paragraph(nb_sentences=2) if randint(1, 4) == 1 else '',
                reminder_minutes_before=choice([1440, 720, 1440*7]),  # 1d, 12h, 7d
            )
            
            hearing.full_clean()
            hearing.save()
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Utworzono {created} rekordów CourtHearing.")
        )