from django.contrib.auth.models import User
from django.test import tag

from .base import SzkpSeleniumTestCase
from szkp.models import (
    Case, CaseType,
    CaseLawyer, CaseLawyerRole,
    Client, ClientType,
    Lawyer,
)


@tag('functional')
class US03CaseAccessTest(SzkpSeleniumTestCase):
    """US-03: Ograniczenie dostępu prawnika do własnych spraw."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()

        self.lawyer_a = Lawyer.objects.create(
            first_name='Andrzej', last_name='Adamski', bar_number='TST/A/001'
        )
        self.user_a = User.objects.create_user(
            username='andrzej_adamski', password='testpass123',
            first_name='Andrzej', last_name='Adamski',
        )
        self.lawyer_a.user = self.user_a
        self.lawyer_a.save()

        self.lawyer_b = Lawyer.objects.create(
            first_name='Barbara', last_name='Bogacka', bar_number='TST/B/001'
        )
        self.user_b = User.objects.create_user(
            username='barbara_bogacka', password='testpass123',
            first_name='Barbara', last_name='Bogacka',
        )
        self.lawyer_b.user = self.user_b
        self.lawyer_b.save()

        self.admin = User.objects.create_user(
            username='admin_test', password='adminpass123',
            is_staff=True, is_superuser=True,
        )

        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA, pesel='12345678901'
        )

        self.case_a = Case.objects.create(
            client=klient, case_number='TST-A-001',
            title='Sprawa Adwokata A', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=self.case_a, lawyer=self.lawyer_a, role=CaseLawyerRole.PROWADZACY
        )

        self.case_b = Case.objects.create(
            client=klient, case_number='TST-B-001',
            title='Sprawa Adwokata B', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=self.case_b, lawyer=self.lawyer_b, role=CaseLawyerRole.PROWADZACY
        )

    def test_prawnik_widzi_tylko_swoje_sprawy_na_liscie(self):
        """Zalogowany prawnik widzi na liście tylko sprawy, do których jest przypisany."""
        self._zaloguj(username='andrzej_adamski', password='testpass123')
        self.selenium.get(self.live_server_url + '/szkp/sprawy/')
        src = self.selenium.page_source
        self.assertIn(self.case_a.case_number, src)
        self.assertNotIn(self.case_b.case_number, src)

    def test_bezposredni_dostep_do_cudzej_sprawy_jest_blokowany(self):
        """Bezpośrednie wejście pod URL cudzej sprawy nie ujawnia jej treści."""
        self._zaloguj(username='andrzej_adamski', password='testpass123')
        self.selenium.get(self.live_server_url + f'/szkp/sprawy/{self.case_b.pk}/')
        self.assertNotIn(self.case_b.title, self.selenium.page_source)

    def test_administrator_widzi_wszystkie_sprawy_na_liscie(self):
        """Administrator (is_staff) widzi wszystkie sprawy bez ograniczeń."""
        self._zaloguj(username='admin_test', password='adminpass123')
        self.selenium.get(self.live_server_url + '/szkp/sprawy/')
        src = self.selenium.page_source
        self.assertIn(self.case_a.case_number, src)
        self.assertIn(self.case_b.case_number, src)

    def test_administrator_ma_dostep_do_szczegolu_kazdej_sprawy(self):
        """Administrator może wejść bezpośrednio na stronę dowolnej sprawy."""
        self._zaloguj(username='admin_test', password='adminpass123')
        detail_url = self.live_server_url + f'/szkp/sprawy/{self.case_b.pk}/'
        self.selenium.get(detail_url)
        self.assertEqual(self.selenium.current_url, detail_url)
        self.assertIn(self.case_b.title, self.selenium.page_source)
