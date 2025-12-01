"""
HtmxModelAdmin - The main interface for HTMX-enhanced Django Admin.

This is the primary class developers will import. It extends Django's ModelAdmin
to provide HTMX-powered interactions like inline editing, modal forms, and more.
"""

import json
from django import forms
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import path
from django.utils.html import format_html

from .mixins import HtmxResponseMixin


def detect_admin_theme():
    """
    Detect which admin theme is installed.

    Returns:
        str: 'grappelli', 'jazzmin', 'django-suit', or 'default'
    """
    installed_apps = getattr(settings, 'INSTALLED_APPS', [])

    if 'grappelli' in installed_apps:
        return 'grappelli'
    elif 'jazzmin' in installed_apps:
        return 'jazzmin'
    elif 'suit' in installed_apps:
        return 'django-suit'
    else:
        return 'default'


class HtmxModelAdmin(HtmxResponseMixin, admin.ModelAdmin):
    """
    Enhanced ModelAdmin with HTMX-powered interactions.

    Attributes:
        list_editable_htmx (list[str]): Fields that can be edited inline
        list_filter_htmx (list[str]): Filters that update without reload
        modal_fields (list[str]): Fields to show in modal form
        htmx_enabled (bool): Master toggle (default: True)
        toast_messages (bool): Show toast notifications (default: True)

    Usage:
        @admin.register(Product)
        class ProductAdmin(HtmxModelAdmin):
            list_display = ['name', 'price', 'stock', 'category']
            list_editable_htmx = ['price', 'stock']
            list_filter_htmx = ['category']
            modal_fields = ['name', 'description', 'price']
    """

    # HTMX-specific attributes
    list_editable_htmx = []
    list_filter_htmx = []
    modal_fields = []
    htmx_enabled = True
    toast_messages = True

    # Template will be selected based on admin theme
    # Note: CSS and JS are loaded via the template to ensure single loading

    @property
    def change_list_template(self):
        """Select template based on detected admin theme."""
        theme = detect_admin_theme()
        if theme == 'grappelli':
            return 'htmx_admin/grappelli/change_list.html'
        return 'htmx_admin/change_list.html'

    def get_urls(self):
        """Add HTMX-specific URL patterns."""
        urls = super().get_urls()
        info = (self.model._meta.app_label, self.model._meta.model_name)

        htmx_urls = [
            path(
                '<path:object_id>/htmx-edit/<str:field>/',
                self.admin_site.admin_view(self.htmx_edit_field),
                name='%s_%s_htmx_edit' % info
            ),
            path(
                '<path:object_id>/htmx-delete/',
                self.admin_site.admin_view(self.htmx_delete),
                name='%s_%s_htmx_delete' % info
            ),
            path(
                'htmx-modal/<path:object_id>/',
                self.admin_site.admin_view(self.htmx_modal),
                name='%s_%s_htmx_modal' % info
            ),
            path(
                'htmx-table-body/',
                self.admin_site.admin_view(self.htmx_table_body),
                name='%s_%s_htmx_table_body' % info
            ),
            path(
                '<path:object_id>/htmx-cell/<str:field>/',
                self.admin_site.admin_view(self.htmx_get_cell),
                name='%s_%s_htmx_cell' % info
            ),
        ]
        return htmx_urls + urls

    def get_field_form(self, obj, field_name, data=None):
        """
        Generate a form for a single field.

        Args:
            obj: The model instance
            field_name: Name of the field to edit
            data: POST data (optional)

        Returns:
            A form instance for the specified field
        """
        model_field = self.model._meta.get_field(field_name)

        class SingleFieldForm(forms.ModelForm):
            class Meta:
                model = self.model
                fields = [field_name]

        if data:
            return SingleFieldForm(data, instance=obj)
        return SingleFieldForm(instance=obj)

    def htmx_edit_field(self, request, object_id, field):
        """
        Handle inline cell editing.

        GET: Returns the edit form for the field
        POST: Saves the field and returns updated cell

        Args:
            request: HTTP request
            object_id: Primary key of the object
            field: Name of the field to edit

        Returns:
            HTML fragment for the edit form or updated cell
        """
        obj = get_object_or_404(self.model, pk=object_id)

        # Verify field is in list_editable_htmx
        if field not in self.list_editable_htmx:
            return HttpResponse('Field not editable', status=403)

        if request.method == 'GET':
            form = self.get_field_form(obj, field)
            return render(request, 'htmx_admin/partials/edit_cell.html', {
                'form': form,
                'object': obj,
                'field': field,
                'opts': self.model._meta,
            })

        elif request.method == 'POST':
            form = self.get_field_form(obj, field, data=request.POST)
            if form.is_valid():
                form.save()
                response = render(
                    request,
                    'htmx_admin/partials/table_cell.html',
                    {
                        'object': obj,
                        'field': field,
                        'value': getattr(obj, field),
                        'opts': self.model._meta,
                        'is_editable': True,
                    }
                )
                response['HX-Trigger'] = 'cellUpdated'
                return response
            else:
                response = render(
                    request,
                    'htmx_admin/partials/edit_cell.html',
                    {'form': form, 'object': obj, 'field': field, 'opts': self.model._meta}
                )
                response.status_code = 422
                return response

        return HttpResponse('Method not allowed', status=405)

    def htmx_get_cell(self, request, object_id, field):
        """
        Get a single cell (used for cancel operations).

        Args:
            request: HTTP request
            object_id: Primary key of the object
            field: Name of the field

        Returns:
            HTML fragment for the cell
        """
        obj = get_object_or_404(self.model, pk=object_id)
        return render(
            request,
            'htmx_admin/partials/table_cell.html',
            {
                'object': obj,
                'field': field,
                'value': getattr(obj, field),
                'opts': self.model._meta,
                'is_editable': field in self.list_editable_htmx,
            }
        )

    def htmx_delete(self, request, object_id):
        """
        Handle deletion with HX-Trigger for row removal animation.

        Args:
            request: HTTP request
            object_id: Primary key of the object to delete

        Returns:
            204 No Content with HX-Trigger header
        """
        obj = get_object_or_404(self.model, pk=object_id)
        obj_display = str(obj)
        obj.delete()

        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({
            'showMessage': {
                'level': 'success',
                'message': f'{obj_display} deleted successfully.'
            },
            'refreshTable': True
        })
        return response

    def htmx_modal(self, request, object_id):
        """
        Modal form for add (object_id='add') or edit operations.

        GET: Returns the modal form HTML
        POST: Processes form submission

        Args:
            request: HTTP request
            object_id: 'add' for new objects, or the pk for editing

        Returns:
            HTML fragment for modal or 204 on success
        """
        if object_id == 'add':
            obj = None
        else:
            obj = get_object_or_404(self.model, pk=object_id)

        # Get the form class
        form_class = self.get_form(request, obj)

        # Filter to modal_fields if specified
        if self.modal_fields:
            class ModalForm(form_class):
                class Meta(form_class.Meta):
                    fields = self.modal_fields
            form_class = ModalForm

        if request.method == 'GET':
            form = form_class(instance=obj)
            return render(
                request,
                'htmx_admin/partials/modal_form.html',
                {'form': form, 'object': obj, 'opts': self.model._meta}
            )

        elif request.method == 'POST':
            form = form_class(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                self.save_model(request, form.instance, form, change=bool(obj))
                # Save many-to-many relationships if the form has them
                if hasattr(form, 'save_m2m'):
                    form.save_m2m()

                # Return empty content with triggers for:
                # 1. showMessage - display success toast
                # 2. refreshTable - reload the table data
                # 3. modalClosed - clean up modal (backup)
                response = HttpResponse('', status=200)
                response['HX-Trigger'] = json.dumps({
                    'showMessage': {
                        'level': 'success',
                        'message': f'{form.instance} saved successfully.'
                    },
                    'refreshTable': True,
                    'modalClosed': True
                })
                return response
            else:
                response = render(
                    request,
                    'htmx_admin/partials/modal_form.html',
                    {'form': form, 'object': obj, 'opts': self.model._meta}
                )
                response.status_code = 422
                return response

        return HttpResponse('Method not allowed', status=405)

    def htmx_table_body(self, request):
        """
        Return the table body for refreshing the list view.

        Args:
            request: HTTP request

        Returns:
            HTML fragment for table body
        """
        cl = self.get_changelist_instance(request)
        admin_theme = detect_admin_theme()

        return render(
            request,
            'htmx_admin/partials/table_body.html',
            {
                'cl': cl,
                'opts': self.model._meta,
                'list_editable_htmx': self.list_editable_htmx,
                'admin_theme': admin_theme,
                'is_grappelli': admin_theme == 'grappelli',
            }
        )

    def changelist_view(self, request, extra_context=None):
        """Override to add HTMX context."""
        extra_context = extra_context or {}
        admin_theme = detect_admin_theme()
        extra_context.update({
            'htmx_enabled': self.htmx_enabled,
            'list_editable_htmx': self.list_editable_htmx,
            'list_filter_htmx': self.list_filter_htmx,
            'modal_fields': self.modal_fields,
            'toast_messages': self.toast_messages,
            'admin_theme': admin_theme,
            'is_grappelli': admin_theme == 'grappelli',
        })
        return super().changelist_view(request, extra_context=extra_context)
