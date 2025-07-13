from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    if dictionary:
        return dictionary.get(key)
    return None

@register.filter
def add(value, arg):
    """Add strings together"""
    return str(value) + str(arg)