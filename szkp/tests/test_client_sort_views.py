from datetime import timedelta

from django.test import tag
from django.urls import reverse
from django.utils import timezone

from szkp.models import Client, ClientType
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class ClientListSortTest(StaffLawyerTestCase):
    """client_list: sortowanie kolumnowe."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.klient_b = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA, first_name='Barbara', last_name='Bednarczyk',
            pesel='90020223456',
        )
        cls.klient_c = Client.objects.create(
            type=ClientType.FIRMA, company_name='Alfa Sp. z o.o.', nip='1234567890',
        )
        now = timezone.now()
        Client.objects.filter(pk=cls.klient.pk).update(created_at=now - timedelta(days=2))
        Client.objects.filter(pk=cls.klient_b.pk).update(created_at=now - timedelta(days=1))
        Client.objects.filter(pk=cls.klient_c.pk).update(created_at=now)

    def _url(self, **params):
        url = reverse('szkp:client_list')
        if params:
            url += '?' + '&'.join(f'{k}={v}' for k, v in params.items())
        return url

    def _pks(self, r):
        return [c.pk for c in r.context['page_obj']]

    def test_domyslne_sortowanie_po_nazwisku(self):
        """Domyślne sortowanie listy klientów odbywa się rosnąco po nazwisku."""
        r = self.client.get(self._url())
        pks = self._pks(r)
        # Bednarczyk < Klientka alfabetycznie
        self.assertLess(pks.index(self.klient_b.pk), pks.index(self.klient.pk))

    def test_sortowanie_po_nazwisku_malejaco(self):
        """Sortowanie po nazwisku malejąco (dir=desc) ustawia klientów w odwrotnej kolejności alfabetycznej."""
        r = self.client.get(self._url(sort='last_name', dir='desc'))
        pks = self._pks(r)
        # Klientka > Bednarczyk w kolejności malejącej
        self.assertLess(pks.index(self.klient.pk), pks.index(self.klient_b.pk))

    def test_sortowanie_po_typie_rosnaco(self):
        """Sortowanie po typie klienta rosnąco (dir=asc) ustawia firmy przed osobami fizycznymi."""
        r = self.client.get(self._url(sort='type', dir='asc'))
        pks = self._pks(r)
        # 'firma' < 'osobafizyczna' alfabetycznie
        self.assertLess(pks.index(self.klient_c.pk), pks.index(self.klient.pk))

    def test_sortowanie_po_dacie_dodania_malejaco(self):
        """Sortowanie po dacie dodania malejąco (dir=desc) ustawia najnowszych klientów na początku."""
        r = self.client.get(self._url(sort='created_at', dir='desc'))
        pks = self._pks(r)
        # klient_c (najnowszy) → klient_b → klient (najstarszy)
        self.assertLess(pks.index(self.klient_c.pk), pks.index(self.klient_b.pk))
        self.assertLess(pks.index(self.klient_b.pk), pks.index(self.klient.pk))

    def test_kontekst_zawiera_sort_i_direction(self):
        """Kontekst szablonu zawiera aktualne wartości parametrów sort i direction."""
        r = self.client.get(self._url(sort='type', dir='asc'))
        self.assertEqual(r.context['sort'], 'type')
        self.assertEqual(r.context['direction'], 'asc')

    def test_nieprawidlowe_pole_sort_nie_powoduje_bledu(self):
        """Nieprawidłowa wartość parametru sort nie powoduje błędu — widok zwraca kod 200."""
        r = self.client.get(self._url(sort='zly_klucz', dir='asc'))
        self.assertEqual(r.status_code, 200)

    def test_sort_zachowany_przy_wyszukiwaniu(self):
        """Parametry sortowania są zachowane w kontekście podczas jednoczesnego wyszukiwania."""
        r = self.client.get(self._url(q='Anna', sort='created_at', dir='desc'))
        self.assertEqual(r.context['sort'], 'created_at')
        self.assertEqual(r.context['direction'], 'desc')

    def test_wyszukiwanie_po_pesel(self):
        """Wyszukiwanie po numerze PESEL zwraca dopasowanego klienta i wyklucza pozostałych."""
        r = self.client.get(self._url(q='90020223456'))
        pks = self._pks(r)
        self.assertIn(self.klient_b.pk, pks)
        self.assertNotIn(self.klient.pk, pks)

    def test_wyszukiwanie_po_nip(self):
        """Wyszukiwanie po numerze NIP zwraca dopasowaną firmę i wyklucza pozostałych klientów."""
        r = self.client.get(self._url(q='1234567890'))
        pks = self._pks(r)
        self.assertIn(self.klient_c.pk, pks)
        self.assertNotIn(self.klient.pk, pks)

    def test_wyszukiwanie_po_fragmencie_peselu(self):
        """Wyszukiwanie po fragmencie numeru PESEL zwraca klientów z pasującym numerem."""
        r = self.client.get(self._url(q='900202'))
        pks = self._pks(r)
        self.assertIn(self.klient_b.pk, pks)
