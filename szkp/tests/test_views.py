from django.test import SimpleTestCase, tag
from szkp.views import home

@tag('integration')
class HomeViewTest(SimpleTestCase):
    """Widok home (/szkp/): dostępność i użyty szablon."""

    def test_home_view_status_code(self):
        """GET /szkp/ zwraca odpowiedź 200 OK."""
        response = self.client.get('/szkp/')
        self.assertEqual(response.status_code, 200)

    def test_home_view_template_used(self):
        """GET /szkp/ renderuje szablon szkp/home.html."""
        response = self.client.get('/szkp/')
        self.assertTemplateUsed(response, 'szkp/home.html')