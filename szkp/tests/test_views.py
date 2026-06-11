from django.test import SimpleTestCase, tag
from szkp.views import home

@tag('integration')
class HomeViewTest(SimpleTestCase):
    def test_home_view_status_code(self):
        response = self.client.get('/szkp/')
        self.assertEqual(response.status_code, 200)
        
    def test_home_view_template_used(self):
        response = self.client.get('/szkp/')
        self.assertTemplateUsed(response, 'szkp/home.html')