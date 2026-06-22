from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, tag
from django.template import Context, Template

from szkp.models import Client, ClientType


def _make_clients(n):
    Client.objects.bulk_create([
        Client(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='X',
            last_name=f'Klient{i}',
            pesel=f'{10000000000 + i:011d}',
        )
        for i in range(n)
    ])


@tag('integration')
class PaginationTagTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        _make_clients(25)

    def _render(self, template_str, page_num=1, extra_get=''):
        from django.core.paginator import Paginator
        factory = RequestFactory()
        url = f'/?page={page_num}'
        if extra_get:
            url += f'&{extra_get}'
        request = factory.get(url)
        qs = Client.objects.all().order_by('pk')
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_num)
        tpl = Template('{% load szkp_tags %}' + template_str)
        ctx = Context({'page_obj': page_obj, 'request': request})
        return tpl.render(ctx)

    def test_renders_prev_link_on_page_2(self):
        html = self._render('{% pagination page_obj %}', page_num=2)
        self.assertIn('page=1', html)
        self.assertNotIn('szkp-page-btn--disabled', html.split('‹')[0] + '‹')

    def test_renders_next_link_on_page_1(self):
        html = self._render('{% pagination page_obj %}', page_num=1)
        self.assertIn('page=2', html)

    def test_prev_disabled_on_first_page(self):
        html = self._render('{% pagination page_obj %}', page_num=1)
        self.assertIn('szkp-page-btn--disabled', html)

    def test_next_disabled_on_last_page(self):
        html = self._render('{% pagination page_obj %}', page_num=3)
        self.assertIn('szkp-page-btn--disabled', html)
        self.assertNotIn('page=4', html)

    def test_preserves_extra_get_params(self):
        html = self._render('{% pagination page_obj %}', page_num=2, extra_get='q=test&sort=name')
        self.assertIn('q=test', html)
        self.assertIn('sort=name', html)

    def test_shows_count_info(self):
        html = self._render('{% pagination page_obj %}', page_num=1)
        self.assertIn('z 25', html)


@tag('integration')
class PaginationDashTagTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        _make_clients(25)

    def _render(self, page_num=1, extra_get=''):
        from django.core.paginator import Paginator
        factory = RequestFactory()
        url = f'/?page={page_num}'
        if extra_get:
            url += f'&{extra_get}'
        request = factory.get(url)
        qs = Client.objects.all().order_by('pk')
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page_num)
        tpl = Template('{% load szkp_tags %}{% pagination_dash page_obj %}')
        ctx = Context({'page_obj': page_obj, 'request': request})
        return tpl.render(ctx)

    def test_renders_prev_link_on_page_2(self):
        html = self._render(page_num=2)
        self.assertIn('page=1', html)

    def test_renders_next_link_on_page_1(self):
        html = self._render(page_num=1)
        self.assertIn('page=2', html)

    def test_hidden_when_only_one_page(self):
        from django.core.paginator import Paginator
        factory = RequestFactory()
        request = factory.get('/?page=1')
        qs = Client.objects.order_by('pk')[:3]
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(1)
        tpl = Template('{% load szkp_tags %}{% pagination_dash page_obj %}')
        ctx = Context({'page_obj': page_obj, 'request': request})
        html = tpl.render(ctx)
        self.assertNotIn('dash-pagination', html)

    def test_preserves_extra_get_params(self):
        html = self._render(page_num=2, extra_get='q=test&sort=name')
        self.assertIn('q=test', html)
        self.assertIn('sort=name', html)
