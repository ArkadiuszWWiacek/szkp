"""Testy integracyjne: Widoki list dla superusera (PSU-L01 – PSU-L05)."""
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from szkp.models import Lawyer, Task, TaskStatus
from szkp.tests.utils import make_due

SPRAWY      = '/szkp/sprawy/'
KLIENCI     = '/szkp/klienci/'
FAKTURY     = '/szkp/faktury/'
ZADANIA     = '/szkp/zadania/'
UZYTKOWNICY = '/szkp/uzytkownicy/'


class _SuperuserListsBase(TestCase):
    """Baza: superuser + staff, bez danych domenowych."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_lst_int', password='x',
            is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_lst_int', password='x',
            is_staff=True, is_superuser=False,
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL01–TI-SUL02: case_list — branching na szablon
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserCaseListViewTest(_SuperuserListsBase):
    """TI-SUL01–TI-SUL02: GET /szkp/sprawy/ → case_list_su.html dla superusera."""

    def test_ti_sul01_superuser_dostaje_case_list_su(self):
        """TI-SUL01: GET /szkp/sprawy/ jako superuser → case_list_su.html (dash layout)."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:case_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'szkp/case_list_su.html')

    def test_ti_sul02_staff_nie_dostaje_dash_szablonu(self):
        """TI-SUL02: GET /szkp/sprawy/ jako staff (non-superuser) → NIE case_list_su.html."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('szkp:case_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'szkp/case_list_su.html')


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL03–TI-SUL04: client_list — branching na szablon
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserClientListViewTest(_SuperuserListsBase):
    """TI-SUL03–TI-SUL04: GET /szkp/klienci/ → client_list_su.html dla superusera."""

    def test_ti_sul03_superuser_dostaje_client_list_su(self):
        """TI-SUL03: GET /szkp/klienci/ jako superuser → client_list_su.html (dash layout)."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'szkp/client_list_su.html')

    def test_ti_sul04_staff_nie_dostaje_dash_szablonu(self):
        """TI-SUL04: GET /szkp/klienci/ jako staff → NIE client_list_su.html."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('szkp:client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'szkp/client_list_su.html')


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL05–TI-SUL06: invoice_list — branching na szablon
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserInvoiceListViewTest(_SuperuserListsBase):
    """TI-SUL05–TI-SUL06: GET /szkp/faktury/ → invoice_list_su.html dla superusera."""

    def test_ti_sul05_superuser_dostaje_invoice_list_su(self):
        """TI-SUL05: GET /szkp/faktury/ jako superuser → invoice_list_su.html (dash layout)."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'szkp/invoice_list_su.html')

    def test_ti_sul06_staff_nie_dostaje_dash_szablonu(self):
        """TI-SUL06: GET /szkp/faktury/ jako staff → NIE invoice_list_su.html."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('szkp:invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'szkp/invoice_list_su.html')


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL07–TI-SUL08: my_tasks — branching na szablon
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserTaskListViewTest(TestCase):
    """TI-SUL07–TI-SUL08: GET /szkp/zadania/ → task_list_su.html dla superusera.

    my_tasks wymaga profilu Lawyer dla każdego użytkownika (get_object_or_404 na linii 21).
    Superuser nie ma Lawyer → 404 w RED (prawidłowy powód failu TI-SUL07).
    Staff ma Lawyer → 200 w RED; assertTemplateNotUsed(task_list_su.html) PASS (guard test).
    """

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_lst_task_int', password='x',
            is_staff=True, is_superuser=True,
        )
        cls.staff = User.objects.create_user(
            username='staff_lst_task_int', password='x',
            is_staff=True, is_superuser=False,
        )
        cls.staff_lawyer = Lawyer.objects.create(
            first_name='Staff', last_name='Prawnik',
            bar_number='TST/TI/STF/001',
            user=cls.staff,
        )

    def test_ti_sul07_superuser_dostaje_task_list_su(self):
        """TI-SUL07: GET /szkp/zadania/ jako superuser → task_list_su.html (dash layout).

        W fazie RED: widok nie ma branching → superuser (bez Lawyer) dostaje 404 zamiast 200.
        W fazie GREEN: widok rozgałęzia się dla is_superuser → 200 + task_list_su.html.
        """
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:my_tasks'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'szkp/task_list_su.html')

    def test_ti_sul08_staff_nie_dostaje_dash_szablonu(self):
        """TI-SUL08: GET /szkp/zadania/ jako staff (z Lawyer) → NIE task_list_su.html."""
        self.client.force_login(self.staff)
        response = self.client.get(reverse('szkp:my_tasks'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'szkp/task_list_su.html')

    def test_ti_sul19_queryset_su_prefetchuje_task_set(self):
        """TI-SUL19: Queryset SU używa prefetch_related — dostęp do task_set.all() nie powoduje extra SQL.

        W RED: brak prefetch_related → każde task.task_set.all() generuje query → assertNumQueries(0) fail.
        W GREEN: prefetch_related w my_tasks → cache zapełniony → 0 dodatkowych zapytań.
        """
        helper = Lawyer.objects.create(
            first_name='Helper', last_name='Prefetch', bar_number='TST/TI/HLP/001',
        )
        parent = Task.objects.create(
            title='Zadanie do prefetch testu',
            assigned_lawyer=helper, created_by=helper,
            due_date=make_due(3), status=TaskStatus.NOWE,
        )
        Task.objects.create(
            title='Podzadanie do prefetch testu',
            assigned_lawyer=helper, created_by=helper,
            parent_task=parent,
            due_date=make_due(5), status=TaskStatus.NOWE,
        )
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:my_tasks'))
        self.assertEqual(response.status_code, 200)
        tasks = list(response.context['tasks'])
        self.assertGreater(len(tasks), 0, 'Brak zadań w kontekście — nie można zweryfikować prefetch')
        with self.assertNumQueries(0):
            for task in tasks:
                list(task.task_set.all())

    def test_ti_sul20_podzadanie_wyswietlane_w_html_odpowiedzi(self):
        """TI-SUL20: HTML odpowiedzi dla SU zawiera tytuł podzadania (template iteruje task_set.all).

        W RED: szablon iteruje tylko zadania nadrzędne → podzadanie niewidoczne w HTML.
        W GREEN: szablon iteruje task.task_set.all → podzadanie renderowane w wierszu subtask.
        """
        helper = Lawyer.objects.create(
            first_name='Helper2', last_name='Render', bar_number='TST/TI/HLP/002',
        )
        parent = Task.objects.create(
            title='Zadanie nadrzędne render test',
            assigned_lawyer=helper, created_by=helper,
            due_date=make_due(3), status=TaskStatus.NOWE,
        )
        Task.objects.create(
            title='UNIKALNE_PODZADANIE_RENDER_TI_SUL20',
            assigned_lawyer=helper, created_by=helper,
            parent_task=parent,
            due_date=make_due(5), status=TaskStatus.NOWE,
        )
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('szkp:my_tasks'))
        self.assertContains(
            response,
            'UNIKALNE_PODZADANIE_RENDER_TI_SUL20',
            msg_prefix='Tytuł podzadania niewidoczny w HTML — '
                        'task_list_su.html nie iteruje task.task_set.all',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL21–TI-SUL25: task_list — sortowanie i wyszukiwanie dla SU
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserTaskListSortSearchViewTest(TestCase):
    """TI-SUL21–TI-SUL25: GET /szkp/zadania/ — sortowanie i wyszukiwanie dla superusera."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_user(
            username='su_sort_int', password='x',
            is_staff=True, is_superuser=True,
        )
        cls.prawnik = Lawyer.objects.create(
            first_name='Sort', last_name='Prawnik', bar_number='TST/TI/SRT/001',
        )
        cls.task_wczesny = Task.objects.create(
            title='Zadanie Wczesne',
            assigned_lawyer=cls.prawnik, created_by=cls.prawnik,
            due_date=make_due(2), status=TaskStatus.NOWE,
        )
        cls.task_pozny = Task.objects.create(
            title='Zadanie Pozne',
            assigned_lawyer=cls.prawnik, created_by=cls.prawnik,
            due_date=make_due(10), status=TaskStatus.W_TOKU,
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_ti_sul21_kontekst_zawiera_sort_i_direction(self):
        """TI-SUL21: GET /zadania/ jako SU → context['sort'] i context['direction'] są przekazane.

        W RED: widok nie przekazuje sort/direction → KeyError lub None.
        W GREEN: widok czyta GET params i dodaje do kontekstu.
        """
        response = self.client.get(reverse('szkp:my_tasks'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'sort', response.context,
            "context['sort'] brak — widok SU nie przekazuje parametru sortowania do szablonu",
        )
        self.assertIn(
            'direction', response.context,
            "context['direction'] brak — widok SU nie przekazuje kierunku sortowania do szablonu",
        )

    def test_ti_sul22_kontekst_zawiera_q(self):
        """TI-SUL22: GET /zadania/?q=test → context['q'] == 'test'.

        W RED: widok nie czyta GET['q'] → brak 'q' w kontekście.
        W GREEN: widok przekazuje q do kontekstu.
        """
        response = self.client.get(reverse('szkp:my_tasks') + '?q=test')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'q', response.context,
            "context['q'] brak — widok SU nie przekazuje frazy wyszukiwania do szablonu",
        )
        self.assertEqual(
            response.context['q'], 'test',
            f"context['q'] != 'test', otrzymano: {response.context.get('q')}",
        )

    def test_ti_sul23_wyszukiwanie_filtruje_po_tytule(self):
        """TI-SUL23: GET ?q=Wczesne → queryset zawiera tylko 'Zadanie Wczesne'.

        W RED: widok ignoruje GET['q'] → oba zadania w kontekście.
        W GREEN: widok filtruje title__icontains → tylko Wczesne.
        """
        response = self.client.get(reverse('szkp:my_tasks') + '?q=Wczesne')
        self.assertEqual(response.status_code, 200)
        tasks = list(response.context['tasks'])
        titles = [t.title for t in tasks]
        self.assertIn(
            'Zadanie Wczesne', titles,
            f"'Zadanie Wczesne' brak w wynikach ?q=Wczesne. Tytuły: {titles}",
        )
        self.assertNotIn(
            'Zadanie Pozne', titles,
            f"'Zadanie Pozne' nadal widoczne po ?q=Wczesne — filtr nie działa. Tytuły: {titles}",
        )

    def test_ti_sul24_sortuje_po_due_date_asc(self):
        """TI-SUL24: GET ?sort=due_date&dir=asc → zadania posortowane od najwcześniejszego.

        W RED: widok ignoruje GET sort/dir → kolejność nieokreślona.
        W GREEN: widok stosuje order_by('due_date') → Wczesne przed Późnym.
        """
        response = self.client.get(reverse('szkp:my_tasks') + '?sort=due_date&dir=asc')
        self.assertEqual(response.status_code, 200)
        tasks = list(response.context['tasks'])
        pks = [t.pk for t in tasks]
        self.assertGreaterEqual(len(pks), 2, 'Za mało zadań w kontekście')
        wczesne_idx = pks.index(self.task_wczesny.pk)
        pozne_idx = pks.index(self.task_pozny.pk)
        self.assertLess(
            wczesne_idx, pozne_idx,
            f'?sort=due_date&dir=asc: "Wczesne" (idx {wczesne_idx}) powinno być przed '
            f'"Późne" (idx {pozne_idx})',
        )

    def test_ti_sul25_sortuje_po_due_date_desc(self):
        """TI-SUL25: GET ?sort=due_date&dir=desc → zadania posortowane od najpóźniejszego.

        W RED: widok ignoruje GET sort/dir → kolejność nieokreślona.
        W GREEN: widok stosuje order_by('-due_date') → Późne przed Wczesnym.
        """
        response = self.client.get(reverse('szkp:my_tasks') + '?sort=due_date&dir=desc')
        self.assertEqual(response.status_code, 200)
        tasks = list(response.context['tasks'])
        pks = [t.pk for t in tasks]
        self.assertGreaterEqual(len(pks), 2, 'Za mało zadań w kontekście')
        wczesne_idx = pks.index(self.task_wczesny.pk)
        pozne_idx = pks.index(self.task_pozny.pk)
        self.assertLess(
            pozne_idx, wczesne_idx,
            f'?sort=due_date&dir=desc: "Późne" (idx {pozne_idx}) powinno być przed '
            f'"Wczesne" (idx {wczesne_idx})',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL09–TI-SUL13: user_list — dostęp i kontekst
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserUserListViewTest(_SuperuserListsBase):
    """TI-SUL09–TI-SUL13: GET /szkp/uzytkownicy/ — dostęp, szablon, kontekst."""

    def setUp(self):
        self.inny = User.objects.create_user(
            username='inny_uzytkownik_int', password='x',
        )

    def test_ti_sul09_superuser_dostaje_200_i_user_list_su(self):
        """TI-SUL09: GET /szkp/uzytkownicy/ jako superuser → 200 + user_list_su.html."""
        self.client.force_login(self.superuser)
        response = self.client.get(UZYTKOWNICY)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'szkp/user_list_su.html')

    def test_ti_sul10_staff_dostaje_403(self):
        """TI-SUL10: GET /szkp/uzytkownicy/ jako staff (non-superuser) → 403 Forbidden."""
        self.client.force_login(self.staff)
        response = self.client.get(UZYTKOWNICY)
        self.assertEqual(response.status_code, 403)

    def test_ti_sul11_niezalogowany_dostaje_redirect_na_login(self):
        """TI-SUL11: GET /szkp/uzytkownicy/ bez logowania → 302 redirect na stronę logowania."""
        response = self.client.get(UZYTKOWNICY)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_ti_sul12_kontekst_zawiera_users(self):
        """TI-SUL12: Kontekst odpowiedzi na /szkp/uzytkownicy/ zawiera klucz 'users'."""
        self.client.force_login(self.superuser)
        response = self.client.get(UZYTKOWNICY)
        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.context)

    def test_ti_sul13_lista_zawiera_wszystkich_uzytkownikow(self):
        """TI-SUL13: Odpowiedź /szkp/uzytkownicy/ zawiera username 'inny_uzytkownik_int'."""
        self.client.force_login(self.superuser)
        response = self.client.get(UZYTKOWNICY)
        self.assertContains(response, 'inny_uzytkownik_int')


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL14–TI-SUL16: user_toggle_active — POST endpoint
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserUserToggleActiveTest(_SuperuserListsBase):
    """TI-SUL14–TI-SUL16: POST /szkp/uzytkownicy/<pk>/aktywuj/ — toggle is_active."""

    def setUp(self):
        self.target = User.objects.create_user(
            username='target_toggle_int', password='x', is_active=True,
        )

    def _toggle_url(self, pk):
        return f'/szkp/uzytkownicy/{pk}/aktywuj/'

    def test_ti_sul14_superuser_deaktywuje_aktywnego_uzytkownika(self):
        """TI-SUL14: POST na /aktywuj/ (aktywny user) → is_active=False + redirect 302."""
        self.client.force_login(self.superuser)
        response = self.client.post(self._toggle_url(self.target.pk))
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    def test_ti_sul15_superuser_aktywuje_nieaktywnego_uzytkownika(self):
        """TI-SUL15: POST na /aktywuj/ (nieaktywny user) → is_active=True + redirect 302."""
        self.target.is_active = False
        self.target.save()
        self.client.force_login(self.superuser)
        self.client.post(self._toggle_url(self.target.pk))
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_ti_sul16_staff_nie_moze_toggleowac(self):
        """TI-SUL16: POST na /aktywuj/ jako staff (non-superuser) → 403 Forbidden."""
        self.client.force_login(self.staff)
        response = self.client.post(self._toggle_url(self.target.pk))
        self.assertEqual(response.status_code, 403)


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL26–TI-SUL29: user_list — wyszukiwanie i sortowanie
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserUserListSearchSortViewTest(_SuperuserListsBase):
    """TI-SUL26–TI-SUL29: GET /szkp/uzytkownicy/ z parametrami ?q= i ?sort= dla superusera."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_a = User.objects.create_user(
            username='alfa_uzytkownik', email='alfa@test.pl', password='x',
        )
        cls.user_b = User.objects.create_user(
            username='zeta_uzytkownik', email='zeta@test.pl', password='x',
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_ti_sul26_wyszukiwanie_q_filtruje_queryset(self):
        """TI-SUL26: GET /uzytkownicy/?q=alfa → context['page_obj'] zawiera tylko alfa_uzytkownik.

        W RED: widok ignoruje GET['q'] → oba użytkownicy w kontekście.
        W GREEN: widok filtruje username__icontains='alfa' → tylko alfa_uzytkownik.
        """
        response = self.client.get(UZYTKOWNICY + '?q=alfa')
        self.assertEqual(response.status_code, 200)
        usernames = [u.username for u in response.context['page_obj']]
        self.assertIn(
            'alfa_uzytkownik', usernames,
            f"'alfa_uzytkownik' brak w ?q=alfa. Użytkownicy: {usernames}",
        )
        self.assertNotIn(
            'zeta_uzytkownik', usernames,
            f"'zeta_uzytkownik' nadal widoczny po ?q=alfa — filtr nie działa. Użytkownicy: {usernames}",
        )

    def test_ti_sul27_sortowanie_username_asc(self):
        """TI-SUL27: GET /uzytkownicy/?sort=username&dir=asc → alfa przed zeta.

        W RED: widok ignoruje parametry sortowania → kolejność nieokreślona.
        W GREEN: widok stosuje order_by('username') → alfabetycznie rosnąco.
        """
        response = self.client.get(UZYTKOWNICY + '?sort=username&dir=asc')
        self.assertEqual(response.status_code, 200)
        usernames = [u.username for u in response.context['page_obj']]
        alfa_idx = next((i for i, n in enumerate(usernames) if 'alfa' in n), None)
        zeta_idx = next((i for i, n in enumerate(usernames) if 'zeta' in n), None)
        self.assertIsNotNone(alfa_idx, f"'alfa_uzytkownik' nie znaleziony. Użytkownicy: {usernames}")
        self.assertIsNotNone(zeta_idx, f"'zeta_uzytkownik' nie znaleziony. Użytkownicy: {usernames}")
        self.assertLess(
            alfa_idx, zeta_idx,
            f'?sort=username&dir=asc: alfa (idx {alfa_idx}) powinno być przed zeta (idx {zeta_idx})',
        )

    def test_ti_sul28_sortowanie_username_desc(self):
        """TI-SUL28: GET /uzytkownicy/?sort=username&dir=desc → zeta przed alfa.

        W RED: widok ignoruje parametry sortowania → kolejność nieokreślona.
        W GREEN: widok stosuje order_by('-username') → alfabetycznie malejąco.
        """
        response = self.client.get(UZYTKOWNICY + '?sort=username&dir=desc')
        self.assertEqual(response.status_code, 200)
        usernames = [u.username for u in response.context['page_obj']]
        alfa_idx = next((i for i, n in enumerate(usernames) if 'alfa' in n), None)
        zeta_idx = next((i for i, n in enumerate(usernames) if 'zeta' in n), None)
        self.assertIsNotNone(alfa_idx, f"'alfa_uzytkownik' nie znaleziony. Użytkownicy: {usernames}")
        self.assertIsNotNone(zeta_idx, f"'zeta_uzytkownik' nie znaleziony. Użytkownicy: {usernames}")
        self.assertLess(
            zeta_idx, alfa_idx,
            f'?sort=username&dir=desc: zeta (idx {zeta_idx}) powinno być przed alfa (idx {alfa_idx})',
        )

    def test_ti_sul29_kontekst_zawiera_q_sort_direction(self):
        """TI-SUL29: GET /uzytkownicy/?q=x&sort=username&dir=asc → context ma q, sort, direction.

        W RED: widok nie przekazuje tych kluczy → KeyError lub brak kluczy.
        W GREEN: widok dodaje q, sort, direction do context.
        """
        response = self.client.get(UZYTKOWNICY + '?q=alfa&sort=username&dir=asc')
        self.assertEqual(response.status_code, 200)
        for key in ('q', 'sort', 'direction'):
            self.assertIn(
                key, response.context,
                f"context['{key}'] brak — widok nie przekazuje parametru do szablonu",
            )
        self.assertEqual(response.context['q'], 'alfa')
        self.assertEqual(response.context['sort'], 'username')
        self.assertEqual(response.context['direction'], 'asc')


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL30–TI-SUL35: user_form (tworzenie) — dostęp i zachowanie POST
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserUserFormCreateViewTest(_SuperuserListsBase):
    """TI-SUL30–TI-SUL35: GET/POST /szkp/uzytkownicy/nowy/ — tworzenie użytkownika."""

    def _url(self):
        return reverse('szkp:user_form_create')

    def test_ti_sul30_superuser_dostaje_200_i_szablon(self):
        """TI-SUL30: GET /nowy/ jako superuser → 200 + user_form_su.html.

        W RED: URL nie istnieje → NoReverseMatch lub 404.
        W GREEN: URL zarejestrowany, widok zwraca formularz.
        """
        self.client.force_login(self.superuser)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'szkp/user_form_su.html')

    def test_ti_sul31_staff_dostaje_403(self):
        """TI-SUL31: GET /nowy/ jako staff (non-superuser) → 403 Forbidden.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: URL istnieje, widok sprawdza is_superuser.
        """
        self.client.force_login(self.staff)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 403)

    def test_ti_sul32_niezalogowany_dostaje_302_na_login(self):
        """TI-SUL32: GET /nowy/ bez logowania → 302 redirect na stronę logowania.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: @login_required przekierowuje na /accounts/login/.
        """
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_ti_sul33_post_poprawne_dane_tworzy_uzytkownika(self):
        """TI-SUL33: POST /nowy/ z poprawnymi danymi → 302 redirect + User w bazie.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: widok tworzy User i przekierowuje na listę.
        """
        self.client.force_login(self.superuser)
        response = self.client.post(self._url(), {
            'username': 'nowy_ti_sul33',
            'email': 'ti33@test.pl',
            'password': 'BezpieczneHaslo1!',
            'password_confirm': 'BezpieczneHaslo1!',
            'is_staff': '',
            'is_active': 'on',
        })
        self.assertEqual(
            response.status_code, 302,
            f'POST /nowy/ nie zwrócił redirect. Status: {response.status_code}',
        )
        self.assertTrue(
            User.objects.filter(username='nowy_ti_sul33').exists(),
            'Użytkownik "nowy_ti_sul33" nie istnieje w bazie po POST — widok nie zapisuje',
        )

    def test_ti_sul34_post_niezgodne_hasla_nie_tworzy_uzytkownika(self):
        """TI-SUL34: POST /nowy/ z niezgodnymi hasłami → 200 (formularz z błędami), brak nowego User.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: walidacja odrzuca formularz, User nie jest tworzony.
        """
        self.client.force_login(self.superuser)
        response = self.client.post(self._url(), {
            'username': 'nowy_ti_sul34',
            'password': 'HasloA1!',
            'password_confirm': 'HasloB2!',
        })
        self.assertEqual(
            response.status_code, 200,
            f'POST z niezgodnymi hasłami powinien zwrócić 200 (formularz). Status: {response.status_code}',
        )
        self.assertFalse(
            User.objects.filter(username='nowy_ti_sul34').exists(),
            'Użytkownik "nowy_ti_sul34" zapisany mimo niezgodnych haseł — brak walidacji',
        )

    def test_ti_sul35_post_zduplikowana_nazwa_nie_tworzy_uzytkownika(self):
        """TI-SUL35: POST /nowy/ z już istniejącym username → 200 (błąd), brak duplikatu.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: walidacja unikalności username odrzuca formularz.
        """
        User.objects.create_user(username='zajeta_nazwa_ti35', password='x')
        self.client.force_login(self.superuser)
        response = self.client.post(self._url(), {
            'username': 'zajeta_nazwa_ti35',
            'password': 'BezpieczneHaslo1!',
            'password_confirm': 'BezpieczneHaslo1!',
        })
        self.assertEqual(
            response.status_code, 200,
            f'POST ze zduplikowanym username powinien zwrócić 200 (błąd). Status: {response.status_code}',
        )
        self.assertEqual(
            User.objects.filter(username='zajeta_nazwa_ti35').count(), 1,
            'Duplikat użytkownika "zajeta_nazwa_ti35" zapisany — brak walidacji unikalności',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TI-SUL36–TI-SUL40: user_form (edycja) — dostęp i zachowanie POST
# ═══════════════════════════════════════════════════════════════════════════

@tag('integration')
class SuperuserUserFormEditViewTest(_SuperuserListsBase):
    """TI-SUL36–TI-SUL40: GET/POST /szkp/uzytkownicy/<pk>/edytuj/ — edycja użytkownika."""

    def setUp(self):
        self.target = User.objects.create_user(
            username='edytowany_ti_edit', email='stary_ti@test.pl',
            password='StarePHaslo1!', is_staff=False,
        )
        self._original_password = self.target.password

    def _url(self, pk=None):
        return reverse('szkp:user_form_edit', kwargs={'pk': pk or self.target.pk})

    def test_ti_sul36_superuser_dostaje_200_i_szablon(self):
        """TI-SUL36: GET /edytuj/ jako superuser → 200 + user_form_su.html.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: URL zarejestrowany, widok zwraca formularz edycji.
        """
        self.client.force_login(self.superuser)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'szkp/user_form_su.html')

    def test_ti_sul37_kontekst_zawiera_dane_uzytkownika(self):
        """TI-SUL37: GET /edytuj/ → context['form_data']['email'] == 'stary_ti@test.pl'.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: widok wczytuje dane User i przekazuje jako form_data.
        """
        self.client.force_login(self.superuser)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 'stary_ti@test.pl',
            msg_prefix='Email użytkownika nie widoczny w formularzu edycji — form_data nie wczytane',
        )

    def test_ti_sul38_post_zmiana_email_aktualizuje_baze(self):
        """TI-SUL38: POST /edytuj/ z nowym emailem → 302 redirect + zaktualizowany email w bazie.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: widok aktualizuje User.email i przekierowuje.
        """
        self.client.force_login(self.superuser)
        response = self.client.post(self._url(), {
            'username': self.target.username,
            'email': 'nowy_ti38@test.pl',
            'password': '',
            'password_confirm': '',
            'is_active': 'on',
        })
        self.assertEqual(
            response.status_code, 302,
            f'POST /edytuj/ nie zwrócił redirect. Status: {response.status_code}',
        )
        self.target.refresh_from_db()
        self.assertEqual(
            self.target.email, 'nowy_ti38@test.pl',
            f'Email nie zaktualizowany. Aktualny: {self.target.email}',
        )

    def test_ti_sul39_post_puste_haslo_nie_zmienia_hasla(self):
        """TI-SUL39: POST /edytuj/ z pustymi polami hasła → hasło bez zmian w bazie.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: widok pomija set_password gdy password == ''.
        """
        self.client.force_login(self.superuser)
        self.client.post(self._url(), {
            'username': self.target.username,
            'email': self.target.email,
            'password': '',
            'password_confirm': '',
            'is_active': 'on',
        })
        self.target.refresh_from_db()
        self.assertEqual(
            self.target.password, self._original_password,
            'Hasło zostało zmienione mimo pustych pól password/password_confirm — brak ochrony hasła',
        )

    def test_ti_sul40_staff_bez_superuser_dostaje_403(self):
        """TI-SUL40: GET /edytuj/ jako staff (non-superuser) → 403 Forbidden.

        W RED: URL nie istnieje → NoReverseMatch.
        W GREEN: widok sprawdza is_superuser i rzuca PermissionDenied.
        """
        self.client.force_login(self.staff)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 403)
