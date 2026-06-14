from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from szkp.models import (
    Case, CaseLawyer, CaseLawyerRole, CaseStatus, CaseType,
    Client, ClientType, Lawyer, Task,
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


@tag('integration')
class CaseLawyerAddViewTest(StaffLawyerTestCase):
    """case_lawyer_add: formularz przypisania prawnika do sprawy."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-CLADD-001',
            title='Sprawa do testów', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=cls.sprawa, lawyer=cls.lawyer, role=CaseLawyerRole.PROWADZACY,
        )
        cls.lawyer2 = Lawyer.objects.create(
            first_name='Maria', last_name='Kowalska', bar_number='PL002',
        )

    def _url(self):
        return reverse('szkp:case_lawyer_add', kwargs={'case_pk': self.sprawa.pk})

    def _valid_data(self, **overrides):
        data = {
            'lawyer': self.lawyer2.pk,
            'role': CaseLawyerRole.ASYSTENT,
        }
        data.update(overrides)
        return data

    def _post(self, data):
        return self.client.post(self._url(), data)

    def test_get_formularz_zwraca_200(self):
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_get_kontekst_zawiera_dostepnych_prawnikow(self):
        r = self.client.get(self._url())
        available = list(r.context['available_lawyers'])
        self.assertIn(self.lawyer2, available)
        self.assertNotIn(self.lawyer, available)

    def test_get_kontekst_zawiera_role_bez_prowadzacego(self):
        r = self.client.get(self._url())
        wartosci = [val for val, _ in r.context['role_choices']]
        self.assertNotIn(CaseLawyerRole.PROWADZACY, wartosci)
        self.assertIn(CaseLawyerRole.ASYSTENT, wartosci)
        self.assertIn(CaseLawyerRole.DORADCA, wartosci)

    def test_get_kontekst_zawiera_sprawe(self):
        r = self.client.get(self._url())
        self.assertEqual(r.context['case'], self.sprawa)

    def test_post_valid_tworzy_caselawyer(self):
        self._post(self._valid_data())
        self.assertTrue(
            CaseLawyer.objects.filter(
                case=self.sprawa, lawyer=self.lawyer2, role=CaseLawyerRole.ASYSTENT,
            ).exists()
        )

    def test_post_valid_redirect_do_prawnicy_tab(self):
        r = self._post(self._valid_data())
        expected = reverse('szkp:case_detail', args=[self.sprawa.pk]) + '?tab=prawnicy'
        self.assertRedirects(r, expected, fetch_redirect_response=False)

    def test_post_brak_prawnika_zwraca_blad(self):
        r = self._post({'lawyer': '', 'role': CaseLawyerRole.ASYSTENT})
        self.assertEqual(r.status_code, 200)
        self.assertIn('lawyer', r.context['errors'])

    def test_post_brak_roli_zwraca_blad(self):
        r = self._post({'lawyer': self.lawyer2.pk, 'role': ''})
        self.assertEqual(r.status_code, 200)
        self.assertIn('role', r.context['errors'])

    def test_post_rola_prowadzacy_zwraca_blad(self):
        r = self._post(self._valid_data(role=CaseLawyerRole.PROWADZACY))
        self.assertEqual(r.status_code, 200)
        self.assertIn('role', r.context['errors'])

    def test_post_duplikat_prawnika_zwraca_blad(self):
        CaseLawyer.objects.create(
            case=self.sprawa, lawyer=self.lawyer2, role=CaseLawyerRole.ASYSTENT,
        )
        r = self._post(self._valid_data())
        self.assertEqual(r.status_code, 200)
        self.assertIn('lawyer', r.context['errors'])


@tag('integration')
class CaseLawyerAddAccessTest(TestCase):
    """case_lawyer_add: kontrola dostępu."""

    @classmethod
    def setUpTestData(cls):
        cls.user_staff = User.objects.create_user('staff_cl', password='pass', is_staff=True)
        cls.lawyer_staff = Lawyer.objects.create(
            user=cls.user_staff, first_name='Jan', last_name='Prawnik', bar_number='PL-ACC-001',
        )
        cls.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Anna', last_name='Klientka', pesel='99010112345',
        )
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-CLADD-ACC-001',
            title='Sprawa do testów dostępu', case_type=CaseType.CYWILNA,
        )

    def _url(self):
        return reverse('szkp:case_lawyer_add', kwargs={'case_pk': self.sprawa.pk})

    def test_wymaga_zalogowania(self):
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])

    def test_nieprzypisany_prawnik_nie_ma_dostepu(self):
        user2 = User.objects.create_user('obcy_cl', password='pass', is_staff=False)
        Lawyer.objects.create(
            user=user2, first_name='Obcy', last_name='Prawnik', bar_number='PL-ACC-999',
        )
        self.client.force_login(user2)
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 403)
