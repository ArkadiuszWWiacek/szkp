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

    def test_tu_sul23_css_zawiera_task_row_subtask(self):
        """TU-SUL23: style.css definiuje .task-row--subtask dla wierszy podzadań."""
        self.assertIn(
            '.task-row--subtask', self._css(),
            'Brak reguły .task-row--subtask w static/style.css — '
            'wiersze podzadań nie mają dedykowanego stylu',
        )

    def test_tu_sul24_task_list_su_zawiera_class_task_row_parent(self):
        """TU-SUL24: task_list_su.html używa klasy CSS task-row--parent dla zadań nadrzędnych."""
        path = os.path.join(
            settings.BASE_DIR,
            'szkp', 'templates', 'szkp', 'task_list_su.html',
        )
        with open(path, encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            'task-row--parent', content,
            'Brak "task-row--parent" w task_list_su.html — '
            'wiersze nadrzędne nie mają klasy CSS do selektowania w testach',
        )

    def test_tu_sul25_task_list_su_zawiera_class_task_row_subtask(self):
        """TU-SUL25: task_list_su.html używa klasy CSS task-row--subtask dla podzadań."""
        path = os.path.join(
            settings.BASE_DIR,
            'szkp', 'templates', 'szkp', 'task_list_su.html',
        )
        with open(path, encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            'task-row--subtask', content,
            'Brak "task-row--subtask" w task_list_su.html — '
            'podzadania nie są renderowane z wymaganą klasą CSS',
        )

    def test_tu_sul26_task_list_su_iteruje_task_set(self):
        """TU-SUL26: task_list_su.html zawiera pętlę po task.task_set.all (podzadania)."""
        path = os.path.join(
            settings.BASE_DIR,
            'szkp', 'templates', 'szkp', 'task_list_su.html',
        )
        with open(path, encoding='utf-8') as f:
            content = f.read()
        self.assertIn(
            'task.task_set.all', content,
            'Brak "task.task_set.all" w task_list_su.html — '
            'szablon nie iteruje podzadań zadania nadrzędnego',
        )

    def _task_list_su_content(self):
        path = os.path.join(
            settings.BASE_DIR,
            'szkp', 'templates', 'szkp', 'task_list_su.html',
        )
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul27_task_list_su_laduje_szkp_tags(self):
        """TU-SUL27: task_list_su.html zawiera {% load szkp_tags %} (wymagane przez sort_th)."""
        self.assertIn(
            'load szkp_tags', self._task_list_su_content(),
            'Brak "{% load szkp_tags %}" w task_list_su.html — '
            'szablon nie może używać tagu sort_th bez załadowania biblioteki',
        )

    def test_tu_sul28_task_list_su_uzywa_sort_th_dla_assigned_lawyer(self):
        """TU-SUL28: task_list_su.html używa sort_th "assigned_lawyer" dla kolumny Prawnik."""
        self.assertIn(
            'sort_th "assigned_lawyer"', self._task_list_su_content(),
            'Brak sort_th "assigned_lawyer" w task_list_su.html — '
            'kolumna "Przypisany prawnik" nie jest sortowalna',
        )

    def test_tu_sul29_task_list_su_uzywa_sort_th_dla_due_date(self):
        """TU-SUL29: task_list_su.html używa sort_th "due_date" dla kolumny Termin."""
        self.assertIn(
            'sort_th "due_date"', self._task_list_su_content(),
            'Brak sort_th "due_date" w task_list_su.html — '
            'kolumna "Termin" nie jest sortowalna',
        )

    def test_tu_sul30_task_list_su_uzywa_sort_th_dla_status(self):
        """TU-SUL30: task_list_su.html używa sort_th "status" dla kolumny Status."""
        self.assertIn(
            'sort_th "status"', self._task_list_su_content(),
            'Brak sort_th "status" w task_list_su.html — '
            'kolumna "Status" nie jest sortowalna',
        )

    def test_tu_sul31_task_list_su_nie_uzywa_sort_th_dla_title(self):
        """TU-SUL31: task_list_su.html NIE używa sort_th "title" — Tytuł jest niesortowalne."""
        self.assertNotIn(
            'sort_th "title"', self._task_list_su_content(),
            'task_list_su.html zawiera sort_th "title" — zgodnie ze specyfikacją '
            'kolumna "Tytuł" nie powinna mieć linku sortowania',
        )

    def test_tu_sul32_task_list_su_ma_input_wyszukiwania(self):
        """TU-SUL32: task_list_su.html zawiera pole wyszukiwania name="q"."""
        self.assertIn(
            'name="q"', self._task_list_su_content(),
            'Brak name="q" w task_list_su.html — '
            'pole wyszukiwania słów kluczowych nie zostało dodane do szablonu',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SUL33–TU-SUL39: user_form_su.html — istnienie i struktura szablonu
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class SuperuserUserFormTemplateTest(SimpleTestCase):
    """TU-SUL33–TU-SUL39: Szablon user_form_su.html istnieje i zawiera wymagane pola."""

    def _path(self):
        return os.path.join(
            apps.get_app_config('szkp').path,
            'templates', 'szkp', 'user_form_su.html',
        )

    def _content(self):
        path = self._path()
        if not os.path.exists(path):
            self.fail(f'Brak pliku user_form_su.html — nie można sprawdzić zawartości: {path}')
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul33_user_form_su_istnieje(self):
        """TU-SUL33: szkp/templates/szkp/user_form_su.html istnieje na dysku."""
        self.assertTrue(os.path.exists(self._path()), f'Brak pliku: {self._path()}')

    def test_tu_sul34_user_form_su_rozszerza_base_dash(self):
        """TU-SUL34: user_form_su.html zawiera extends 'base_dash.html'."""
        self.assertIn('base_dash.html', self._content())

    def test_tu_sul35_user_form_su_ma_pole_username(self):
        """TU-SUL35: user_form_su.html zawiera pole name="username"."""
        self.assertIn(
            'name="username"', self._content(),
            'Brak name="username" w user_form_su.html — pole loginu niedostępne w formularzu',
        )

    def test_tu_sul36_user_form_su_ma_pole_email(self):
        """TU-SUL36: user_form_su.html zawiera pole name="email"."""
        self.assertIn(
            'name="email"', self._content(),
            'Brak name="email" w user_form_su.html — pole email niedostępne w formularzu',
        )

    def test_tu_sul37_user_form_su_ma_pole_password(self):
        """TU-SUL37: user_form_su.html zawiera pole name="password"."""
        self.assertIn(
            'name="password"', self._content(),
            'Brak name="password" w user_form_su.html — pole hasła niedostępne w formularzu',
        )

    def test_tu_sul38_user_form_su_ma_pole_password_confirm(self):
        """TU-SUL38: user_form_su.html zawiera pole name="password_confirm"."""
        self.assertIn(
            'name="password_confirm"', self._content(),
            'Brak name="password_confirm" w user_form_su.html — potwierdzenie hasła niedostępne',
        )

    def test_tu_sul39_user_form_su_ma_aktywny_nav_users(self):
        """TU-SUL39: user_form_su.html ustawia {% block nav_users %}dash-nav-item--active{% endblock nav_users %}."""
        content = self._content()
        self.assertIn(
            'nav_users', content,
            'Brak bloku nav_users w user_form_su.html — pozycja "Użytkownicy" nie będzie podświetlona',
        )
        self.assertIn(
            'dash-nav-item--active', content,
            'Brak dash-nav-item--active w bloku nav_users w user_form_su.html',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SUL40–TU-SUL41: base_dash.html — nawigacja do listy użytkowników
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class SuperuserNavigationBaseTemplateTest(SimpleTestCase):
    """TU-SUL40–TU-SUL41: base_dash.html zawiera blok i link nawigacyjny dla użytkowników."""

    def _base_dash_content(self):
        path = os.path.join(settings.BASE_DIR, 'templates', 'base_dash.html')
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul40_base_dash_zawiera_blok_nav_users(self):
        """TU-SUL40: base_dash.html definiuje {% block nav_users %}{% endblock nav_users %}."""
        self.assertIn(
            'nav_users', self._base_dash_content(),
            'Brak bloku nav_users w base_dash.html — szablony rozszerzające nie mogą ustawić '
            'aktywnego stanu dla pozycji Użytkownicy',
        )

    def test_tu_sul41_base_dash_zawiera_link_do_user_list(self):
        """TU-SUL41: base_dash.html zawiera link (href) do widoku listy użytkowników."""
        content = self._base_dash_content()
        has_link = (
            "url 'szkp:user_list'" in content
            or '/uzytkownicy/' in content
        )
        self.assertTrue(
            has_link,
            "base_dash.html nie zawiera linku do szkp:user_list — "
            "pozycja 'Użytkownicy' nie dodana do paska bocznego",
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SUL42–TU-SUL44: user_list_su.html — aktualizacje szablonu
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class SuperuserUserListSuTemplateUpdatesTest(SimpleTestCase):
    """TU-SUL42–TU-SUL44: user_list_su.html zaktualizowany o nav_users, wyszukiwanie, linki SZKP."""

    def _content(self):
        path = os.path.join(
            apps.get_app_config('szkp').path,
            'templates', 'szkp', 'user_list_su.html',
        )
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul42_user_list_su_ma_aktywny_nav_users(self):
        """TU-SUL42: user_list_su.html ustawia {% block nav_users %}dash-nav-item--active{% endblock nav_users %}."""
        content = self._content()
        self.assertIn(
            'nav_users', content,
            'Brak bloku nav_users w user_list_su.html — podświetlenie pozycji nawigacji niedostępne',
        )
        self.assertIn(
            'dash-nav-item--active', content,
            'Brak dash-nav-item--active w bloku nav_users w user_list_su.html',
        )

    def test_tu_sul43_user_list_su_ma_pole_wyszukiwania(self):
        """TU-SUL43: user_list_su.html zawiera <input name="q"> dla wyszukiwania użytkowników."""
        self.assertIn(
            'name="q"', self._content(),
            'Brak name="q" w user_list_su.html — wyszukiwanie użytkowników niedostępne',
        )

    def test_tu_sul44_user_list_su_link_edytuj_nie_prowadzi_do_admin(self):
        """TU-SUL44: user_list_su.html używa user_form_edit (nie admin:auth_user_change) dla edycji."""
        content = self._content()
        self.assertIn(
            'user_form_edit', content,
            'Brak user_form_edit w user_list_su.html — link "Edytuj" nadal przez /admin/',
        )
        self.assertNotIn(
            'admin:auth_user_change', content,
            'user_list_su.html nadal zawiera admin:auth_user_change — '
            'zarządzanie użytkownikami powinno być przez formularz SZKP',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SUL45: users.py — user_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class SuperuserUserFormViewModuleTest(SimpleTestCase):
    """TU-SUL45: szkp/views/users.py definiuje funkcję user_form."""

    def _content(self):
        path = os.path.join(settings.BASE_DIR, 'szkp', 'views', 'users.py')
        if not os.path.exists(path):
            self.fail('Brak szkp/views/users.py')
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul45_users_py_zawiera_def_user_form(self):
        """TU-SUL45: szkp/views/users.py definiuje funkcję user_form."""
        self.assertIn(
            'user_form', self._content(),
            'Brak def user_form w szkp/views/users.py — widok formularza niezaimplementowany',
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SUL46: __init__.py — eksport user_form
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class SuperuserUserFormInitExportTest(SimpleTestCase):
    """TU-SUL46: szkp/views/__init__.py eksportuje user_form."""

    def _content(self):
        path = os.path.join(settings.BASE_DIR, 'szkp', 'views', '__init__.py')
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_tu_sul46_init_eksportuje_user_form(self):
        """TU-SUL46: szkp/views/__init__.py zawiera 'user_form' w imporcie."""
        self.assertIn(
            'user_form', self._content(),
            "szkp/views/__init__.py nie eksportuje 'user_form'",
        )


# ═══════════════════════════════════════════════════════════════════════════
# TU-SUL47–TU-SUL48: URLs formularza użytkownika
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class SuperuserUserFormUrlsTest(SimpleTestCase):
    """TU-SUL47–TU-SUL48: URL-e user_form_create i user_form_edit są zarejestrowane."""

    def test_tu_sul47_url_user_form_create_zarejestrowany(self):
        """TU-SUL47: URL szkp:user_form_create istnieje i wskazuje na /uzytkownicy/nowy/."""
        try:
            url = reverse('szkp:user_form_create')
        except NoReverseMatch:
            url = None
        self.assertIsNotNone(
            url, 'URL szkp:user_form_create nie jest zarejestrowany w szkp/urls.py',
        )
        self.assertIn('/nowy/', url, f'URL user_form_create nie zawiera /nowy/: {url}')

    def test_tu_sul48_url_user_form_edit_zarejestrowany(self):
        """TU-SUL48: URL szkp:user_form_edit(pk=1) istnieje i wskazuje na /uzytkownicy/1/edytuj/."""
        try:
            url = reverse('szkp:user_form_edit', kwargs={'pk': 1})
        except NoReverseMatch:
            url = None
        self.assertIsNotNone(
            url, 'URL szkp:user_form_edit nie jest zarejestrowany w szkp/urls.py',
        )
        self.assertIn('/edytuj/', url, f'URL user_form_edit nie zawiera /edytuj/: {url}')


# ═══════════════════════════════════════════════════════════════════════════
# TU-SUL49–TU-SUL53: UserFormSU — walidacja formularza
# ═══════════════════════════════════════════════════════════════════════════

@tag('unit')
class SuperuserUserFormClassTest(SimpleTestCase):
    """TU-SUL49–TU-SUL53: UserFormSU waliduje dane wejściowe poprawnie."""

    def _get_form_class(self):
        try:
            from szkp.forms import UserFormSU
            return UserFormSU
        except ImportError:
            self.fail('Nie można zaimportować UserFormSU z szkp.forms — klasa nie istnieje')

    def test_tu_sul49_user_form_su_importowalny(self):
        """TU-SUL49: UserFormSU importowalny z szkp.forms."""
        self._get_form_class()

    def test_tu_sul50_puste_dane_sa_niepoprawne_brak_username(self):
        """TU-SUL50: UserFormSU(data={}, is_new=True).is_valid() == False, błąd w 'username'."""
        UserFormSU = self._get_form_class()
        form = UserFormSU(data={}, is_new=True)
        self.assertFalse(form.is_valid())
        self.assertIn(
            'username', form.errors,
            f"Brak błędu 'username' dla pustych danych. Błędy: {dict(form.errors)}",
        )

    def test_tu_sul51_niezgodne_hasla_sa_niepoprawne(self):
        """TU-SUL51: UserFormSU z niezgodnymi hasłami → is_valid() == False, błąd w 'password_confirm'."""
        UserFormSU = self._get_form_class()
        form = UserFormSU(
            data={
                'username': 'testuser',
                'password': 'HasloA1!',
                'password_confirm': 'HasloB2!',
            },
            is_new=True,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'password_confirm', form.errors,
            f"Brak błędu 'password_confirm' dla niezgodnych haseł. Błędy: {dict(form.errors)}",
        )

    def test_tu_sul52_poprawne_dane_z_haslem_sa_poprawne(self):
        """TU-SUL52: UserFormSU z poprawnymi danymi (create) → is_valid() == True."""
        UserFormSU = self._get_form_class()
        form = UserFormSU(
            data={
                'username': 'nowyuser',
                'email': 'nowy@test.pl',
                'password': 'BezpieczneHaslo1!',
                'password_confirm': 'BezpieczneHaslo1!',
            },
            is_new=True,
        )
        self.assertTrue(
            form.is_valid(),
            f'UserFormSU z poprawnymi danymi nie przeszedł walidacji. Błędy: {dict(form.errors)}',
        )

    def test_tu_sul53_puste_haslo_w_trybie_edycji_jest_poprawne(self):
        """TU-SUL53: UserFormSU(is_new=False) z pustym hasłem → is_valid() == True (hasło opcjonalne)."""
        UserFormSU = self._get_form_class()
        form = UserFormSU(
            data={
                'username': 'edytowanyuser',
                'email': 'edytowany@test.pl',
                'password': '',
                'password_confirm': '',
            },
            is_new=False,
        )
        self.assertTrue(
            form.is_valid(),
            f'UserFormSU(is_new=False) z pustym hasłem powinien być poprawny. Błędy: {dict(form.errors)}',
        )
