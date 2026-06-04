from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permet d'accéder à un dictionnaire par clé variable dans un template.
    Usage : {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
