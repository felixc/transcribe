import django.template


register = django.template.Library()


@register.filter
def remove_newlines(text):
    """Template filter to replace newlines with spaces."""
    return text.replace('\n', ' ').rstrip(' ')


@register.filter
def dedent(text):
    """Template filter to un-indent text by removing leading spaces."""
    results = []
    for line in text.splitlines():
        results.append(line.lstrip(' '))
    return "\n".join(results)
