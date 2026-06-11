import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Python_Web.settings')
django.setup()

from django.core.management.base import BaseCommand
from faker import Faker
from decimal import Decimal
from szkp.models import Lawyer

fake = Faker('pl_PL')

class Command(BaseCommand):
    help = 'Seed 50 rekordów Lawyer'

    def handle(self, *args, **options):
        for i in range(5):
            lawyer = Lawyer(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                bar_number=f'WP/{fake.random_int(min=1000, max=9999)}/{fake.random_int(min=1000, max=9999)}',
                specialization=fake.random_element(elements=[
                    'prawo cywilne', 'prawo karne', 'prawo gospodarcze', 
                    'prawo administracyjne', 'prawo rodzinne', 'prawo pracy'
                ]),
                email=fake.email(),
                phone=fake.numerify(text='### ### ###'),
                activeflag=fake.boolean(chance_of_getting_true=90),
                defaultrate=Decimal(str(fake.random_int(min=150, max=500)))
            )
            lawyer.full_clean()
            lawyer.save()
            self.stdout.write(f"Utworzono Lawyer {i+1}: {lawyer.first_name} {lawyer.last_name}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Seed Lawyers zakończony! {Lawyer.objects.count()} rekordów.')
        )
