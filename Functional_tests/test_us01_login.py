from django.contrib.auth.models import User
from django.test import tag

from .base import SzkpSeleniumTestCase


@tag('functional')
class US01LoginLogoutTest(SzkpSeleniumTestCase):
    """US-01: Logowanie i wylogowanie."""

    def setUp(self):
        self.selenium.get(self.live_server_url)
        self.selenium.delete_all_cookies()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            first_name="Jan",
            last_name="Kowalski",
        )

    def test_formularz_zawiera_token_csrf(self):
        """Formularz logowania zawiera ukryte pole csrfmiddlewaretoken."""
        self.selenium.get(self.live_server_url + "/accounts/login/")
        csrf = self.selenium.find_element(
            "css selector", "input[name='csrfmiddlewaretoken']"
        )
        self.assertTrue(csrf.get_attribute("value"))

    def test_poprawne_logowanie_przekierowuje_na_pulpit(self):
        """Zalogowanie poprawnymi danymi przekierowuje na /szkp/pulpit/."""
        self._zaloguj()
        self.assertEqual(
            self.selenium.current_url, self.live_server_url + "/szkp/pulpit/"
        )
        self.assertIn("Pulpit", self.selenium.title)

    def test_bledne_dane_wyswietlaja_komunikat_bledu(self):
        """Błędne hasło wyświetla .alert-danger i pozostawia użytkownika na stronie logowania."""
        self._zaloguj(password="bledne_haslo")
        self.assertIn("/accounts/login/", self.selenium.current_url)
        error = self.selenium.find_element("css selector", ".alert-danger")
        self.assertIn("Nieprawidłowy login lub hasło", error.text)

    def test_wylogowanie_przekierowuje_na_strone_logowania(self):
        """Kliknięcie 'Wyloguj się' przenosi na stronę logowania."""
        self._zaloguj()
        self._wyloguj()
        self.assertIn("/accounts/login/", self.selenium.current_url)
        self.assertIn("Logowanie", self.selenium.title)

    def test_po_wylogowaniu_chroniony_widok_wymaga_zalogowania(self):
        """Po wylogowaniu wejście na /szkp/pulpit/ przekierowuje z powrotem na login."""
        self._zaloguj()
        self._wyloguj()
        self.selenium.get(self.live_server_url + "/szkp/pulpit/")
        self.assertIn("/accounts/login/", self.selenium.current_url)
