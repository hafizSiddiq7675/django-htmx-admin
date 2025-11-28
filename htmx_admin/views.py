"""
AJAX endpoints for django-htmx-admin.

This module contains standalone views that can be used outside of the admin interface
for custom HTMX integrations.
"""

import json
from django.http import HttpResponse
from django.views import View
from django.views.generic.edit import FormView

from .mixins import HtmxResponseMixin, HtmxFormMixin


class HtmxDeleteView(HtmxResponseMixin, View):
    """
    Generic HTMX delete view.

    Usage:
        path('items/<int:pk>/delete/',
             HtmxDeleteView.as_view(model=Item),
             name='item-delete')
    """

    model = None
    success_message = '{object} deleted successfully.'

    def post(self, request, pk):
        """Handle DELETE/POST request."""
        obj = self.model.objects.get(pk=pk)
        obj_display = str(obj)
        obj.delete()

        return self.htmx_response(
            status=204,
            rowDeleted={'id': str(pk)},
            showMessage={
                'level': 'success',
                'message': self.success_message.format(object=obj_display)
            }
        )


class HtmxFormView(HtmxFormMixin, FormView):
    """
    Generic HTMX form view.

    Usage:
        class ItemCreateView(HtmxFormView):
            form_class = ItemForm
            template_name = 'partials/item_form.html'
    """

    def get(self, request, *args, **kwargs):
        """Return form for HTMX requests."""
        if self.is_htmx_request(request):
            return super().get(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)


class HtmxInlineEditView(HtmxResponseMixin, View):
    """
    Generic inline edit view for single field editing.

    Usage:
        path('items/<int:pk>/edit/<str:field>/',
             HtmxInlineEditView.as_view(model=Item, editable_fields=['name', 'price']),
             name='item-inline-edit')
    """

    model = None
    editable_fields = []
    form_template = 'htmx_admin/partials/edit_cell.html'
    cell_template = 'htmx_admin/partials/table_cell.html'

    def get_field_form(self, obj, field_name, data=None):
        """Generate a form for a single field."""
        from django import forms

        model_field = self.model._meta.get_field(field_name)

        class SingleFieldForm(forms.ModelForm):
            class Meta:
                model = self.model
                fields = [field_name]

        if data:
            return SingleFieldForm(data, instance=obj)
        return SingleFieldForm(instance=obj)

    def get(self, request, pk, field):
        """Return edit form for the field."""
        from django.shortcuts import render, get_object_or_404

        if field not in self.editable_fields:
            return HttpResponse('Field not editable', status=403)

        obj = get_object_or_404(self.model, pk=pk)
        form = self.get_field_form(obj, field)

        return render(request, self.form_template, {
            'form': form,
            'object': obj,
            'field': field,
            'opts': self.model._meta,
        })

    def post(self, request, pk, field):
        """Save the field value."""
        from django.shortcuts import render, get_object_or_404

        if field not in self.editable_fields:
            return HttpResponse('Field not editable', status=403)

        obj = get_object_or_404(self.model, pk=pk)
        form = self.get_field_form(obj, field, data=request.POST)

        if form.is_valid():
            form.save()
            response = render(
                request,
                self.cell_template,
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
                self.form_template,
                {'form': form, 'object': obj, 'field': field, 'opts': self.model._meta}
            )
            response.status_code = 422
            return response


class HtmxModalView(HtmxResponseMixin, View):
    """
    Generic modal view for create/edit operations.

    Usage:
        path('items/modal/<path:object_id>/',
             HtmxModalView.as_view(model=Item, form_class=ItemForm),
             name='item-modal')
    """

    model = None
    form_class = None
    template_name = 'htmx_admin/partials/modal_form.html'

    def get(self, request, object_id):
        """Return modal form."""
        from django.shortcuts import render, get_object_or_404

        if object_id == 'add':
            obj = None
        else:
            obj = get_object_or_404(self.model, pk=object_id)

        form = self.form_class(instance=obj)

        return render(request, self.template_name, {
            'form': form,
            'object': obj,
            'opts': self.model._meta,
        })

    def post(self, request, object_id):
        """Process form submission."""
        from django.shortcuts import render, get_object_or_404

        if object_id == 'add':
            obj = None
        else:
            obj = get_object_or_404(self.model, pk=object_id)

        form = self.form_class(request.POST, request.FILES, instance=obj)

        if form.is_valid():
            instance = form.save()
            return self.htmx_response(
                status=204,
                modalClosed=True,
                tableRefresh=True,
                showMessage={
                    'level': 'success',
                    'message': f'{instance} saved successfully.'
                }
            )
        else:
            response = render(request, self.template_name, {
                'form': form,
                'object': obj,
                'opts': self.model._meta,
            })
            response.status_code = 422
            return response
