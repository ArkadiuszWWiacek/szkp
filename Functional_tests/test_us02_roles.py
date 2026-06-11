from django.contrib.auth.models import User
from django.test import tag

from .base import SzkpSeleniumTestCase


@tag('functional')
class US02RoleAccessTest(SzkpSeleniumTestCase):
    """US-02: Ochrona widoków i role."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username="prawnik_test",
            password="testpass123",
        )
        self.admin = User.objects.create_user(
            username="admin_test",
            password="adminpass123",
            is_staff=True,
            is_superuser=True,
        )

    def test_niezalogowany_nie_ma_dostepu_do_pulpitu(self):
        """Niezalogowany użytkownik próbujący wejść na pulpit trafia na stronę logowania."""
        self.selenium.get(self.live_server_url + "/szkp/pulpit/")
        self.assertIn("/accounts/login/", self.selenium.current_url)

    def test_niezalogowany_nie_ma_dostepu_do_listy_spraw(self):
        """Niezalogowany użytkownik próbujący wejść na listę spraw trafia na stronę logowania."""
        self.selenium.get(self.live_server_url + "/szkp/sprawy/")
        self.assertIn("/accounts/login/", self.selenium.current_url)

    def test_niezalogowany_nie_ma_dostepu_do_listy_klientow(self):
        """Niezalogowany użytkownik próbujący wejść na listę klientów trafia na stronę logowania."""
        self.selenium.get(self.live_server_url + "/szkp/klienci/")
        self.assertIn("/accounts/login/", self.selenium.current_url)

    def test_niezalogowany_nie_ma_dostepu_do_moich_zadan(self):
        """Widok zadań wymaga @login_required — brak dekoratora ujawnia ten test jako FAIL."""
        self.selenium.get(self.live_server_url + "/szkp/zadania/")
        self.assertIn("/accounts/login/", self.selenium.current_url)

    def test_redirect_zawiera_parametr_next(self):
        """Przekierowanie na stronę logowania zawiera parametr next= wskazujący żądany URL."""
        self.selenium.get(self.live_server_url + "/szkp/pulpit/")
        self.assertIn("next=", self.selenium.current_url)

    def test_zalogowany_uzytkownik_ma_dostep_do_widokow(self):
        """Zalogowany użytkownik (bez specjalnej roli) ma dostęp do chronionych widoków."""
        self._zaloguj_przez_orm(self.user)
        self.selenium.get(self.live_server_url + "/szkp/pulpit/")
        self.assertEqual(self.selenium.current_url, self.live_server_url + "/szkp/pulpit/")

    def test_panel_admina_niedostepny_dla_zwyklego_uzytkownika(self):
        """Użytkownik bez is_staff próbujący wejść do /admin/ trafia na stronę logowania admina."""
        self._zaloguj_przez_orm(self.user)
        self.selenium.get(self.live_server_url + "/admin/")
        self.assertIn("/admin/login/", self.selenium.current_url)

    def test_panel_admina_dostepny_dla_superuzytkownika(self):
        """Superuser ma bezpośredni dostęp do panelu /admin/."""
        self._zaloguj_przez_orm(self.admin)
        self.selenium.get(self.live_server_url + "/admin/")
        self.assertEqual(self.selenium.current_url, self.live_server_url + "/admin/")
