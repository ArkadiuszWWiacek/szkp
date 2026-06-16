from urllib.parse import urlencode

from django import template

register = template.Library()


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
