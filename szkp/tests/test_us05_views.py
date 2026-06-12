from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseStatus, CaseType,
    Client, ClientType, Task,
)
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class CaseListSearchTest(TestCase):
    """case_list: filtrowanie i wyszukiwanie querysetem."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pracownik', password='pass', is_staff=True)
        cls.klient_a = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Jan', last_name='Testowy', pesel='89010112345',
        )
        cls.klient_b = Client.objects.create(
            type=ClientType.FIRMA,
            company_name='Firma XYZ', nip='5250012345',
        )
        cls.sprawa_nowa = Case.objects.create(
            client=cls.klient_a, case_number='TST-LISTA-001',
            title='Sprawa nowa', case_type=CaseType.CYWILNA,
            status=CaseStatus.NOWA,
        )
        cls.sprawa_zakonczona = Case.objects.create(
            client=cls.klient_a, case_number='TST-LISTA-002',
            title='Sprawa zakończona', case_type=CaseType.KARNA,
            status=CaseStatus.ZAKOŃCZONA,
            court_case_number='SYGN-123',
        )
        cls.sprawa_firmy = Case.objects.create(
            client=cls.klient_b, case_number='TST-LISTA-003',
            title='Sprawa firmy', case_type=CaseType.CYWILNA,
            status=CaseStatus.W_TOKU,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_filtr_po_statusie_zaweza_wyniki(self):
        r = self.client.get(reverse('szkp:case_list'), {'status': 'nowa'})
        numery = [c.case_number for c in r.context['page_obj']]
        self.assertIn('TST-LISTA-001', numery)
        self.assertNotIn('TST-LISTA-002', numery)
        self.assertNotIn('TST-LISTA-003', numery)

    def test_filtr_po_typie_zaweza_wyniki(self):
        r = self.client.get(reverse('szkp:case_list'), {'type': 'karna'})
        numery = [c.case_number for c in r.context['page_obj']]
        self.assertIn('TST-LISTA-002', numery)
        self.assertNotIn('TST-LISTA-001', numery)

    def test_wyszukiwanie_po_numerze_sprawy(self):
        r = self.client.get(reverse('szkp:case_list'), {'q': 'TST-LISTA-001'})
        numery = [c.case_number for c in r.context['page_obj']]
        self.assertEqual(numery, ['TST-LISTA-001'])

    def test_wyszukiwanie_po_sygnaturze_sadowej(self):
        r = self.client.get(reverse('szkp:case_list'), {'q': 'SYGN-123'})
        numery = [c.case_number for c in r.context['page_obj']]
        self.assertIn('TST-LISTA-002', numery)

    def test_wyszukiwanie_po_nazwisku_klienta(self):
        r = self.client.get(reverse('szkp:case_list'), {'q': 'Testowy'})
        numery = [c.case_number for c in r.context['page_obj']]
        self.assertIn('TST-LISTA-001', numery)
        self.assertIn('TST-LISTA-002', numery)
        self.assertNotIn('TST-LISTA-003', numery)


@tag('integration')
class CaseCreateViewTest(StaffLawyerTestCase):
    """case_form (nowa sprawa): walidacja POST, tworzenie, auto-przypisanie prawnika."""

    def _post_new(self, data):
        return self.client.post(reverse('szkp:case_new'), data)

    def _valid_data(self, **overrides):
        data = {
            'case_number': 'TST-NEW-001',
            'title': 'Nowa sprawa testowa',
            'client': self.klient.pk,
            'case_type': CaseType.CYWILNA,
        }
        data.update(overrides)
        return data

    def test_get_zwraca_200(self):
        r = self.client.get(reverse('szkp:case_new'))
        self.assertEqual(r.status_code, 200)

    def test_post_tworzy_sprawe(self):
        self._post_new(self._valid_data())
        self.assertTrue(Case.objects.filter(case_number='TST-NEW-001').exists())

    def test_post_brak_numeru_zwraca_blad(self):
        r = self._post_new(self._valid_data(case_number=''))
        self.assertEqual(r.status_code, 200)
        self.assertIn('case_number', r.context['errors'])

    def test_post_brak_tytulu_zwraca_blad(self):
        r = self._post_new(self._valid_data(title=''))
        self.assertEqual(r.status_code, 200)
        self.assertIn('title', r.context['errors'])

    def test_post_status_domyslnie_nowa(self):
        self._post_new(self._valid_data())
        case = Case.objects.get(case_number='TST-NEW-001')
        self.assertEqual(case.status, CaseStatus.NOWA)

    def test_post_przypisuje_prawnika_prowadzacy(self):
        self._post_new(self._valid_data())
        case = Case.objects.get(case_number='TST-NEW-001')
        self.assertTrue(
            CaseLawyer.objects.filter(
                case=case, lawyer=self.lawyer, role=CaseLawyerRole.PROWADZACY,
            ).exists()
        )

    def test_po_utworzeniu_redirect(self):
        r = self._post_new(self._valid_data())
        self.assertEqual(r.status_code, 302)

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(reverse('szkp:case_new'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])


@tag('integration')
class CaseEditViewTest(StaffLawyerTestCase):
    """case_form (edycja): aktualizacja danych, zmiana statusu ustawia closed_at."""

    def setUp(self):
        super().setUp()
        self.sprawa = Case.objects.create(
            client=self.klient, case_number='TST-EDIT-001',
            title='Stary tytuł', case_type=CaseType.CYWILNA,
        )

    def test_get_zwraca_200_z_danymi(self):
        r = self.client.get(reverse('szkp:case_edit', kwargs={'pk': self.sprawa.pk}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['form_data']['title'], 'Stary tytuł')

    def test_post_aktualizuje_tytul(self):
        self.client.post(
            reverse('szkp:case_edit', kwargs={'pk': self.sprawa.pk}),
            {
                'case_number': 'TST-EDIT-001',
                'title': 'Nowy tytuł',
                'client': self.klient.pk,
                'case_type': CaseType.CYWILNA,
                'status': CaseStatus.NOWA,
            },
        )
        self.sprawa.refresh_from_db()
        self.assertEqual(self.sprawa.title, 'Nowy tytuł')

    def test_zmiana_statusu_na_zakonczona_ustawia_closed_at(self):
        self.client.post(
            reverse('szkp:case_edit', kwargs={'pk': self.sprawa.pk}),
            {
                'case_number': 'TST-EDIT-001',
                'title': 'Stary tytuł',
                'client': self.klient.pk,
                'case_type': CaseType.CYWILNA,
                'status': CaseStatus.ZAKOŃCZONA,
            },
        )
        self.sprawa.refresh_from_db()
        self.assertIsNotNone(self.sprawa.closed_at)


@tag('integration')
class CaseDetailTasksTabLinksTest(StaffLawyerTestCase):
    """case_detail zakładka zadania: tytuły zadań linkują do my_tasks z filtrem sygnatury."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-TASKLINK-001',
            title='Sprawa z zadaniami', case_type=CaseType.CYWILNA,
        )
        cls.task = Task.objects.create(
            title='Zadanie klikalne',
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
            case=cls.sprawa,
        )

    def _url(self):
        return reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=zadania'

    def test_tytul_zadania_jest_linkiem_do_my_tasks_z_filtrem_sygnatury(self):
        r = self.client.get(self._url())
        expected_url = reverse('szkp:my_tasks') + f'?case_number={self.sprawa.case_number}'
        self.assertContains(r, expected_url)
