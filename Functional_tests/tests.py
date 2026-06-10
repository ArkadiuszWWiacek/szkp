from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import os


class NewVisitorTest(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["MOZ_DISABLE_CONTENT_SANDBOX"] = "1"

        super().setUpClass()
        cls.service = Service(
            executable_path="/usr/local/bin/geckodriver",
            log_output="/tmp/geckodriver.log",
        )
        cls.options = Options()
        cls.options.binary_location = "/lib/firefox-esr/firefox-esr"
        cls.options.add_argument("--headless")
        cls.options.add_argument("--no-sandbox")
        cls.options.add_argument("--disable-dev-shm-usage")

        print("Starting Firefox...")
        cls.selenium = webdriver.Firefox(service=cls.service, options=cls.options)
        print("Firefox started!")

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_can_open_home_page(self):
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
