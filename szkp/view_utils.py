from django.core.paginator import Paginator


def apply_sorting(qs, sort_param, dir_param, valid_fields, default_field):
    sort_field = valid_fields.get(sort_param, default_field)
    if dir_param == 'desc':
        sort_field = f'-{sort_field}'
    return qs.order_by(sort_field)


def apply_pagination(qs, page_param, per_page=20):
    paginator = Paginator(qs, per_page)
    return paginator.get_page(page_param)
