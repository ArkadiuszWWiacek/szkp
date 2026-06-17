from datetime import date
from decimal import Decimal

from django.test import tag
from django.urls import reverse

from szkp.models import Case, CaseType, Invoice, InvoiceStatus
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class InvoiceListSortTest(StaffLawyerTestCase):
    """invoice_list: sortowanie kolumnowe."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa_a = Case.objects.create(
            client=cls.klient, case_number='TST-SORT-INV-001',
            title='Sprawa A do testów faktur', case_type=CaseType.CYWILNA,
        )
        cls.sprawa_b = Case.objects.create(
            client=cls.klient, case_number='TST-SORT-INV-002',
            title='Sprawa B do testów faktur', case_type=CaseType.CYWILNA,
        )
        cls.inv1 = Invoice.objects.create(
            case=cls.sprawa_a,
            invoice_number='FV/2024/001',
            issue_date=date(2024, 1, 10),
            due_date=date(2024, 2, 10),
            net_amount=Decimal('500.00'),
            status=InvoiceStatus.WYSTAWIONA,
        )
        cls.inv2 = Invoice.objects.create(
            case=cls.sprawa_b,
            invoice_number='FV/2024/002',
            issue_date=date(2024, 3, 15),
            due_date=date(2024, 4, 15),
            net_amount=Decimal('1000.00'),
            status=InvoiceStatus.OPŁACONA,
        )
        cls.inv3 = Invoice.objects.create(
            case=cls.sprawa_a,
            invoice_number='FV/2024/003',
            issue_date=date(2024, 2, 20),
            due_date=date(2024, 3, 20),
            net_amount=Decimal('200.00'),
            status=InvoiceStatus.PRZETERMINOWANA,
        )

    def _url(self, **params):
        url = reverse('szkp:invoice_list')
        if params:
            url += '?' + '&'.join(f'{k}={v}' for k, v in params.items())
        return url

    def _pks(self, r):
        return [inv.pk for inv in r.context['invoices']]

    def test_domyslne_sortowanie_po_dacie_wystawienia_malejaco(self):
        """Domyślne sortowanie listy faktur odbywa się malejąco po dacie wystawienia."""
        r = self.client.get(self._url())
        pks = self._pks(r)
        # inv2 (2024-03-15) > inv3 (2024-02-20) > inv1 (2024-01-10)
        self.assertLess(pks.index(self.inv2.pk), pks.index(self.inv3.pk))
        self.assertLess(pks.index(self.inv3.pk), pks.index(self.inv1.pk))

    def test_sortowanie_po_numerze_faktury_rosnaco(self):
        """Sortowanie po numerze faktury rosnąco (dir=asc) ustawia faktury w kolejności alfabetycznej."""
        r = self.client.get(self._url(sort='invoice_number', dir='asc'))
        pks = self._pks(r)
        # FV/2024/001 < FV/2024/002 < FV/2024/003
        self.assertLess(pks.index(self.inv1.pk), pks.index(self.inv2.pk))
        self.assertLess(pks.index(self.inv2.pk), pks.index(self.inv3.pk))

    def test_sortowanie_po_terminie_platnosci_rosnaco(self):
        """Sortowanie po terminie płatności rosnąco (dir=asc) ustawia faktury od najwcześniejszego terminu."""
        r = self.client.get(self._url(sort='due_date', dir='asc'))
        pks = self._pks(r)
        # 2024-02-10 < 2024-03-20 < 2024-04-15
        self.assertLess(pks.index(self.inv1.pk), pks.index(self.inv3.pk))
        self.assertLess(pks.index(self.inv3.pk), pks.index(self.inv2.pk))

    def test_sortowanie_po_statusie_rosnaco(self):
        """Sortowanie po statusie faktury rosnąco (dir=asc) ustawia faktury w kolejności alfabetycznej statusu."""
        r = self.client.get(self._url(sort='status', dir='asc'))
        pks = self._pks(r)
        # 'opłacona' < 'przeterminowana' < 'wystawiona'
        self.assertLess(pks.index(self.inv2.pk), pks.index(self.inv3.pk))
        self.assertLess(pks.index(self.inv3.pk), pks.index(self.inv1.pk))

    def test_sortowanie_po_kwocie_brutto_malejaco(self):
        """Sortowanie po kwocie brutto malejąco (dir=desc) ustawia faktury od najwyższej kwoty."""
        r = self.client.get(self._url(sort='gross_amount', dir='desc'))
        pks = self._pks(r)
        # inv2: 1230 > inv1: 615 > inv3: 246
        self.assertLess(pks.index(self.inv2.pk), pks.index(self.inv1.pk))
        self.assertLess(pks.index(self.inv1.pk), pks.index(self.inv3.pk))

    def test_sortowanie_po_sprawie_rosnaco(self):
        """Sortowanie po numerze sprawy rosnąco (dir=asc) ustawia faktury w kolejności sygnatur."""
        r = self.client.get(self._url(sort='case', dir='asc'))
        pks = self._pks(r)
        # TST-SORT-INV-001 < TST-SORT-INV-002
        self.assertLess(pks.index(self.inv1.pk), pks.index(self.inv2.pk))

    def test_kontekst_zawiera_sort_i_direction(self):
        """Kontekst szablonu zawiera aktualne wartości parametrów sort i direction."""
        r = self.client.get(self._url(sort='status', dir='asc'))
        self.assertEqual(r.context['sort'], 'status')
        self.assertEqual(r.context['direction'], 'asc')

    def test_nieprawidlowe_pole_sort_nie_powoduje_bledu(self):
        """Nieprawidłowa wartość parametru sort nie powoduje błędu — widok zwraca kod 200."""
        r = self.client.get(self._url(sort='HACK', dir='asc'))
        self.assertEqual(r.status_code, 200)

    def test_sort_zachowany_przy_filtrze_statusu(self):
        """Parametry sortowania są zachowane w kontekście podczas jednoczesnego filtrowania po statusie."""
        r = self.client.get(self._url(status='wystawiona', sort='due_date', dir='asc'))
        self.assertEqual(r.context['sort'], 'due_date')
        self.assertEqual(r.context['direction'], 'asc')

    def test_wyszukiwanie_po_numerze_faktury(self):
        """Wyszukiwanie po dokładnym numerze faktury zwraca tylko pasującą fakturę."""
        r = self.client.get(self._url(q='FV/2024/001'))
        pks = self._pks(r)
        self.assertIn(self.inv1.pk, pks)
        self.assertNotIn(self.inv2.pk, pks)
        self.assertNotIn(self.inv3.pk, pks)

    def test_wyszukiwanie_po_fragmencie_numeru_faktury(self):
        """Wyszukiwanie po fragmencie numeru faktury zwraca wszystkie pasujące faktury."""
        r = self.client.get(self._url(q='FV/2024'))
        pks = self._pks(r)
        self.assertIn(self.inv1.pk, pks)
        self.assertIn(self.inv2.pk, pks)
        self.assertIn(self.inv3.pk, pks)

    def test_wyszukiwanie_po_numerze_sprawy(self):
        """Wyszukiwanie po numerze sprawy zwraca faktury powiązane z tą sprawą."""
        r = self.client.get(self._url(q='TST-SORT-INV-002'))
        pks = self._pks(r)
        self.assertIn(self.inv2.pk, pks)
        self.assertNotIn(self.inv1.pk, pks)

    def test_wyszukiwanie_zachowuje_filtr_statusu(self):
        """Wyszukiwanie przy aktywnym filtrze statusu zwraca tylko faktury spełniające oba kryteria."""
        r = self.client.get(self._url(q='FV/2024', status='wystawiona'))
        pks = self._pks(r)
        self.assertIn(self.inv1.pk, pks)
        self.assertNotIn(self.inv2.pk, pks)
        self.assertNotIn(self.inv3.pk, pks)
