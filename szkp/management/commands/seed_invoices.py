from decimal import Decimal
from datetime import timedelta
from random import choice, randint

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from szkp.models import Case, Invoice, InvoiceStatus


class Command(BaseCommand):
    help = "Tworzy testowe rekordy Invoice"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Liczba faktur do utworzenia (domyślnie: 100).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuń istniejące rekordy Invoice przed seedowaniem.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]

        if clear:
            deleted_count, _ = Invoice.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Usunięto {deleted_count} faktur."))

        cases = list(Case.objects.all())
        if not cases:
            self.stdout.write(self.style.WARNING("Brak spraw - case będzie NULL. Kontynuuję..."))

        currencies = ['PLN', 'EUR', 'USD']
        vat_rates = [Decimal('0.23'), Decimal('0.08'), Decimal('0.05'), Decimal('0.00')]

        created = 0
        now = timezone.now()

        for i in range(count):
            case = choice(cases) if cases else None

            invoice_number = f"INV/{now.year}/{i+1:04d}/{randint(1000, 9999)}"
            
            issue_date = now - timedelta(days=randint(1, 365))
            due_date = issue_date + timedelta(days=choice([14, 30, 60]))
            
            net_amount = Decimal(str(randint(50, 5000))) / 100
            
            if due_date < now - timedelta(days=7):
                status = InvoiceStatus.PRZETERMINOWANA
                paid_at = None
            elif issue_date < now - timedelta(days=30):
                status = choice([InvoiceStatus.OPŁACONA, InvoiceStatus.PRZETERMINOWANA])
                if status == InvoiceStatus.OPŁACONA:
                    paid_at = issue_date + timedelta(days=randint(1, 45))
                else:
                    paid_at = None
            else:
                status = InvoiceStatus.WYSTAWIONA
                paid_at = None

            invoice = Invoice(
                case=case,
                invoice_number=invoice_number,
                currency=choice(currencies),
                vat_rate=choice(vat_rates),
                net_amount=net_amount,
                status=status,
                issue_date=issue_date,
                due_date=due_date,
                paid_at=paid_at,
            )
            
            invoice.full_clean()
            invoice.save()
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Utworzono {created} faktur.")
        )