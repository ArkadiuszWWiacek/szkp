import os

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SzkpSeleniumTestCase(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["MOZ_DISABLE_CONTENT_SANDBOX"] = "1"
        super().setUpClass()
        service = Service(
            executable_path="/usr/local/bin/geckodriver",
            log_output="/tmp/geckodriver.log",
        )
        options = Options()
        options.binary_location = "/lib/firefox-esr/firefox-esr"
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.selenium = webdriver.Firefox(service=service, options=options)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def _zaloguj(self, username="testuser", password="testpass123"):
        self.selenium.get(self.live_server_url + "/accounts/login/")
        self.selenium.find_element("id", "id_username").send_keys(username)
        self.selenium.find_element("id", "id_password").send_keys(password)
        self.selenium.find_element("css selector", "button[type='submit']").click()

    def _wyloguj(self):
        self.selenium.find_element("css selector", ".szkp-user-badge").click()
        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.dropdown-item"))
        ).click()
