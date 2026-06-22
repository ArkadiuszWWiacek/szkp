from urllib.parse import urlencode

from django import template

register = template.Library()


def _base_url_without_page(request):
    """Zwraca słownik parametrów GET bez klucza 'page'."""
    if not request:
        return {}
    return {k: v for k, v in request.GET.items() if k != 'page'}


@register.filter
def widget_value(bound_field):
    """Zwraca wartość pola sformatowaną przez widget (np. daty jako YYYY-MM-DD)."""
    return bound_field.field.widget.format_value(bound_field.value())


@register.inclusion_tag('szkp/partials/sort_th.html', takes_context=True)
def sort_th(context, key, label):
    """Renderuje sortowalny nagłówek tabeli <th>.
    Użycie: {% sort_th "case_number" "Sygnatura" %}
    Wymaga w kontekście: sort, direction oraz request (przez context processor).
    """
    sort = context.get('sort', '')
    direction = context.get('direction', 'asc')
    request = context.get('request')

    params = {}
    if request:
        params = {k: v for k, v in request.GET.items()
                  if k not in ('sort', 'dir', 'page')}

    is_active = (sort == key)
    next_dir = 'desc' if (is_active and direction == 'asc') else 'asc'
    params['sort'] = key
    params['dir'] = next_dir

    return {
        'key': key,
        'label': label,
        'is_active': is_active,
        'current_dir': direction if is_active else '',
        'url': f'?{urlencode(params)}',
    }


@register.inclusion_tag('szkp/partials/pagination.html', takes_context=True)
def pagination(context, page_obj):
    """Renderuje paginację w stylu Bootstrap (base.html).
    Użycie: {% pagination page_obj %}
    """
    params = _base_url_without_page(context.get('request'))
    base_url = f'?{urlencode(params)}&' if params else '?'
    return {'page_obj': page_obj, 'base_url': base_url}


@register.inclusion_tag('szkp/partials/pagination_dash.html', takes_context=True)
def pagination_dash(context, page_obj):
    """Renderuje paginację w stylu dashboard (base_dash.html).
    Użycie: {% pagination_dash page_obj %}
    """
    params = _base_url_without_page(context.get('request'))
    base_url = f'?{urlencode(params)}&' if params else '?'
    return {'page_obj': page_obj, 'base_url': base_url}
