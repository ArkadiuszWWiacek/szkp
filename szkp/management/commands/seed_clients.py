import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Python_Web.settings")
django.setup()

from django.core.management.base import BaseCommand
from faker import Faker
from szkp.models import Client

fake = Faker("pl_PL")


class Command(BaseCommand):
    help = "Seed 50 rekordów Client z walidacjami"

    def handle(self, *args, **options):
        for i in range(50):
            typ = fake.random_element(elements=("osobafizyczna", "firma"))

            if typ == "osobafizyczna":
                pesel = fake.random_int(min=0, max=99999999999)
                pesel_str = f"{pesel:011d}"
                nip = None
                company = None
                first = fake.first_name_female() if i % 2 else fake.first_name_male()
            else:
                nip = fake.random_int(min=0, max=9999999999999)
                nip_str = f"{nip:013d}"
                pesel = None
                company = fake.company()
                first = None

            client = Client(
                first_name=first,
                last_name=fake.last_name() if typ == "osobafizyczna" else None,
                company_name=company,
                type=typ,
                pesel=pesel_str if typ == "osobafizyczna" else None,
                nip=nip_str if typ == "firma" else None,
                phone=fake.numerify(text="### ### ###"),
                email=fake.email(),
                address_street=fake.street_name() + " " + str(fake.building_number()),
                address_city=fake.city(),
                address_zip=fake.postcode(),
                country="Polska",
            )

            client.full_clean()
            client.save()
            self.stdout.write(f"Utworzono Client {i+1}: {client}")

        self.stdout.write(self.style.SUCCESS("Seed Clients zakończony! 50 rekordów."))
