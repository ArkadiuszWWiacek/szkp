from django.test import SimpleTestCase, TestCase, tag

from szkp.view_utils import apply_pagination, apply_sorting


@tag('unit')
class ApplySortingTest(SimpleTestCase):

    VALID_FIELDS = {
        'name': 'last_name',
        'date': 'created_at',
    }
    DEFAULT = 'last_name'

    def _qs(self):
        return None

    def test_known_key_asc(self):
        class FakeQS:
            def order_by(self, field):
                self.ordered_by = field
                return self
        qs = FakeQS()
        result = apply_sorting(qs, 'name', 'asc', self.VALID_FIELDS, self.DEFAULT)
        self.assertEqual(result.ordered_by, 'last_name')

    def test_known_key_desc(self):
        class FakeQS:
            def order_by(self, field):
                self.ordered_by = field
                return self
        qs = FakeQS()
        result = apply_sorting(qs, 'name', 'desc', self.VALID_FIELDS, self.DEFAULT)
        self.assertEqual(result.ordered_by, '-last_name')

    def test_unknown_key_falls_back_to_default(self):
        class FakeQS:
            def order_by(self, field):
                self.ordered_by = field
                return self
        qs = FakeQS()
        result = apply_sorting(qs, 'nieznany', 'asc', self.VALID_FIELDS, self.DEFAULT)
        self.assertEqual(result.ordered_by, self.DEFAULT)

    def test_unknown_key_desc_falls_back_to_default_with_prefix(self):
        class FakeQS:
            def order_by(self, field):
                self.ordered_by = field
                return self
        qs = FakeQS()
        result = apply_sorting(qs, 'nieznany', 'desc', self.VALID_FIELDS, self.DEFAULT)
        self.assertEqual(result.ordered_by, f'-{self.DEFAULT}')

    def test_empty_sort_param_falls_back_to_default(self):
        class FakeQS:
            def order_by(self, field):
                self.ordered_by = field
                return self
        qs = FakeQS()
        result = apply_sorting(qs, '', 'asc', self.VALID_FIELDS, self.DEFAULT)
        self.assertEqual(result.ordered_by, self.DEFAULT)


@tag('unit')
class ApplyPaginationTest(TestCase):

    def _make_list(self, n):
        from szkp.models import ClientType
        from szkp.models import Client
        return Client.objects.bulk_create([
            Client(
                type=ClientType.OSOBA_FIZYCZNA,
                first_name='X',
                last_name=f'Klient{i}',
                pesel=f'{10000000000 + i:011d}',
            )
            for i in range(n)
        ])

    def test_returns_first_page(self):
        self._make_list(25)
        from szkp.models import Client
        qs = Client.objects.order_by('pk')
        page = apply_pagination(qs, '1', per_page=10)
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page.object_list), 10)

    def test_returns_last_page_for_out_of_range(self):
        self._make_list(5)
        from szkp.models import Client
        qs = Client.objects.order_by('pk')
        page = apply_pagination(qs, '999', per_page=10)
        self.assertEqual(page.number, 1)

    def test_empty_queryset(self):
        from szkp.models import Client
        qs = Client.objects.none()
        page = apply_pagination(qs, '1')
        self.assertEqual(len(page.object_list), 0)

    def test_default_per_page_is_20(self):
        self._make_list(25)
        from szkp.models import Client
        qs = Client.objects.order_by('pk')
        page = apply_pagination(qs, '1')
        self.assertEqual(len(page.object_list), 20)
