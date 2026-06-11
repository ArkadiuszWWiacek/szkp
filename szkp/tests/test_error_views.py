from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from Python_Web.views import handler_400, handler_403, handler_404, handler_500


class ErrorViewsDirectTest(SimpleTestCase):
    """Testuje widoki błędów wywołując je bezpośrednio (niezależnie od DEBUG)."""

    def _make_request(self):
        from django.test import RequestFactory
        return RequestFactory().get('/')

    def test_400_status_and_template(self):
        request = self._make_request()
        response = handler_400(request)
        self.assertEqual(response.status_code, 400)

    def test_403_status_and_template(self):
        request = self._make_request()
        response = handler_403(request)
        self.assertEqual(response.status_code, 403)

    def test_404_status_and_template(self):
        request = self._make_request()
        response = handler_404(request)
        self.assertEqual(response.status_code, 404)

    def test_500_status_and_template(self):
        request = self._make_request()
        response = handler_500(request)
        self.assertEqual(response.status_code, 500)


@override_settings(DEBUG=False)
class ErrorViewsIntegrationTest(SimpleTestCase):
    """Testuje niestandardowe handlery przez klienta HTTP przy DEBUG=False."""

    def test_404_uses_custom_template(self):
        response = self.client.get('/nieistniejacy-url-abcxyz/', follow=False)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')

    def test_403_uses_custom_template(self):
        from django.core.exceptions import PermissionDenied
        from django.test import RequestFactory
        from Python_Web.views import handler_403

        request = RequestFactory().get('/')
        response = handler_403(request, exception=PermissionDenied())
        self.assertEqual(response.status_code, 403)

    def test_500_uses_custom_template(self):
        from django.test import RequestFactory
        from Python_Web.views import handler_500

        request = RequestFactory().get('/')
        response = handler_500(request)
        self.assertEqual(response.status_code, 500)
