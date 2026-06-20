"""Testy funkcjonalne: Formularze SU — TC-SU-F01 – TC-SU-F24.

Weryfikują, że superużytkownik widzi formularze w stylu base_dash.html
(pasek boczny .dash-sidebar) i ma dostęp do dodatkowych pól modeli,
których zwykły staff użytkownik nie widzi.
"""
from django.contrib.auth.models import User
from django.test import tag
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from Functional_tests.base import SzkpSeleniumTestCase
from szkp.models import (
    Case, CaseType,
    CaseLawyer, CaseLawyerRole,
    Client, ClientType,
    Lawyer,
    Task, TaskStatus,
)
from szkp.tests.utils import make_due


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-F01 – TC-SU-F05: case_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCaseFormTest(SzkpSeleniumTestCase):
    """SU na formularzu sprawy widzi base_dash layout i pola opened_at / closed_at."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_caseform', password='supass123',
            is_staff=True, is_superuser=True,
        )
        self.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Test', last_name='Klient', pesel='80010112345',
        )

    @tag('smoke')
    def test_tc_su_f01_su_case_form_wyswietla_sidebar(self):
        """TC-SU-F01: SU na /szkp/sprawy/nowy/ widzi .dash-sidebar (base_dash.html)."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — SU na case_form widzi szablon Bootstrap zamiast base_dash.html',
        )

    def test_tc_su_f02_su_case_form_zawiera_pole_opened_at(self):
        """TC-SU-F02: SU widzi pole opened_at w formularzu sprawy."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        field = self.selenium.find_elements(By.NAME, 'opened_at')
        self.assertTrue(
            len(field) > 0,
            'Brak pola [name="opened_at"] — CaseFormSU nie zawiera tego pola',
        )

    def test_tc_su_f03_su_case_form_zawiera_pole_closed_at(self):
        """TC-SU-F03: SU widzi pole closed_at w formularzu sprawy."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        field = self.selenium.find_elements(By.NAME, 'closed_at')
        self.assertTrue(
            len(field) > 0,
            'Brak pola [name="closed_at"] — CaseFormSU nie zawiera tego pola',
        )

    def test_tc_su_f04_niesu_case_form_nie_wyswietla_sidebar(self):
        """TC-SU-F04: Staff (nie SU) na /szkp/sprawy/nowy/ NIE widzi .dash-sidebar."""
        staff = User.objects.create_user(
            username='staff_caseform', password='staffpass123', is_staff=True,
        )
        Lawyer.objects.create(
            user=staff, first_name='Jan', last_name='Prawnik', bar_number='TST/SCF/001',
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            '.dash-sidebar obecny dla nie-SU na case_form — błąd regresji',
        )

    def test_tc_su_f05_niesu_case_form_nie_zawiera_opened_at(self):
        """TC-SU-F05: Staff (nie SU) na /szkp/sprawy/nowy/ NIE widzi pola opened_at."""
        staff = User.objects.create_user(
            username='staff_caseform2', password='staffpass123', is_staff=True,
        )
        Lawyer.objects.create(
            user=staff, first_name='Piotr', last_name='Prawnik2', bar_number='TST/SCF/002',
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        self.selenium.get(self.live_server_url + '/szkp/sprawy/nowy/')
        field = self.selenium.find_elements(By.NAME, 'opened_at')
        self.assertEqual(
            len(field), 0,
            'Pole [name="opened_at"] widoczne dla nie-SU — błąd izolacji formularzy SU',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-F06 – TC-SU-F09: client_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUClientFormTest(SzkpSeleniumTestCase):
    """SU na formularzu klienta widzi base_dash layout, pole country; może zapisać z niestandardowym krajem."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_clientform', password='supass123',
            is_staff=True, is_superuser=True,
        )

    @tag('smoke')
    def test_tc_su_f06_su_client_form_wyswietla_sidebar(self):
        """TC-SU-F06: SU na /szkp/klienci/nowy/ widzi .dash-sidebar (base_dash.html)."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/klienci/nowy/')
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — SU na client_form widzi szablon Bootstrap zamiast base_dash.html',
        )

    def test_tc_su_f07_su_client_form_zawiera_pole_country(self):
        """TC-SU-F07: SU widzi pole country w formularzu klienta."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/klienci/nowy/')
        field = self.selenium.find_elements(By.NAME, 'country')
        self.assertTrue(
            len(field) > 0,
            'Brak pola [name="country"] — ClientFormSU nie zawiera tego pola',
        )

    def test_tc_su_f08_niesu_client_form_nie_wyswietla_sidebar(self):
        """TC-SU-F08: Staff (nie SU) na /szkp/klienci/nowy/ NIE widzi .dash-sidebar."""
        staff = User.objects.create_user(
            username='staff_clientform', password='staffpass123', is_staff=True,
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        self.selenium.get(self.live_server_url + '/szkp/klienci/nowy/')
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            '.dash-sidebar obecny dla nie-SU na client_form — błąd regresji',
        )

    def test_tc_su_f09_su_zapisuje_klienta_z_custom_country(self):
        """TC-SU-F09: SU zapisuje klienta z country='Niemcy' — pole utrwalone w DB."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/klienci/nowy/')

        country_fields = self.selenium.find_elements(By.NAME, 'country')
        self.assertTrue(
            len(country_fields) > 0,
            'Brak pola [name="country"] — ClientFormSU nie zawiera tego pola (RED)',
        )

        self.selenium.find_element(
            By.CSS_SELECTOR, 'input[type="radio"][name="type"][value="osobafizyczna"]'
        ).click()
        self.selenium.find_element(By.NAME, 'first_name').send_keys('Hans')
        self.selenium.find_element(By.NAME, 'last_name').send_keys('Muller')
        self.selenium.find_element(By.NAME, 'pesel').send_keys('90010112349')
        country_fields[0].clear()
        country_fields[0].send_keys('Niemcy')
        self.selenium.find_element(By.CSS_SELECTOR, '[type="submit"]').click()

        klient = Client.objects.filter(last_name='Muller').first()
        self.assertIsNotNone(klient, 'Klient nie został zapisany — formularz SU nie przetworzył POST')
        self.assertEqual(
            klient.country, 'Niemcy',
            f'Pole country zawiera "{klient.country if klient else "?"}" zamiast "Niemcy"',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-F10 – TC-SU-F13: court_hearing_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCourtHearingFormTest(SzkpSeleniumTestCase):
    """SU na formularzu terminu widzi base_dash layout i pola responsible_lawyer / reminder_sent_at."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_hearingform', password='supass123',
            is_staff=True, is_superuser=True,
        )
        Lawyer.objects.create(
            user=self.superuser, first_name='Su', last_name='Admin', bar_number='TST/SH/001',
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Termin', last_name='Klient', pesel='80010112346',
        )
        self.case = Case.objects.create(
            client=klient, case_number='TST/HEAR/001',
            title='Sprawa terminow SU', case_type=CaseType.CYWILNA,
        )

    @tag('smoke')
    def test_tc_su_f10_su_hearing_form_wyswietla_sidebar(self):
        """TC-SU-F10: SU na formularzu terminu widzi .dash-sidebar (base_dash.html)."""
        self._zaloguj_przez_orm(self.superuser)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/terminy/nowy/'
        self.selenium.get(url)
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — SU na court_hearing_form widzi stary szablon Bootstrap',
        )

    def test_tc_su_f11_su_hearing_form_zawiera_pole_responsible_lawyer(self):
        """TC-SU-F11: SU widzi pole responsible_lawyer w formularzu terminu."""
        self._zaloguj_przez_orm(self.superuser)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/terminy/nowy/'
        self.selenium.get(url)
        field = self.selenium.find_elements(By.NAME, 'responsible_lawyer')
        self.assertTrue(
            len(field) > 0,
            'Brak pola [name="responsible_lawyer"] — CourtHearingFormSU nie zawiera tego pola',
        )

    def test_tc_su_f12_su_hearing_form_zawiera_pole_reminder_sent_at(self):
        """TC-SU-F12: SU widzi pole reminder_sent_at w formularzu terminu."""
        self._zaloguj_przez_orm(self.superuser)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/terminy/nowy/'
        self.selenium.get(url)
        field = self.selenium.find_elements(By.NAME, 'reminder_sent_at')
        self.assertTrue(
            len(field) > 0,
            'Brak pola [name="reminder_sent_at"] — CourtHearingFormSU nie zawiera tego pola',
        )

    def test_tc_su_f13_niesu_hearing_form_nie_wyswietla_sidebar(self):
        """TC-SU-F13: Staff (nie SU) na court_hearing_form NIE widzi .dash-sidebar."""
        staff = User.objects.create_user(
            username='staff_hearingform', password='staffpass123', is_staff=True,
        )
        lawyer_staff = Lawyer.objects.create(
            user=staff, first_name='Jan', last_name='Pracownik', bar_number='TST/SH/002',
        )
        CaseLawyer.objects.create(
            case=self.case, lawyer=lawyer_staff, role=CaseLawyerRole.ASYSTENT,
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/terminy/nowy/'
        self.selenium.get(url)
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            '.dash-sidebar obecny dla nie-SU na court_hearing_form — błąd regresji',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-F14 – TC-SU-F16: invoice_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUInvoiceFormTest(SzkpSeleniumTestCase):
    """SU na formularzu faktury widzi base_dash layout i pole paid_at."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_invoiceform', password='supass123',
            is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Faktura', last_name='Klient', pesel='80010112347',
        )
        self.case = Case.objects.create(
            client=klient, case_number='TST/INV/001',
            title='Sprawa faktur SU', case_type=CaseType.CYWILNA,
        )

    @tag('smoke')
    def test_tc_su_f14_su_invoice_form_wyswietla_sidebar(self):
        """TC-SU-F14: SU na formularzu faktury widzi .dash-sidebar (base_dash.html)."""
        self._zaloguj_przez_orm(self.superuser)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/faktury/nowa/'
        self.selenium.get(url)
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — SU na invoice_form widzi stary szablon Bootstrap',
        )

    def test_tc_su_f15_su_invoice_form_zawiera_pole_paid_at(self):
        """TC-SU-F15: SU widzi pole paid_at w formularzu faktury."""
        self._zaloguj_przez_orm(self.superuser)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/faktury/nowa/'
        self.selenium.get(url)
        field = self.selenium.find_elements(By.NAME, 'paid_at')
        self.assertTrue(
            len(field) > 0,
            'Brak pola [name="paid_at"] — InvoiceFormSU nie zawiera tego pola',
        )

    def test_tc_su_f16_niesu_invoice_form_nie_wyswietla_sidebar(self):
        """TC-SU-F16: Staff (nie SU) na invoice_form NIE widzi .dash-sidebar."""
        staff = User.objects.create_user(
            username='staff_invoiceform', password='staffpass123', is_staff=True,
        )
        lawyer_staff = Lawyer.objects.create(
            user=staff, first_name='Jan', last_name='PracownikInv', bar_number='TST/INV/002',
        )
        CaseLawyer.objects.create(
            case=self.case, lawyer=lawyer_staff, role=CaseLawyerRole.ASYSTENT,
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/faktury/nowa/'
        self.selenium.get(url)
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            '.dash-sidebar obecny dla nie-SU na invoice_form — błąd regresji',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-F17 – TC-SU-F19: task_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUTaskFormTest(SzkpSeleniumTestCase):
    """SU na formularzu zadania widzi base_dash layout i pole created_by."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_taskform', password='supass123',
            is_staff=True, is_superuser=True,
        )
        Lawyer.objects.create(
            user=self.superuser, first_name='Su', last_name='Admin', bar_number='TST/TF/001',
        )

    @tag('smoke')
    def test_tc_su_f17_su_task_form_wyswietla_sidebar(self):
        """TC-SU-F17: SU na /szkp/zadania/nowe/ widzi .dash-sidebar (base_dash.html)."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/zadania/nowe/')
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — SU na task_form widzi stary szablon Bootstrap',
        )

    def test_tc_su_f18_su_task_form_zawiera_pole_created_by(self):
        """TC-SU-F18: SU widzi pole created_by w formularzu zadania."""
        self._zaloguj_przez_orm(self.superuser)
        self.selenium.get(self.live_server_url + '/szkp/zadania/nowe/')
        field = self.selenium.find_elements(By.NAME, 'created_by')
        self.assertTrue(
            len(field) > 0,
            'Brak pola [name="created_by"] — TaskFormSU nie zawiera tego pola',
        )

    def test_tc_su_f19_niesu_task_form_nie_wyswietla_sidebar(self):
        """TC-SU-F19: Staff (nie SU) na task_form NIE widzi .dash-sidebar."""
        staff = User.objects.create_user(
            username='staff_taskform', password='staffpass123', is_staff=True,
        )
        Lawyer.objects.create(
            user=staff, first_name='Jan', last_name='PracownikTask', bar_number='TST/TF/002',
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        self.selenium.get(self.live_server_url + '/szkp/zadania/nowe/')
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            '.dash-sidebar obecny dla nie-SU na task_form — błąd regresji',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-F20 – TC-SU-F22: case_lawyer_add
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUCaseLawyerFormTest(SzkpSeleniumTestCase):
    """SU na formularzu dodania prawnika widzi base_dash layout i opcję PROWADZĄCY w selekcie roli."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_clawyerform', password='supass123',
            is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Prawnicy', last_name='Klient', pesel='80010112348',
        )
        self.case = Case.objects.create(
            client=klient, case_number='TST/CL/001',
            title='Sprawa CaseLawyer SU', case_type=CaseType.CYWILNA,
        )
        self.other_lawyer = Lawyer.objects.create(
            first_name='Inny', last_name='Prawnik', bar_number='TST/CL/002',
        )

    @tag('smoke')
    def test_tc_su_f20_su_case_lawyer_add_wyswietla_sidebar(self):
        """TC-SU-F20: SU na formularzu dodania prawnika widzi .dash-sidebar (base_dash.html)."""
        self._zaloguj_przez_orm(self.superuser)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/prawnicy/dodaj/'
        self.selenium.get(url)
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — SU na case_lawyer_add widzi stary szablon Bootstrap',
        )

    def test_tc_su_f21_su_widzi_role_prowadzacy_w_selekcie(self):
        """TC-SU-F21: SU widzi opcję PROWADZĄCY w selekcie roli na formularzu dodania prawnika."""
        self._zaloguj_przez_orm(self.superuser)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/prawnicy/dodaj/'
        self.selenium.get(url)
        role_element = self.selenium.find_element(By.NAME, 'role')
        option_values = [
            opt.get_attribute('value') for opt in Select(role_element).options
        ]
        self.assertIn(
            CaseLawyerRole.PROWADZACY,
            option_values,
            f'Opcja PROWADZACY ({CaseLawyerRole.PROWADZACY}) niedostepna dla SU. '
            f'Dostepne: {option_values}',
        )

    def test_tc_su_f22_niesu_nie_widzi_roli_prowadzacy(self):
        """TC-SU-F22: Staff (nie SU) na case_lawyer_add NIE widzi opcji PROWADZĄCY."""
        staff = User.objects.create_user(
            username='staff_clawyerform', password='staffpass123', is_staff=True,
        )
        lead_lawyer = Lawyer.objects.create(
            user=staff, first_name='Jan', last_name='Prowadzacy', bar_number='TST/CL/003',
        )
        CaseLawyer.objects.create(
            case=self.case, lawyer=lead_lawyer, role=CaseLawyerRole.PROWADZACY,
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/prawnicy/dodaj/'
        self.selenium.get(url)
        role_element = self.selenium.find_element(By.NAME, 'role')
        option_values = [
            opt.get_attribute('value') for opt in Select(role_element).options
        ]
        self.assertNotIn(
            CaseLawyerRole.PROWADZACY,
            option_values,
            f'Opcja PROWADZACY dostepna dla nie-SU — blad izolacji formularzy',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-F23 – TC-SU-F24: document_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUDocumentFormTest(SzkpSeleniumTestCase):
    """SU na formularzu dokumentu widzi base_dash layout zamiast szablonu Bootstrap."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_docform', password='supass123',
            is_staff=True, is_superuser=True,
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Dokument', last_name='Klient', pesel='80010112349',
        )
        self.case = Case.objects.create(
            client=klient, case_number='TST/DOC/001',
            title='Sprawa dokumentow SU', case_type=CaseType.CYWILNA,
        )

    @tag('smoke')
    def test_tc_su_f23_su_document_form_wyswietla_sidebar(self):
        """TC-SU-F23: SU na formularzu dokumentu widzi .dash-sidebar (base_dash.html)."""
        self._zaloguj_przez_orm(self.superuser)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/dokumenty/nowy/'
        self.selenium.get(url)
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertTrue(
            len(sidebar) > 0,
            'Brak .dash-sidebar — SU na document_form widzi stary szablon Bootstrap',
        )

    def test_tc_su_f24_niesu_document_form_nie_wyswietla_sidebar(self):
        """TC-SU-F24: Staff (nie SU) na document_form NIE widzi .dash-sidebar."""
        staff = User.objects.create_user(
            username='staff_docform', password='staffpass123', is_staff=True,
        )
        lawyer_staff = Lawyer.objects.create(
            user=staff, first_name='Jan', last_name='PracownikDoc', bar_number='TST/DOC/002',
        )
        CaseLawyer.objects.create(
            case=self.case, lawyer=lawyer_staff, role=CaseLawyerRole.ASYSTENT,
        )
        self.selenium.delete_all_cookies()
        self._zaloguj_przez_orm(staff)
        url = self.live_server_url + f'/szkp/sprawy/{self.case.pk}/dokumenty/nowy/'
        self.selenium.get(url)
        sidebar = self.selenium.find_elements(By.CSS_SELECTOR, '.dash-sidebar')
        self.assertEqual(
            len(sidebar), 0,
            '.dash-sidebar obecny dla nie-SU na document_form — blad regresji',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TC-SU-F25 – TC-SU-F30: task_form hierarchia — ModelChoiceField + inline formset
# ═══════════════════════════════════════════════════════════════════════════

@tag('functional')
class SUTaskFormHierarchyTest(SzkpSeleniumTestCase):
    """TC-SU-F25–F30: SU na formularzu zadania widzi selekty z nazwami i może edytować podzadania inline."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.superuser = User.objects.create_user(
            username='su_taskhier', password='x',
            is_staff=True, is_superuser=True,
        )
        self.lawyer = Lawyer.objects.create(
            user=self.superuser,
            first_name='Su', last_name='Admin',
            bar_number='TST/TH/001',
        )
        self.lawyer2 = Lawyer.objects.create(
            first_name='Anna', last_name='Kowalska',
            bar_number='TST/TH/002',
        )
        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Jan', last_name='Klient',
            pesel='80010112348',
        )
        self.case = Case.objects.create(
            client=klient,
            case_number='TST/TH/2024/001',
            title='Sprawa hierarchii zadań',
            case_type=CaseType.CYWILNA,
        )
        self.parent_task = Task.objects.create(
            title='Zadanie nadrzędne hierarchii',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            due_date=make_due(7),
            status=TaskStatus.NOWE,
        )
        self.subtask = Task.objects.create(
            title='Podzadanie istniejące',
            assigned_lawyer=self.lawyer,
            created_by=self.lawyer,
            parent_task=self.parent_task,
            due_date=make_due(5),
            status=TaskStatus.NOWE,
        )
        self._zaloguj_przez_orm(self.superuser)

    def test_tc_su_f25_assigned_lawyer_jest_selectem_z_nazwiskami(self):
        """TC-SU-F25: SU na formularzu nowego zadania widzi <select> dla assigned_lawyer z nazwiskami prawników."""
        self.selenium.get(self.live_server_url + '/szkp/zadania/nowe/')
        selects = self.selenium.find_elements(By.CSS_SELECTOR, 'select[name="assigned_lawyer"]')
        self.assertGreater(
            len(selects), 0,
            'Brak <select name="assigned_lawyer"> — pole renderuje się jako <input type="number">; '
            'TaskFormSU.assigned_lawyer powinno być ModelChoiceField',
        )
        select = Select(selects[0])
        option_texts = [opt.text for opt in select.options]
        lawyer_name = f'{self.lawyer2.first_name} {self.lawyer2.last_name}'
        self.assertIn(
            lawyer_name, option_texts,
            f'Nazwisko {lawyer_name!r} nieobecne w opcjach selektu assigned_lawyer — '
            f'dostępne opcje: {option_texts}',
        )

    def test_tc_su_f26_case_jest_selectem_z_sygnaturami(self):
        """TC-SU-F26: SU na formularzu nowego zadania widzi <select> dla case z sygnaturami spraw."""
        self.selenium.get(self.live_server_url + '/szkp/zadania/nowe/')
        selects = self.selenium.find_elements(By.CSS_SELECTOR, 'select[name="case"]')
        self.assertGreater(
            len(selects), 0,
            'Brak <select name="case"> — pole renderuje się jako <input type="number">; '
            'TaskFormSU.case powinno być ModelChoiceField',
        )
        select = Select(selects[0])
        option_texts = [opt.text for opt in select.options]
        self.assertTrue(
            any(self.case.case_number in text for text in option_texts),
            f'Sygnatura {self.case.case_number!r} nieobecna w opcjach selektu case — '
            f'dostępne opcje: {option_texts}',
        )

    def test_tc_su_f27_su_task_form_edit_zawiera_sekcje_podzadan(self):
        """TC-SU-F27: SU edytując zadanie nadrzędne widzi sekcję 'Podzadania' z formularzem inline."""
        url = self.live_server_url + f'/szkp/zadania/{self.parent_task.pk}/edytuj/'
        self.selenium.get(url)
        podzadania_headers = self.selenium.find_elements(
            By.XPATH, '//*[contains(text(), "Podzadania")]',
        )
        self.assertGreater(
            len(podzadania_headers), 0,
            'Brak sekcji z tekstem "Podzadania" w formularzu edycji zadania nadrzędnego — '
            'inline formset podzadań nie jest renderowany',
        )

    def test_tc_su_f28_su_task_form_mozna_edytowac_podzadanie_inline(self):
        """TC-SU-F28: SU może zmienić tytuł istniejącego podzadania przez formularz inline."""
        url = self.live_server_url + f'/szkp/zadania/{self.parent_task.pk}/edytuj/'
        self.selenium.get(url)
        title_inputs = self.selenium.find_elements(
            By.CSS_SELECTOR, 'input[name^="task_set-"][name$="-title"]',
        )
        self.assertGreater(
            len(title_inputs), 0,
            'Brak pól title podzadania w formularzu (input[name^="task_set-"][name$="-title"]) — '
            'formset podzadań nie jest renderowany',
        )
        title_inputs[0].clear()
        title_inputs[0].send_keys('Zmieniony tytuł podzadania')
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        updated = Task.objects.get(pk=self.subtask.pk)
        self.assertEqual(
            updated.title, 'Zmieniony tytuł podzadania',
            f'Tytuł podzadania nie zmienił się po zapisie — aktualnie: {updated.title!r}',
        )

    def test_tc_su_f29_su_task_form_mozna_dodac_podzadanie_inline(self):
        """TC-SU-F29: SU może dodać nowe podzadanie przez extra-row w formularzu inline."""
        url = self.live_server_url + f'/szkp/zadania/{self.parent_task.pk}/edytuj/'
        self.selenium.get(url)
        title_inputs = self.selenium.find_elements(
            By.CSS_SELECTOR, 'input[name^="task_set-"][name$="-title"]',
        )
        self.assertGreater(
            len(title_inputs), 1,
            'Brak dodatkowego (extra) wiersza dla nowego podzadania — '
            'SubtaskInlineFormSet powinien mieć extra=1',
        )
        extra_title = title_inputs[-1]
        extra_title.send_keys('Nowe podzadanie przez formset')
        lawyer_selects = self.selenium.find_elements(
            By.CSS_SELECTOR, 'select[name^="task_set-"][name$="-assigned_lawyer"]',
        )
        lawyer_name = f'{self.lawyer.first_name} {self.lawyer.last_name}'
        Select(lawyer_selects[-1]).select_by_visible_text(lawyer_name)
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        new_task = Task.objects.filter(
            title='Nowe podzadanie przez formset',
            parent_task=self.parent_task,
        ).first()
        self.assertIsNotNone(
            new_task,
            'Nowe podzadanie nie zostało zapisane w bazie po wypełnieniu extra-row formset',
        )

    def test_tc_su_f30_su_task_form_mozna_usunac_podzadanie_inline(self):
        """TC-SU-F30: SU może usunąć podzadanie zaznaczając checkbox DELETE w formularzu inline."""
        url = self.live_server_url + f'/szkp/zadania/{self.parent_task.pk}/edytuj/'
        self.selenium.get(url)
        delete_checkboxes = self.selenium.find_elements(
            By.CSS_SELECTOR, 'input[name^="task_set-"][name$="-DELETE"]',
        )
        self.assertGreater(
            len(delete_checkboxes), 0,
            'Brak checkboxów DELETE w formularzu podzadań — '
            'SubtaskInlineFormSet powinien mieć can_delete=True',
        )
        delete_checkboxes[0].click()
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        still_exists = Task.objects.filter(pk=self.subtask.pk).exists()
        self.assertFalse(
            still_exists,
            f'Podzadanie pk={self.subtask.pk} nadal istnieje w bazie po zaznaczeniu DELETE i zapisaniu',
        )
