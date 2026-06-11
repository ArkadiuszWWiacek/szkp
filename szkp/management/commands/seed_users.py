import re

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from szkp.models import Lawyer

_PL_CHARS = str.maketrans(
    "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
    "acelnoszzACELNOSZZ",
)


def _slugify_name(name: str) -> str:
    transliterated = name.lower().translate(_PL_CHARS)
    return re.sub(r"[^a-z0-9]", "", transliterated)


def _unique_username(first_name: str, last_name: str) -> str:
    base = f"{_slugify_name(first_name)}.{_slugify_name(last_name)}"
    username = base
    n = 2
    while User.objects.filter(username=username).exists():
        username = f"{base}{n}"
        n += 1
    return username


class Command(BaseCommand):
    help = "Tworzy konta Django User dla istniejących rekordów Lawyer"

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="szkp1234",
            help="Domyślne hasło dla tworzonych kont (domyślnie: szkp1234).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuń wszystkich nie-superuserów przed seedowaniem.",
        )

    def handle(self, *args, **options):
        password = options["password"]
        clear = options["clear"]

        if clear:
            deleted, _ = User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING(f"Usunięto {deleted} kont użytkowników."))

        lawyers = Lawyer.objects.all()
        if not lawyers.exists():
            self.stdout.write(self.style.ERROR("Brak rekordów Lawyer. Najpierw uruchom seed_lawyers."))
            return

        created = 0
        skipped = 0

        for lawyer in lawyers:
            existing = User.objects.filter(
                first_name=lawyer.first_name, last_name=lawyer.last_name
            ).first()

            if existing:
                self.stdout.write(f"  Pominięto (istnieje): {lawyer.first_name} {lawyer.last_name}")
                skipped += 1
                user = existing
            else:
                username = _unique_username(lawyer.first_name, lawyer.last_name)
                user = User.objects.create_user(
                    username=username,
                    email=lawyer.email or "",
                    password=password,
                    first_name=lawyer.first_name,
                    last_name=lawyer.last_name,
                )
                self.stdout.write(f"  Utworzono: {username}  (hasło: {password})")
                created += 1

            if lawyer.user_id != user.pk:
                lawyer.user = user
                lawyer.save(update_fields=['user'])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed Users zakończony! Utworzono: {created}, pominięto: {skipped}."
            )
        )
