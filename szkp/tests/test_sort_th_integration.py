"""
R-04 — Testy integracyjne: renderowanie tagu sort_th w szablonach Django.

Tagi: @tag('integration')
"""
from datetime import date
from decimal import Decimal

from django.template import Context, Template, TemplateSyntaxError
from django.test import RequestFactory, TestCase, tag
from django.urls import reverse

from szkp.models import Case, CaseType, Client, ClientType, Invoice, InvoiceStatus
from szkp.tests.base import StaffLawyerTestCase


# ---------------------------------------------------------------------------
# TI-R04-01 – TI-R04-07: Tag jako jednostka w silniku szablonów
# ---------------------------------------------------------------------------

@tag('integration')
class SortThTagLoadTest(TestCase):
    """Weryfikuje że tag jest poprawnie zarejestrowany i ładowalny."""

    # TI-R04-01
    def test_load_szkp_tags_nie_rzuca_bledu(self):
        """{% load szkp_tags %} nie rzuca TemplateSyntaxError."""
        try:
            Template('{% load szkp_tags %}')
        except TemplateSyntaxError as e:
            self.fail('{%% load szkp_tags %%} — TemplateSyntaxError: ' + str(e))

    # TI-R04-02
    def test_sort_th_renderuje_element_th(self):
        """{% sort_th "col" "Etykieta" %} renderuje element <th>."""
        factory = RequestFactory()
        request = factory.get('/test/', {'sort': '', 'dir': 'asc'})
        tpl = Template(
            '{% load szkp_tags %}'
            '{% sort_th "col" "Etykieta" %}'
        )
        ctx = Context({'sort': '', 'direction': 'asc', 'request': request})
        output = tpl.render(ctx)
        self.assertIn('<th', output)
        self.assertIn('</th>', output)

    # TI-R04-03
    def test_sort_th_aktywna_kolumna_ma_klase_sort_active(self):
        """Renderowany <th> ma klasę szkp-sort-active gdy key == sort w kontekście."""
        factory = RequestFactory()
        request = factory.get('/test/', {'sort': 'case_number', 'dir': 'asc'})
        tpl = Template(
            '{% load szkp_tags %}'
            '{% sort_th "case_number" "Sygnatura" %}'
        )
        ctx = Context({'sort': 'case_number', 'direction': 'asc', 'request': request})
        output = tpl.render(ctx)
        self.assertIn('szkp-sort-active', output)

    # TI-R04-04
    def test_sort_th_nieaktywna_kolumna_nie_ma_klasy_sort_active(self):
        """Renderowany <th> nie ma klasy szkp-sort-active gdy key != sort."""
        factory = RequestFactory()
        request = factory.get('/test/', {'sort': 'client', 'dir': 'asc'})
        tpl = Template(
            '{% load szkp_tags %}'
            '{% sort_th "case_number" "Sygnatura" %}'
        )
        ctx = Context({'sort': 'client', 'direction': 'asc', 'request': request})
        output = tpl.render(ctx)
        self.assertNotIn('szkp-sort-active', output)

    # TI-R04-05
    def test_sort_th_link_zawiera_etykiete(self):
        """Renderowany tag zawiera przekazaną etykietę kolumny."""
        factory = RequestFactory()
        request = factory.get('/test/')
        tpl = Template(
            '{% load szkp_tags %}'
            '{% sort_th "case_number" "Moja Etykieta" %}'
        )
        ctx = Context({'sort': '', 'direction': 'asc', 'request': request})
        output = tpl.render(ctx)
        self.assertIn('Moja Etykieta', output)

    # TI-R04-06
    def test_sort_th_link_zawiera_href_z_sort(self):
        """Renderowany <a> ma href zawierający sort=<key>."""
        factory = RequestFactory()
        request = factory.get('/test/')
        tpl = Template(
            '{% load szkp_tags %}'
            '{% sort_th "invoice_number" "Numer" %}'
        )
        ctx = Context({'sort': '', 'direction': 'asc', 'request': request})
        output = tpl.render(ctx)
        self.assertIn('sort=invoice_number', output)

    # TI-R04-07
    def test_sort_th_ikona_asc_na_aktywnej_kolumnie(self):
        """Aktywna kolumna ASC zawiera klasę szkp-sort-icon--asc."""
        factory = RequestFactory()
        request = factory.get('/test/', {'sort': 'status', 'dir': 'asc'})
        tpl = Template(
            '{% load szkp_tags %}'
            '{% sort_th "status" "Status" %}'
        )
        ctx = Context({'sort': 'status', 'direction': 'asc', 'request': request})
        output = tpl.render(ctx)
        self.assertIn('szkp-sort-icon--asc', output)

    # TI-R04-08
    def test_sort_th_ikona_desc_na_aktywnej_kolumnie(self):
        """Aktywna kolumna DESC zawiera klasę szkp-sort-icon--desc."""
        factory = RequestFactory()
        request = factory.get('/test/', {'sort': 'status', 'dir': 'desc'})
        tpl = Template(
            '{% load szkp_tags %}'
            '{% sort_th "status" "Status" %}'
        )
        ctx = Context({'sort': 'status', 'direction': 'desc', 'request': request})
        output = tpl.render(ctx)
        self.assertIn('szkp-sort-icon--desc', output)

    # TI-R04-09
    def test_sort_th_link_zachowuje_obecne_params_get(self):
        """href w tagu zachowuje bieżące params GET (poza sort/dir/page)."""
        factory = RequestFactory()
        request = factory.get('/test/', {'q': 'alfa', 'status': 'nowa', 'page': '3'})
        tpl = Template(
            '{% load szkp_tags %}'
            '{% sort_th "case_number" "Sygnatura" %}'
        )
        ctx = Context({'sort': '', 'direction': 'asc', 'request': request})
        output = tpl.render(ctx)
        self.assertIn('q=alfa', output)
        self.assertIn('status=nowa', output)
        self.assertNotIn('page=', output)


# ---------------------------------------------------------------------------
# TI-R04-10 – TI-R04-14: Widok case_list z tagiem sort_th
# ---------------------------------------------------------------------------

@tag('integration')
class SortThCaseListViewTest(StaffLawyerTestCase):
    """Widok case_list renderuje sortowalne nagłówki przez tag sort_th."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-INTH-C001',
            title='Sprawa integracyjna', case_type=CaseType.CYWILNA,
        )

    # TI-R04-10
    def test_case_list_zwraca_200(self):
        """case_list z sort_th renderuje się bez błędu (HTTP 200)."""
        r = self.client.get(reverse('szkp:case_list') + '?sort=case_number&dir=asc')
        self.assertEqual(r.status_code, 200)

    # TI-R04-11
    def test_case_list_aktywna_kolumna_ma_klase_w_html(self):
        """Odpowiedź HTML case_list zawiera szkp-sort-active dla posortowanej kolumny."""
        r = self.client.get(reverse('szkp:case_list') + '?sort=case_number&dir=asc')
        self.assertContains(r, 'szkp-sort-active')

    # TI-R04-12
    def test_case_list_sort_link_zachowuje_q_w_href(self):
        """W HTML case_list linki sortowania zachowują parametr q."""
        r = self.client.get(
            reverse('szkp:case_list') + '?q=TST-INTH&sort=client&dir=asc'
        )
        self.assertContains(r, 'q=TST-INTH')

    # TI-R04-13
    def test_case_list_kolumna_prawnicy_nie_ma_linku_sort(self):
        """W HTML case_list kolumna 'Prawnicy' nie zawiera sort= w żadnym tagu <th>."""
        r = self.client.get(reverse('szkp:case_list'))
        content = r.content.decode()
        # Sprawdź że po znalezieniu "Prawnicy" w nagłówku nie ma sort= w tym samym th
        prawnicy_idx = content.find('Prawnicy')
        self.assertGreater(prawnicy_idx, 0, "Brak kolumny 'Prawnicy' w HTML")
        # Fragment <th> zawierający "Prawnicy" nie powinien mieć href z sort=
        th_start = content.rfind('<th', 0, prawnicy_idx)
        th_end = content.find('</th>', prawnicy_idx)
        th_fragment = content[th_start:th_end]
        self.assertNotIn('sort=', th_fragment)

    # TI-R04-14
    def test_case_list_sort_link_nie_zawiera_page_w_href(self):
        """Linki sortowania w case_list nie propagują parametru page."""
        r = self.client.get(
            reverse('szkp:case_list') + '?sort=case_number&dir=asc&page=2'
        )
        content = r.content.decode()
        # Szukamy linku z sort=case_number — musi nie zawierać page=
        import re
        sort_links = re.findall(r'href="([^"]*sort=case_number[^"]*)"', content)
        self.assertTrue(len(sort_links) > 0, 'Brak linku sort=case_number w HTML')
        for href in sort_links:
            self.assertNotIn('page=', href,
                             f'Link sortowania zawiera page=: {href!r}')


# ---------------------------------------------------------------------------
# TI-R04-15 – TI-R04-18: Widok client_list z tagiem sort_th
# ---------------------------------------------------------------------------

@tag('integration')
class SortThClientListViewTest(StaffLawyerTestCase):
    """Widok client_list renderuje sortowalne nagłówki przez tag sort_th."""

    # TI-R04-15
    def test_client_list_zwraca_200(self):
        """client_list z sort_th renderuje się bez błędu (HTTP 200)."""
        r = self.client.get(reverse('szkp:client_list') + '?sort=last_name&dir=asc')
        self.assertEqual(r.status_code, 200)

    # TI-R04-16
    def test_client_list_aktywna_kolumna_ma_klase_w_html(self):
        """Odpowiedź HTML client_list zawiera szkp-sort-active dla aktywnej kolumny."""
        r = self.client.get(reverse('szkp:client_list') + '?sort=last_name&dir=asc')
        self.assertContains(r, 'szkp-sort-active')

    # TI-R04-17
    def test_client_list_kolumna_pesel_nie_ma_linku_sort(self):
        """Kolumna 'PESEL / NIP' w client_list nie ma linku sortowania."""
        r = self.client.get(reverse('szkp:client_list'))
        content = r.content.decode()
        pesel_idx = content.find('PESEL')
        self.assertGreater(pesel_idx, 0, "Brak kolumny 'PESEL / NIP' w HTML")
        th_start = content.rfind('<th', 0, pesel_idx)
        th_end = content.find('</th>', pesel_idx)
        th_fragment = content[th_start:th_end]
        self.assertNotIn('sort=', th_fragment)

    # TI-R04-18
    def test_client_list_sort_link_zachowuje_q(self):
        """Linki sortowania w client_list zawierają q= gdy wyszukiwanie jest aktywne."""
        r = self.client.get(
            reverse('szkp:client_list') + '?q=anna&sort=type&dir=asc'
        )
        content = r.content.decode()
        import re
        sort_links = re.findall(r'href="([^"]*sort=last_name[^"]*)"', content)
        self.assertTrue(len(sort_links) > 0, 'Brak linku sort=last_name w HTML')
        for href in sort_links:
            self.assertIn('q=anna', href)


# ---------------------------------------------------------------------------
# TI-R04-19 – TI-R04-22: Widok invoice_list z tagiem sort_th
# ---------------------------------------------------------------------------

@tag('integration')
class SortThInvoiceListViewTest(StaffLawyerTestCase):
    """Widok invoice_list renderuje sortowalne nagłówki przez tag sort_th."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-INTH-I001',
            title='Sprawa do faktur', case_type=CaseType.CYWILNA,
        )
        cls.faktura = Invoice.objects.create(
            case=cls.sprawa,
            invoice_number='FV/TEST/001',
            issue_date=date(2025, 1, 10),
            due_date=date(2025, 2, 10),
            net_amount=Decimal('1000.00'),
            status=InvoiceStatus.WYSTAWIONA,
        )

    # TI-R04-19
    def test_invoice_list_zwraca_200(self):
        """invoice_list z sort_th renderuje się bez błędu (HTTP 200)."""
        r = self.client.get(
            reverse('szkp:invoice_list') + '?sort=invoice_number&dir=asc'
        )
        self.assertEqual(r.status_code, 200)

    # TI-R04-20
    def test_invoice_list_aktywna_kolumna_ma_klase_w_html(self):
        """Odpowiedź HTML invoice_list zawiera szkp-sort-active dla aktywnej kolumny."""
        r = self.client.get(
            reverse('szkp:invoice_list') + '?sort=invoice_number&dir=asc'
        )
        self.assertContains(r, 'szkp-sort-active')

    # TI-R04-21
    def test_invoice_list_sort_link_zachowuje_status_i_q(self):
        """Linki sortowania w invoice_list zachowują status i q w href."""
        r = self.client.get(
            reverse('szkp:invoice_list')
            + '?status=wystawiona&q=FV&sort=due_date&dir=asc'
        )
        content = r.content.decode()
        import re
        # Link do sortowania po invoice_number musi zachować status i q
        sort_links = re.findall(r'href="([^"]*sort=invoice_number[^"]*)"', content)
        self.assertTrue(len(sort_links) > 0, 'Brak linku sort=invoice_number w HTML')
        for href in sort_links:
            self.assertIn('status=wystawiona', href)
            self.assertIn('q=FV', href)

    # TI-R04-22
    def test_invoice_list_szesc_kolumn_sortowalnych(self):
        """HTML invoice_list zawiera linki dla wszystkich 6 sortowalnych kolumn."""
        r = self.client.get(reverse('szkp:invoice_list'))
        content = r.content.decode()
        expected = [
            'sort=invoice_number', 'sort=case', 'sort=issue_date',
            'sort=due_date', 'sort=gross_amount', 'sort=status',
        ]
        for sort_param in expected:
            self.assertIn(sort_param, content,
                          f'Brak linku {sort_param} w HTML invoice_list')
