"""
R-06 — Atrybuty SRI dla zasobów Bootstrap CDN w base.html.
Testy jednostkowe (SimpleTestCase) + integracyjny (TestCase) — faza RED.

Testy jednostkowe czytają templates/base.html bezpośrednio.
Brak DB i serwera — bardzo szybkie (SimpleTestCase).

Test integracyjny renderuje stronę logowania (nie wymaga zalogowania)
i sprawdza response.content — jeden dowód end-to-end.

Podział klas:
    BootstrapSriInTemplateTest — odczyt pliku, 4 testy padające + 1 guard.
    BootstrapSriInResponseTest — renderowanie strony, 1 test padający.
"""
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, tag


BASE_HTML = Path(settings.BASE_DIR) / 'templates' / 'base.html'

# Oficjalne hashe Bootstrap 5.3.0 — źródło: https://getbootstrap.com/docs/5.3/
BOOTSTRAP_CSS_SRI = (
    'sha384-9ndCyUaIbzAi2FUVXJi0CjmCapSmO7SnpJef0486qhLnuZ2cdeRhO02iuK6FUUVM'
)
BOOTSTRAP_JS_SRI = (
    'sha384-geWF76RCwLtnZ8qwWowPQNguL3RmwHVBC9FhGdlKrxdiJJigb/j/68SIy3Te4Bkz'
)


# ===========================================================================
# Zawartość pliku base.html — TU-R06-01 – TU-R06-05
# ===========================================================================

@tag('unit')
class BootstrapSriInTemplateTest(SimpleTestCase):
    """
    Sprawdza, że templates/base.html zawiera atrybuty SRI dla Bootstrap.
    SimpleTestCase — żadna migracja ani logowanie nie jest potrzebne.

    TU-R06-01 – TU-R06-04 padają: integrity/crossorigin jeszcze nie dodane.
    TU-R06-05 przechodzi: Google Fonts nie powinno mieć integrity (guard).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.content = BASE_HTML.read_text(encoding='utf-8')

    # TU-R06-01
    def test_bootstrap_css_zawiera_poprawny_hash_sri(self):
        """
        Tag <link> Bootstrap CSS musi zawierać oficjalny hash SHA-384.
        PADA: hash nieobecny w pliku — atrybut integrity jeszcze nie dodany.
        """
        self.assertIn(
            BOOTSTRAP_CSS_SRI,
            self.content,
            f"Hash SRI dla Bootstrap CSS nie został dodany do base.html. "
            f"Oczekiwano: integrity=\"sha384-{BOOTSTRAP_CSS_SRI[:16]}...\"",
        )

    # TU-R06-02
    def test_bootstrap_css_zawiera_crossorigin_anonymous(self):
        """
        Tag <link> Bootstrap CSS musi mieć crossorigin="anonymous".
        PADA: crossorigin nieobecny przy tagu Bootstrap CSS.
        """
        css_pos = self.content.find('bootstrap@5.3.0/dist/css')
        self.assertGreater(css_pos, -1, "Tag Bootstrap CSS nie istnieje w base.html.")
        snippet = self.content[css_pos: css_pos + 400]
        self.assertIn(
            'crossorigin="anonymous"',
            snippet,
            "Tag <link> Bootstrap CSS nie ma atrybutu crossorigin=\"anonymous\".",
        )

    # TU-R06-03
    def test_bootstrap_js_zawiera_poprawny_hash_sri(self):
        """
        Tag <script> Bootstrap JS bundle musi zawierać oficjalny hash SHA-384.
        PADA: hash nieobecny w pliku — atrybut integrity jeszcze nie dodany.
        """
        self.assertIn(
            BOOTSTRAP_JS_SRI,
            self.content,
            f"Hash SRI dla Bootstrap JS nie został dodany do base.html. "
            f"Oczekiwano: integrity=\"sha384-{BOOTSTRAP_JS_SRI[:16]}...\"",
        )

    # TU-R06-04
    def test_bootstrap_js_zawiera_crossorigin_anonymous(self):
        """
        Tag <script> Bootstrap JS musi mieć crossorigin="anonymous".
        PADA: crossorigin nieobecny przy tagu Bootstrap JS.
        """
        js_pos = self.content.find('bootstrap@5.3.0/dist/js')
        self.assertGreater(js_pos, -1, "Tag Bootstrap JS nie istnieje w base.html.")
        snippet = self.content[js_pos: js_pos + 400]
        self.assertIn(
            'crossorigin="anonymous"',
            snippet,
            "Tag <script> Bootstrap JS nie ma atrybutu crossorigin=\"anonymous\".",
        )

    # TU-R06-05 — guard (musi przejść przed i po R-06)
    def test_google_fonts_nie_ma_atrybutu_integrity(self):
        """
        Żaden tag Google Fonts NIE może mieć integrity= — Google rotuje zasoby.
        Ten test jest guardem: musi przejść w RED i pozostać zielony po R-06.
        """
        bootstrap_pos = self.content.find('bootstrap@5.3.0')
        self.assertGreater(bootstrap_pos, -1, "Bootstrap nie istnieje w base.html.")
        fonts_section = self.content[:bootstrap_pos]
        self.assertIn(
            'fonts.googleapis.com',
            fonts_section,
            "Nie znaleziono tagów Google Fonts przed sekcją Bootstrap.",
        )
        self.assertNotIn(
            'integrity=',
            fonts_section,
            "Google Fonts ma atrybut integrity= — zgodnie z R-06 nie powinno.",
        )


# ===========================================================================
# Wyrenderowana odpowiedź HTTP — TI-R06-01
# ===========================================================================

@tag('integration')
class BootstrapSriInResponseTest(TestCase):
    """
    Jeden test integracyjny: renderuje stronę logowania (dostępna bez auth)
    i sprawdza, że wyrenderowany HTML zawiera hash SRI Bootstrap CSS.
    Wystarczy jeden: jeśli base.html jest renderowane poprawnie, oba hashe
    będą obecne — weryfikacja CSS obejmuje też wdrożenie mechanizmu.

    TI-R06-01 pada: hash nieobecny w response.content.
    """

    # TI-R06-01
    def test_wyrenderowana_strona_logowania_zawiera_hash_sri_bootstrap_css(self):
        """
        GET /accounts/login/ zwraca HTML zawierający hash SRI Bootstrap CSS.
        PADA: base.html jeszcze nie ma atrybutu integrity — hash nieobecny.
        """
        r = self.client.get('/accounts/login/')
        self.assertEqual(r.status_code, 200, "Strona logowania nie zwróciła 200.")
        self.assertContains(
            r,
            BOOTSTRAP_CSS_SRI,
            msg_prefix=(
                "Hash SRI Bootstrap CSS nieobecny w wyrenderowanym HTML strony logowania. "
                "R-06 nie zostało jeszcze zaimplementowane."
            ),
        )
