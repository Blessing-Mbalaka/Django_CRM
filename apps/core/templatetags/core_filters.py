from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Allow dict lookups in templates: {{ my_dict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0


@register.simple_tag(takes_context=True)
def url_replace(context, field, value):
    """
    Return the current query string with `field` replaced by `value`.
    Used for pagination links to preserve existing filter params.
    Usage: {% url_replace 'page' page_obj.next_page_number %}
    """
    request = context.get('request')
    if request is None:
        return f'?{field}={value}'
    params = request.GET.copy()
    params[field] = value
    return f'?{params.urlencode()}'

