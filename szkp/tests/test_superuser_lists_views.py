"""Testy integracyjne: Widoki list dla superusera (PSU-L01 – PSU-L05)."""
from django.contrib.auth.models import User
from django.test import TestCase, tag
from django.urls import reverse

from szkp.models import Lawyer

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
