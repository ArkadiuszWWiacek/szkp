"""
R-05 — Paginacja listy faktur.
Testy integracyjne — faza RED.

Uwaga o testach jednostkowych:
    R-05 nie wprowadza żadnej wydzielonej, czystej funkcji (jak sort_th w R-04).
    Paginator jest wbudowany bezpośrednio w invoice_list, które zawsze uderza
    w bazę danych. Testy SimpleTestCase (bez DB) nie mają tu zastosowania.
    Wszystkie testy poniżej są tagowane @tag('integration').

Podział klas:
    InvoiceListPaginatorContractTest — kontrakt widoku (klucze kontekstu, typy).
        Minimalne dane testowe (0 faktur lub 1), padają przez KeyError.
    InvoiceListPaginationBehaviourTest — zachowanie przy 25 fakturach.
        Padają przez KeyError lub błąd asercji (25 != 20 itp.).
"""
import datetime
from decimal import Decimal

from django.core.paginator import Page
from django.test import TestCase, tag
from django.urls import reverse

from szkp.models import Case, CaseType, Invoice, InvoiceStatus
from szkp.tests.base import StaffLawyerTestCase


URL = '/szkp/faktury/'


def _bulk(case, count, prefix, status=InvoiceStatus.WYSTAWIONA):
    today = datetime.date.today()
    Invoice.objects.bulk_create([
        Invoice(
            case=case,
            invoice_number=f'{prefix}{i:03d}',
            issue_date=today,
            due_date=today + datetime.timedelta(days=14),
            net_amount=Decimal('100.00') * i,
            status=status,
        )
        for i in range(1, count + 1)
    ])


# ===========================================================================
# Kontrakt widoku (klucze kontekstu, typy) — TI-R05-01 – TI-R05-05
# ===========================================================================

@tag('integration')
class InvoiceListPaginatorContractTest(StaffLawyerTestCase):
    """
    Kontrakt invoice_list po R-05: które klucze kontekstu istnieją i jakie mają typy.
    Dane testowe: 0 faktur w DB — weryfikujemy sam interfejs widoku.
    Wszystkie testy padają teraz przez KeyError: 'page_obj' nie ma w kontekście.
    """

    # TI-R05-01
    def test_kontekst_zawiera_klucz_page_obj(self):
        """
        Po R-05 invoice_list zwraca 'page_obj' w kontekście.
        PADA: klucz 'page_obj' nie istnieje w kontekście (widok jeszcze go nie dodaje).
        """
        r = self.client.get(URL)
        self.assertIn(
            'page_obj', r.context,
            "Klucz 'page_obj' nieobecny w kontekście invoice_list. "
            "Paginator nie jest jeszcze zaimplementowany."
        )

    # TI-R05-02
    def test_invoices_jest_aliasem_page_obj(self):
        """
        context['invoices'] i context['page_obj'] to ten sam obiekt.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL)
        self.assertIs(
            r.context['invoices'],
            r.context['page_obj'],
            "context['invoices'] musi być tym samym obiektem co context['page_obj']."
        )

    # TI-R05-03
    def test_page_obj_jest_instancja_Page(self):
        """
        context['page_obj'] jest instancją django.core.paginator.Page.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL)
        self.assertIsInstance(
            r.context['page_obj'],
            Page,
            f"context['page_obj'] powinno być instancją Page, "
            f"jest: {type(r.context.get('page_obj'))}."
        )

    # TI-R05-04
    def test_domyslna_strona_to_1(self):
        """
        Bez parametru ?page widok zwraca page_obj.number == 1.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL)
        self.assertEqual(
            r.context['page_obj'].number, 1,
            "Domyślna strona powinna być 1, gdy brak parametru ?page."
        )

    # TI-R05-05
    def test_parametr_page_2_zwraca_strone_2(self):
        """
        ?page=2 zwraca page_obj.number == 2.
        Przy braku rekordów Django Paginator zwraca pierwszą (i jedyną) stronę —
        ale sam fakt, że page_obj istnieje w kontekście jest tutaj kluczowy.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL + '?page=2')
        self.assertIn('page_obj', r.context,
                      "Klucz 'page_obj' nieobecny po dodaniu ?page=2.")


# ===========================================================================
# Zachowanie paginatora przy 25 fakturach — TI-R05-06 – TI-R05-12
# ===========================================================================

@tag('integration')
class InvoiceListPaginationBehaviourTest(StaffLawyerTestCase):
    """
    Zachowanie invoice_list z 25 fakturami w DB.

    TI-R05-06 pada przez błąd asercji: len(context['invoices']) == 25, nie 20.
    TI-R05-07 – TI-R05-12 padają przez KeyError: 'page_obj' nieobecny.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-R05-PAG-001',
            title='Sprawa do testów paginacji', case_type=CaseType.CYWILNA,
        )
        _bulk(cls.sprawa, 25, prefix='FV/R05P/')

    # TI-R05-06
    def test_strona_1_ma_dokladnie_20_elementow(self):
        """
        Przy 25 fakturach w DB strona 1 zawiera dokładnie 20 rekordów.
        PADA: widok zwraca wszystkie 25 bez ograniczenia (brak paginatora).
        """
        r = self.client.get(URL)
        count = len(list(r.context['invoices']))
        self.assertEqual(
            count, 20,
            f"Strona 1 powinna mieć 20 elementów, ma {count}. "
            "Paginator nie jest zaimplementowany — zwracane są wszystkie rekordy."
        )

    # TI-R05-07
    def test_has_next_true_gdy_25_faktur(self):
        """
        page_obj.has_next() == True gdy istnieje strona 2.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL)
        self.assertTrue(
            r.context['page_obj'].has_next(),
            "page_obj.has_next() powinno być True przy 25 fakturach (2 strony)."
        )

    # TI-R05-08
    def test_paginator_count_rowna_sie_liczbie_rekordow_w_db(self):
        """
        page_obj.paginator.count zwraca łączną liczbę faktur (25).
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL)
        self.assertEqual(
            r.context['page_obj'].paginator.count, 25,
            "page_obj.paginator.count powinno zwracać 25."
        )

    # TI-R05-09
    def test_strona_2_ma_5_elementow(self):
        """
        Strona 2 z 25 faktur (page_size=20) zawiera 5 rekordów.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL + '?page=2')
        count = len(list(r.context['page_obj']))
        self.assertEqual(
            count, 5,
            f"Strona 2 powinna mieć 5 elementów, ma {count}."
        )

    # TI-R05-10
    def test_filtr_statusu_dziala_przed_paginacja(self):
        """
        Status filter jest stosowany do queryset PRZED paginacją.
        Przy 25 fakturach wystawiona i filtrze ?status=wystawiona
        strona 2 nadal zwraca tylko faktury o statusie wystawiona.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL + '?status=wystawiona&page=2')
        page_obj = r.context['page_obj']
        statuses = [inv.status for inv in page_obj]
        self.assertTrue(
            all(s == InvoiceStatus.WYSTAWIONA for s in statuses),
            f"Na stronie 2 z filtrem ?status=wystawiona wszystkie rekordy "
            f"powinny mieć status WYSTAWIONA. Znalezione statusy: {statuses}"
        )

    # TI-R05-11
    def test_wyszukiwanie_dziala_przed_paginacja(self):
        """
        Wyszukiwanie (?q=) jest stosowane do queryset PRZED paginacją.
        Przy 25 fakturach pasujących do 'FV/R05P/' i ?q=FV/R05P/
        strona 2 zwraca wyłącznie pasujące rekordy.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL + '?q=FV%2FR05P%2F&page=2')
        page_obj = r.context['page_obj']
        numbers = [inv.invoice_number for inv in page_obj]
        self.assertTrue(
            all('FV/R05P/' in n for n in numbers),
            f"Strona 2 z wyszukiwaniem 'FV/R05P/' powinna zawierać "
            f"tylko pasujące faktury. Znalezione numery: {numbers}"
        )

    # TI-R05-12
    def test_has_next_false_gdy_20_lub_mniej_faktur(self):
        """
        page_obj.has_next() == False gdy jest dokładnie 20 faktur (mieści się na 1 stronie).
        Używamy filtra ?status=przeterminowana — w DB nie ma takich faktur,
        więc strona 1 z 0 wynikami nie ma następnej strony.
        PADA: 'page_obj' nie ma w kontekście → KeyError.
        """
        r = self.client.get(URL + '?status=przeterminowana')
        self.assertFalse(
            r.context['page_obj'].has_next(),
            "page_obj.has_next() powinno być False gdy wyniki mieszczą się na 1 stronie."
        )
