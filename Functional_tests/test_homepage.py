from django.test import tag

from .base import SzkpSeleniumTestCase


@tag('functional')
class NewVisitorTest(SzkpSeleniumTestCase):
    """Scenariusz pierwszej wizyty — weryfikacja tytułu strony i linku nawigacyjnego SZKP."""

    @tag('smoke')
    def test_can_open_home_page(self):
        """Strona główna wyświetla tytuł 'System Zarządzania Kancelarią Prawną', a link nawigacyjny 'SZKP' przenosi na /szkp/."""
        # Edyta dowiedziała się o nowej, wspaniałej aplikacji do prowadzenia kancelarii prawnej.
        # Postanowiła więc przejść na stronę główną tej aplikacji.
        self.selenium.get(self.live_server_url)

        # Zwróciła uwagę, że tytuł strony i nagłówek zawierają słowo "Prawną".
        self.assertIn("System Zarządzania Kancelarią Prawną", self.selenium.title)

        # Edyta zauważyła, że na stronie jest napis "SZKP" i kliknęła w ten napis.
        header = self.selenium.find_element("css selector", ".navbar-brand")
        self.assertEqual(header.text, "SZKP")
        header.click()
        self.assertEqual(self.selenium.current_url, self.live_server_url + "/szkp/")
