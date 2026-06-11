import os

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service


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
