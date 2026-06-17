import inspect
import importlib
import os

from django.apps import apps
from django.conf import settings
from django.test import SimpleTestCase, tag


@tag('unit')
class DashboardSuperuserImportsTest(SimpleTestCase):
    """TU-D01–TU-D03: moduł dashboard.py zawiera importy wymagane przez gałąź superusera."""

    def _source(self):
        module = importlib.import_module('szkp.views.dashboard')
        return inspect.getsource(module)

    def test_tu_d01_import_get_user_model(self):
        """TU-D01: dashboard.py importuje get_user_model."""
        self.assertIn('get_user_model', self._source())

    def test_tu_d02_import_session(self):
        """TU-D02: dashboard.py importuje Session (django.contrib.sessions)."""
        self.assertIn('Session', self._source())

    def test_tu_d03_import_task_priority(self):
        """TU-D03: dashboard.py importuje TaskPriority."""
        self.assertIn('TaskPriority', self._source())


@tag('unit')
class DashboardSuperuserTemplateFilesTest(SimpleTestCase):
    """TU-D04–TU-D07: wymagane pliki szablonów istnieją na dysku."""

    def test_tu_d04_szablon_dashboard_superuser_istnieje(self):
        """TU-D04: szkp/templates/szkp/dashboard_superuser.html istnieje na dysku."""
        app_path = apps.get_app_config('szkp').path
        path = os.path.join(app_path, 'templates', 'szkp', 'dashboard_superuser.html')
        self.assertTrue(os.path.exists(path), f'Brak pliku: {path}')

    def test_tu_d05_szablon_base_dash_istnieje(self):
        """TU-D05: templates/base_dash.html istnieje na dysku."""
        path = os.path.join(settings.BASE_DIR, 'templates', 'base_dash.html')
        self.assertTrue(os.path.exists(path), f'Brak pliku: {path}')

    def test_tu_d06_dashboard_superuser_rozszerza_base_dash(self):
        """TU-D06: dashboard_superuser.html zawiera extends 'base_dash.html'."""
        app_path = apps.get_app_config('szkp').path
        path = os.path.join(app_path, 'templates', 'szkp', 'dashboard_superuser.html')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('base_dash.html', content)

    def test_tu_d07_base_dash_zawiera_dash_sidebar(self):
        """TU-D07: base_dash.html zawiera element .dash-sidebar."""
        path = os.path.join(settings.BASE_DIR, 'templates', 'base_dash.html')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('dash-sidebar', content)


@tag('unit')
class DashboardSuperuserStyleTokensTest(SimpleTestCase):
    """TU-D08–TU-D11: static/style.css zawiera tokeny CSS layoutu administracyjnego."""

    def _css(self):
        path = os.path.join(settings.BASE_DIR, 'static', 'style.css')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_tu_d08_token_dash_ink(self):
        """TU-D08: style.css zawiera token --dash-ink."""
        self.assertIn('--dash-ink', self._css())

    def test_tu_d09_token_dash_sidebar_w(self):
        """TU-D09: style.css zawiera token --dash-sidebar-w."""
        self.assertIn('--dash-sidebar-w', self._css())

    def test_tu_d10_klasa_dash_sidebar(self):
        """TU-D10: style.css definiuje klasę .dash-sidebar."""
        self.assertIn('.dash-sidebar', self._css())

    def test_tu_d11_klasa_dash_metric_card(self):
        """TU-D11: style.css definiuje klasę .dash-metric-card."""
        self.assertIn('.dash-metric-card', self._css())
