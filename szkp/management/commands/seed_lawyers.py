from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from szkp.models import Lawyer

LAWYERS = [
    {
        "first_name": "Anna",
        "last_name": "Kowalska",
        "bar_number": "WP/0001/2021",
        "specialization": "prawo cywilne",
        "email": "a.kowalska@kancelaria.pl",
        "phone": "600 100 001",
        "activeflag": True,
        "defaultrate": Decimal("350.00"),
    },
    {
        "first_name": "Piotr",
        "last_name": "Nowak",
        "bar_number": "WP/0002/2019",
        "specialization": "prawo karne",
        "email": "p.nowak@kancelaria.pl",
        "phone": "600 100 002",
        "activeflag": True,
        "defaultrate": Decimal("400.00"),
    },
    {
        "first_name": "Marta",
        "last_name": "Wiśniewska",
        "bar_number": "WP/0003/2020",
        "specialization": "prawo gospodarcze",
        "email": "m.wisniewska@kancelaria.pl",
        "phone": "600 100 003",
        "activeflag": True,
        "defaultrate": Decimal("420.00"),
    },
    {
        "first_name": "Tomasz",
        "last_name": "Wójcik",
        "bar_number": "WP/0004/2018",
        "specialization": "prawo rodzinne",
        "email": "t.wojcik@kancelaria.pl",
        "phone": "600 100 004",
        "activeflag": True,
        "defaultrate": Decimal("300.00"),
    },
    {
        "first_name": "Katarzyna",
        "last_name": "Kamińska",
        "bar_number": "WP/0005/2022",
        "specialization": "prawo pracy",
        "email": "k.kaminska@kancelaria.pl",
        "phone": "600 100 005",
        "activeflag": True,
        "defaultrate": Decimal("380.00"),
    },
]


class Command(BaseCommand):
    help = "Tworzy stałą listę 5 prawników (deterministyczne dane demo)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuń istniejące rekordy Lawyer przed seedowaniem.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Lawyer.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Usunięto {deleted} rekordów Lawyer."))

        for data in LAWYERS:
            bar_number = data.pop("bar_number")
            lawyer, created = Lawyer.objects.update_or_create(
                bar_number=bar_number,
                defaults=data,
            )
            data["bar_number"] = bar_number  # przywróć dla ewentualnych kolejnych wywołań
            status = "Utworzono" if created else "Zaktualizowano"
            self.stdout.write(f"  {status}: {lawyer.first_name} {lawyer.last_name} ({bar_number})")

        self.stdout.write(
            self.style.SUCCESS(f"Seed Lawyers zakończony! {Lawyer.objects.count()} rekordów.")
        )
