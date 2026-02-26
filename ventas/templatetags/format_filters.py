from django import template

register = template.Library()

@register.filter(name='commas')
def commas(value):
    try:
        if type(value) == str:
            value = value.replace(',', '')
        number = float(value)
        return "{:,.2f}".format(number)
    except (ValueError, TypeError):
        return value