import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='clean_html')
def clean_html(value):
    # Remove <style> and <meta> tags along with their content
    value = re.sub(r'<style[\s\S]*?</style>', '', value)
    value = re.sub(r'<meta[\s\S]*?>', '', value)
    # Remove ```html and ```
    value = re.sub(r'```html|```', '', value)
    return mark_safe(value)
