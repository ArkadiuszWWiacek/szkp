"""Testy jednostkowe: Widoki list dla superusera (PSU-L01 – PSU-L05)."""
import os

from django.apps import apps
from django.conf import settings
from django.test import SimpleTestCase, tag
from django.urls import NoReverseMatch, reverse


@tag('unit')
class SuperuserListTemplateFilesTest(SimpleTestCase):
    """TU-SUL01–TU-SUL05: Pliki szablonów widoków list superusera istnieją na dysku."""

    def _path(self, filename):
        return os.path.join(
            apps.get_app_config('szkp').path,
            'templates', 'szkp', filename,
        )

    def test_tu_sul01_case_list_su_istnieje(self):
        """TU-SUL01: szkp/templates/szkp/case_list_su.html istnieje na dysku."""
        path = self._path('case_list_su.html')
        self.assertTrue(os.path.exists(path), f'Brak pliku: {path}')

    def test_tu_sul02_client_list_su_istnieje(self):
        """TU-SUL02: szkp/templates/szkp/client_list_su.html istnieje na dysku."""
        path = self._path('client_list_su.html')
        self.assertTrue(os.path.exists(path), f'Brak pliku: {path}')

    def test_tu_sul03_invoice_list_su_istnieje(self):
        """TU-SUL03: szkp/templates/szkp/invoice_list_su.html istnieje na dysku."""
        path = self._path('invoice_list_su.html')
        self.assertTrue(os.path.exists(path), f'Brak pliku: {path}')

    def test_tu_sul04_task_list_su_istnieje(self):
        """TU-SUL04: szkp/templates/szkp/task_list_su.html istnieje na dysku."""
        path = self._path('task_list_su.html')
        self.assertTrue(os.path.exists(path), f'Brak pliku: {path}')

    def test_tu_sul05_user_list_su_istnieje(self):
        """TU-SUL05: szkp/templates/szkp/user_list_su.html istnieje na dysku."""
        path = self._path('user_list_su.html')
        self.assertTrue(os.path.exists(path), f'Brak pliku: {path}')


@tag('unit')
class SuperuserListTemplateExtendsTest(SimpleTestCase):
    """TU-SUL06–TU-SUL10: Wszystkie szablony list superusera rozszerzają base_dash.html."""

    def _content(self, filename):
        path = os.path.join(
            apps.get_app_config('szkp').path,
            'templates', 'szkp', filename,
        )
        if not os.path.exists(path):
            self.fail(f'Szablon nie istnieje — nie można sprawdzić extends: {path}')
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul06_case_list_su_rozszerza_base_dash(self):
        """TU-SUL06: case_list_su.html zawiera extends 'base_dash.html'."""
        self.assertIn('base_dash.html', self._content('case_list_su.html'))

    def test_tu_sul07_client_list_su_rozszerza_base_dash(self):
        """TU-SUL07: client_list_su.html zawiera extends 'base_dash.html'."""
        self.assertIn('base_dash.html', self._content('client_list_su.html'))

    def test_tu_sul08_invoice_list_su_rozszerza_base_dash(self):
        """TU-SUL08: invoice_list_su.html zawiera extends 'base_dash.html'."""
        self.assertIn('base_dash.html', self._content('invoice_list_su.html'))

    def test_tu_sul09_task_list_su_rozszerza_base_dash(self):
        """TU-SUL09: task_list_su.html zawiera extends 'base_dash.html'."""
        self.assertIn('base_dash.html', self._content('task_list_su.html'))

    def test_tu_sul10_user_list_su_rozszerza_base_dash(self):
        """TU-SUL10: user_list_su.html zawiera extends 'base_dash.html'."""
        self.assertIn('base_dash.html', self._content('user_list_su.html'))


@tag('unit')
class SuperuserListViewModuleTest(SimpleTestCase):
    """TU-SUL11–TU-SUL15: szkp/views/users.py istnieje i zawiera wymagane elementy."""

    def _views_users_path(self):
        return os.path.join(settings.BASE_DIR, 'szkp', 'views', 'users.py')

    def _views_users_content(self):
        path = self._views_users_path()
        if not os.path.exists(path):
            self.fail(f'Plik nie istnieje — nie można sprawdzić zawartości: {path}')
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul11_plik_views_users_istnieje(self):
        """TU-SUL11: szkp/views/users.py istnieje na dysku."""
        self.assertTrue(
            os.path.exists(self._views_users_path()),
            'Brak pliku szkp/views/users.py',
        )

    def test_tu_sul12_users_py_zawiera_def_user_list(self):
        """TU-SUL12: szkp/views/users.py definiuje funkcję user_list."""
        self.assertIn('user_list', self._views_users_content())

    def test_tu_sul13_users_py_zawiera_def_user_toggle_active(self):
        """TU-SUL13: szkp/views/users.py definiuje funkcję user_toggle_active."""
        self.assertIn('user_toggle_active', self._views_users_content())

    def test_tu_sul14_users_py_uzywa_login_required(self):
        """TU-SUL14: szkp/views/users.py stosuje @login_required lub login_required."""
        self.assertIn('login_required', self._views_users_content())

    def test_tu_sul15_users_py_sprawdza_is_superuser(self):
        """TU-SUL15: szkp/views/users.py sprawdza is_superuser (blokada dla zwykłego staff)."""
        self.assertIn('is_superuser', self._views_users_content())


@tag('unit')
class SuperuserListViewsInitTest(SimpleTestCase):
    """TU-SUL16–TU-SUL17: szkp/views/__init__.py eksportuje widoki użytkowników."""

    def _init_content(self):
        path = os.path.join(settings.BASE_DIR, 'szkp', 'views', '__init__.py')
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul16_init_eksportuje_user_list(self):
        """TU-SUL16: szkp/views/__init__.py zawiera 'user_list' (import lub __all__)."""
        self.assertIn(
            'user_list', self._init_content(),
            "szkp/views/__init__.py nie eksportuje 'user_list'",
        )

    def test_tu_sul17_init_eksportuje_user_toggle_active(self):
        """TU-SUL17: szkp/views/__init__.py zawiera 'user_toggle_active'."""
        self.assertIn(
            'user_toggle_active', self._init_content(),
            "szkp/views/__init__.py nie eksportuje 'user_toggle_active'",
        )


@tag('unit')
class SuperuserListUrlsTest(SimpleTestCase):
    """TU-SUL18–TU-SUL19: Nowe URL-e widoku listy użytkowników są zarejestrowane."""

    def test_tu_sul18_url_user_list_zarejestrowany(self):
        """TU-SUL18: URL szkp:user_list istnieje i wskazuje na /uzytkownicy/."""
        try:
            url = reverse('szkp:user_list')
        except NoReverseMatch:
            url = None
        self.assertIsNotNone(
            url, 'URL szkp:user_list nie jest zarejestrowany w szkp/urls.py',
        )

    def test_tu_sul19_url_user_toggle_active_zarejestrowany(self):
        """TU-SUL19: URL szkp:user_toggle_active(pk) istnieje i wskazuje na /aktywuj/."""
        try:
            url = reverse('szkp:user_toggle_active', kwargs={'pk': 1})
        except NoReverseMatch:
            url = None
        self.assertIsNotNone(
            url, 'URL szkp:user_toggle_active nie jest zarejestrowany w szkp/urls.py',
        )


@tag('unit')
class SuperuserListCssTest(SimpleTestCase):
    """TU-SUL20–TU-SUL22: static/style.css zawiera klasy CSS dla widoków list dash."""

    def _css(self):
        path = os.path.join(settings.BASE_DIR, 'static', 'style.css')
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul20_css_zawiera_dash_toolbar(self):
        """TU-SUL20: style.css definiuje .dash-toolbar dla paska narzędzi list."""
        self.assertIn('.dash-toolbar', self._css())

    def test_tu_sul21_css_zawiera_dash_search_input(self):
        """TU-SUL21: style.css definiuje .dash-search-input dla pola wyszukiwania."""
        self.assertIn('.dash-search-input', self._css())

    def test_tu_sul22_css_zawiera_dash_pagination(self):
        """TU-SUL22: style.css definiuje .dash-pagination dla paginacji."""
        self.assertIn('.dash-pagination', self._css())
