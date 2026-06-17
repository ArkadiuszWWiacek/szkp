"""
R-04 — Testy jednostkowe funkcji sort_th z szkp.templatetags.szkp_tags.

Testowana jednostka: sort_th(context, key, label)
Odpowiedzialność: na podstawie kontekstu szablonu i argumentów
zwraca słownik z metadanymi potrzebnymi do renderowania sortowalnego <th>.
"""
from unittest.mock import MagicMock

from django.http import QueryDict
from django.test import SimpleTestCase, tag


def _make_request(query_string=''):
    """Pomocnicza fabryka: zwraca obiekt request z GET wypełnionym z query_string."""
    req = MagicMock()
    req.GET = QueryDict(query_string)
    return req


def _ctx(sort='', direction='asc', request=None):
    """Buduje minimalny kontekst szablonu."""
    return {'sort': sort, 'direction': direction, 'request': request}


@tag('unit')
class SortThIsActiveTest(SimpleTestCase):
    """TU-R04-01 / TU-R04-02 — flaga is_active."""

    # TU-R04-01
    def test_is_active_true_gdy_key_rowna_sie_sort(self):
        """`is_active=True` gdy key == context['sort']."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(sort='case_number'), key='case_number', label='Sygnatura')
        self.assertTrue(result['is_active'])

    # TU-R04-02
    def test_is_active_false_gdy_key_rozni_sie_od_sort(self):
        """`is_active=False` gdy key != context['sort']."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(sort='client'), key='case_number', label='Sygnatura')
        self.assertFalse(result['is_active'])


@tag('unit')
class SortThNextDirTest(SimpleTestCase):
    """TU-R04-03 – TU-R04-05 — obliczanie następnego kierunku sortowania."""

    # TU-R04-03
    def test_next_dir_desc_gdy_aktywna_i_asc(self):
        """`dir=desc` w URL gdy kolumna aktywna i kierunek='asc'."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(sort='status', direction='asc'), key='status', label='Status')
        self.assertIn('dir=desc', result['url'])

    # TU-R04-04
    def test_next_dir_asc_gdy_aktywna_i_desc(self):
        """`dir=asc` w URL gdy kolumna aktywna i kierunek='desc'."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(sort='status', direction='desc'), key='status', label='Status')
        self.assertIn('dir=asc', result['url'])

    # TU-R04-05
    def test_next_dir_asc_gdy_nieaktywna(self):
        """`dir=asc` w URL gdy kolumna nieaktywna (niezależnie od bieżącego kierunku)."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(sort='client', direction='desc'), key='case_number', label='Sygnatura')
        self.assertIn('dir=asc', result['url'])


@tag('unit')
class SortThUrlParamsTest(SimpleTestCase):
    """TU-R04-06 – TU-R04-12 — budowanie URL z parametrami GET."""

    # TU-R04-06
    def test_url_zawiera_sort_z_podanym_kluczem(self):
        """URL zawiera `sort=<key>` dla każdej kolumny."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(), key='case_number', label='Sygnatura')
        self.assertIn('sort=case_number', result['url'])

    # TU-R04-07
    def test_url_zaczyna_sie_od_znaku_zapytania(self):
        """URL zaczyna się od '?' (jest relative query string, nie pełny URL)."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(), key='case_number', label='Sygnatura')
        self.assertTrue(result['url'].startswith('?'))

    # TU-R04-08
    def test_url_zachowuje_inne_parametry_get(self):
        """URL zachowuje parametry GET inne niż sort/dir/page."""
        from szkp.templatetags.szkp_tags import sort_th
        req = _make_request('q=testval&status=nowa')
        result = sort_th(_ctx(request=req), key='case_number', label='Sygnatura')
        self.assertIn('q=testval', result['url'])
        self.assertIn('status=nowa', result['url'])

    # TU-R04-09
    def test_url_pomija_parametr_sort_z_request_get(self):
        """URL nie duplikuje stariej wartości `sort` z request.GET — zastępuje ją."""
        from szkp.templatetags.szkp_tags import sort_th
        req = _make_request('sort=stary_klucz&q=abc')
        result = sort_th(_ctx(request=req), key='nowy_klucz', label='Nowa')
        self.assertNotIn('sort=stary_klucz', result['url'])
        self.assertIn('sort=nowy_klucz', result['url'])

    # TU-R04-10
    def test_url_pomija_parametr_dir_z_request_get(self):
        """URL nie duplikuje stariej wartości `dir` z request.GET — zastępuje ją."""
        from szkp.templatetags.szkp_tags import sort_th
        req = _make_request('dir=stary_kierunek&q=abc')
        result = sort_th(_ctx(request=req), key='col', label='Kolumna')
        self.assertNotIn('dir=stary_kierunek', result['url'])

    # TU-R04-11
    def test_url_pomija_parametr_page_z_request_get(self):
        """URL wyklucza `page` z request.GET — kliknięcie sortowania wraca do str. 1."""
        from szkp.templatetags.szkp_tags import sort_th
        req = _make_request('page=5&q=abc')
        result = sort_th(_ctx(request=req), key='col', label='Kolumna')
        self.assertNotIn('page=', result['url'])

    # TU-R04-12
    def test_url_gdy_brak_request_zawiera_tylko_sort_i_dir(self):
        """Gdy kontekst nie ma `request`, URL zawiera tylko sort i dir (bez innych params)."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(request=None), key='col', label='Kolumna')
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(result['url'].lstrip('?'))
        self.assertSetEqual(set(qs.keys()), {'sort', 'dir'})


@tag('unit')
class SortThCurrentDirTest(SimpleTestCase):
    """TU-R04-13 – TU-R04-14 — zwracane current_dir."""

    # TU-R04-13
    def test_current_dir_rowna_sie_direction_gdy_aktywna(self):
        """`current_dir` == context['direction'] gdy kolumna jest aktywna."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(sort='status', direction='desc'), key='status', label='Status')
        self.assertEqual(result['current_dir'], 'desc')

    # TU-R04-14
    def test_current_dir_pusty_gdy_nieaktywna(self):
        """`current_dir` == '' gdy kolumna nie jest aktywna."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(sort='other', direction='asc'), key='status', label='Status')
        self.assertEqual(result['current_dir'], '')


@tag('unit')
class SortThReturnedFieldsTest(SimpleTestCase):
    """TU-R04-15 – TU-R04-16 — label i key w słowniku wynikowym."""

    # TU-R04-15
    def test_label_zwracany_bez_zmian(self):
        """`label` w wyniku === przekazanemu argumentowi label."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(), key='x', label='Moja etykieta')
        self.assertEqual(result['label'], 'Moja etykieta')

    # TU-R04-16
    def test_key_zwracany_bez_zmian(self):
        """`key` w wyniku === przekazanemu argumentowi key."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(), key='my_key', label='L')
        self.assertEqual(result['key'], 'my_key')


@tag('unit')
class SortThDefaultsTest(SimpleTestCase):
    """TU-R04-17 – TU-R04-20 — domyślne wartości i zachowanie przy brakujących kluczach."""

    # TU-R04-17
    def test_brak_request_w_kontekscie_nie_rzuca_wyjatku(self):
        """Wywołanie bez `request` w kontekście nie powoduje wyjątku."""
        from szkp.templatetags.szkp_tags import sort_th
        try:
            sort_th({}, key='col', label='L')
        except Exception as e:
            self.fail(f'sort_th rzucił wyjątek przy braku request: {e}')

    # TU-R04-18
    def test_domyslny_sort_pusty_string(self):
        """Gdy kontekst nie ma `sort`, is_active=False dla każdego klucza."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th({}, key='col', label='L')
        self.assertFalse(result['is_active'])

    # TU-R04-19
    def test_domyslny_direction_asc(self):
        """Gdy kontekst nie ma `direction`, kolumna nieaktywna linkuje do dir=asc."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th({'sort': 'other'}, key='col', label='L')
        self.assertIn('dir=asc', result['url'])

    # TU-R04-20
    def test_slownik_wyniku_zawiera_wymagane_klucze(self):
        """Wynikowy słownik zawiera wszystkie klucze potrzebne partial sort_th.html."""
        from szkp.templatetags.szkp_tags import sort_th
        result = sort_th(_ctx(), key='col', label='L')
        for key in ('key', 'label', 'is_active', 'current_dir', 'url'):
            self.assertIn(key, result, f'Brakujący klucz w wyniku sort_th: {key!r}')
