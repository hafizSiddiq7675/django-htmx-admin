"""
Template tags for django-htmx-admin.

These template tags provide convenient ways to add HTMX attributes
to HTML elements in Django templates.
"""

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.simple_tag
def htmx_edit_url(obj, field):
    """
    Generate the URL for inline editing a field.

    Usage:
        {% htmx_edit_url object 'price' %}

    Args:
        obj: Model instance
        field: Field name to edit

    Returns:
        URL string for the HTMX edit endpoint
    """
    opts = obj._meta
    return reverse(
        f'admin:{opts.app_label}_{opts.model_name}_htmx_edit',
        args=[obj.pk, field]
    )


@register.simple_tag
def htmx_delete_url(obj):
    """
    Generate the URL for deleting an object via HTMX.

    Usage:
        {% htmx_delete_url object %}

    Args:
        obj: Model instance

    Returns:
        URL string for the HTMX delete endpoint
    """
    opts = obj._meta
    return reverse(
        f'admin:{opts.app_label}_{opts.model_name}_htmx_delete',
        args=[obj.pk]
    )


@register.simple_tag
def htmx_modal_url(opts, object_id='add'):
    """
    Generate the URL for the modal form.

    Usage:
        {% htmx_modal_url opts %}  {# For add #}
        {% htmx_modal_url opts object.pk %}  {# For edit #}

    Args:
        opts: Model _meta options
        object_id: 'add' for new objects, or pk for editing

    Returns:
        URL string for the HTMX modal endpoint
    """
    return reverse(
        f'admin:{opts.app_label}_{opts.model_name}_htmx_modal',
        args=[object_id]
    )


@register.simple_tag
def htmx_cell_url(obj, field):
    """
    Generate the URL for getting a cell (for cancel operations).

    Usage:
        {% htmx_cell_url object 'price' %}

    Args:
        obj: Model instance
        field: Field name

    Returns:
        URL string for the HTMX cell endpoint
    """
    opts = obj._meta
    return reverse(
        f'admin:{opts.app_label}_{opts.model_name}_htmx_cell',
        args=[obj.pk, field]
    )


@register.simple_tag
def htmx_table_body_url(opts):
    """
    Generate the URL for refreshing the table body.

    Usage:
        {% htmx_table_body_url opts %}

    Args:
        opts: Model _meta options

    Returns:
        URL string for the HTMX table body endpoint
    """
    return reverse(
        f'admin:{opts.app_label}_{opts.model_name}_htmx_table_body'
    )


@register.simple_tag
def htmx_attrs(trigger='click', target=None, swap='outerHTML', **kwargs):
    """
    Generate HTMX attributes as a string.

    Usage:
        <button {% htmx_attrs trigger='click' target='#result' swap='innerHTML' %}>
            Click me
        </button>

    Args:
        trigger: Event that triggers the request (default: 'click')
        target: CSS selector for target element
        swap: Swap mode (default: 'outerHTML')
        **kwargs: Additional hx-* attributes

    Returns:
        String of HTMX attributes
    """
    attrs = []

    if trigger:
        attrs.append(f'hx-trigger="{trigger}"')
    if target:
        attrs.append(f'hx-target="{target}"')
    if swap:
        attrs.append(f'hx-swap="{swap}"')

    # Add any additional attributes
    for key, value in kwargs.items():
        # Convert underscores to hyphens (e.g., hx_get -> hx-get)
        attr_name = key.replace('_', '-')
        if not attr_name.startswith('hx-'):
            attr_name = f'hx-{attr_name}'
        attrs.append(f'{attr_name}="{value}"')

    return mark_safe(' '.join(attrs))


@register.inclusion_tag('htmx_admin/partials/toast_container.html')
def toast_container():
    """
    Render the toast notification container.

    Usage:
        {% load htmx_admin_tags %}
        {% toast_container %}

    Returns:
        Rendered toast container HTML
    """
    return {}


@register.inclusion_tag('htmx_admin/partials/modal_container.html')
def modal_container():
    """
    Render the modal container.

    Usage:
        {% load htmx_admin_tags %}
        {% modal_container %}

    Returns:
        Rendered modal container HTML
    """
    return {}


@register.filter
def get_field_value(obj, field_name):
    """
    Get a field value from an object.

    Usage:
        {{ object|get_field_value:'price' }}

    Args:
        obj: Model instance
        field_name: Name of the field

    Returns:
        Field value
    """
    return getattr(obj, field_name, '')


@register.filter(name='enumerate')
def enumerate_filter(iterable):
    """
    Enumerate an iterable for use in templates.

    Usage:
        {% for i, item in items|enumerate %}

    Args:
        iterable: Any iterable

    Returns:
        Enumerated iterable with index starting at 1
    """
    import builtins
    return list(builtins.enumerate(iterable, start=1))


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary.

    Usage:
        {{ my_dict|get_item:key }}

    Args:
        dictionary: Dict to get item from
        key: Key to lookup

    Returns:
        Value or None
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def sort_param(index, cl):
    """
    Generate the sort parameter for a column.

    Usage:
        {{ i|sort_param:cl }}

    Args:
        index: Column index (1-based)
        cl: ChangeList instance

    Returns:
        Sort parameter string (e.g., '1' for ascending, '-1' for descending)
    """
    # Get current ordering
    ordering = cl.params.get('o', '')

    # Check if this column is currently being sorted
    if ordering:
        current_orders = ordering.split('.')
        for order in current_orders:
            if order.lstrip('-') == str(index):
                # Column is sorted, toggle direction
                if order.startswith('-'):
                    return str(index)  # Currently desc, switch to asc
                else:
                    return f'-{index}'  # Currently asc, switch to desc

    # Column is not sorted, default to ascending
    return str(index)


@register.filter
def current_sort_order(index, cl):
    """
    Get the current sort order for a column.

    Usage:
        {{ i|current_sort_order:cl }}

    Args:
        index: Column index (1-based)
        cl: ChangeList instance

    Returns:
        'asc', 'desc', or empty string if not sorted
    """
    ordering = cl.params.get('o', '')

    if ordering:
        current_orders = ordering.split('.')
        for order in current_orders:
            if order.lstrip('-') == str(index):
                if order.startswith('-'):
                    return 'desc'
                else:
                    return 'asc'

    return ''


@register.filter
def is_htmx_editable(field_name, editable_fields):
    """
    Check if a field is in the HTMX editable list.

    Usage:
        {% if field|is_htmx_editable:list_editable_htmx %}

    Args:
        field_name: Name of the field
        editable_fields: List of editable field names

    Returns:
        bool: True if field is editable
    """
    return field_name in editable_fields


@register.simple_tag(takes_context=True)
def htmx_csrf_token(context):
    """
    Render CSRF token for HTMX requests.

    Usage:
        {% htmx_csrf_token %}

    Returns:
        Hidden input with CSRF token
    """
    csrf_token = context.get('csrf_token', '')
    return mark_safe(f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">')


@register.simple_tag
def json_encode(value):
    """
    JSON encode a value for use in HTML attributes.

    Usage:
        <div hx-vals='{% json_encode my_dict %}'>

    Args:
        value: Value to encode

    Returns:
        JSON string
    """
    return mark_safe(json.dumps(value))
