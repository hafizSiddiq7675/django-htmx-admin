"""
Reusable mixins for django-htmx-admin.

These mixins provide HTMX response utilities that can be used in any Django view.
"""

import json
from django.http import HttpResponse


class HtmxResponseMixin:
    """
    Mixin providing HTMX response utilities.

    This mixin adds helper methods for creating HTMX-compatible responses
    with HX-Trigger headers and proper status codes.

    Usage:
        class MyView(HtmxResponseMixin, View):
            def post(self, request):
                # Do something
                return self.htmx_response(
                    status=204,
                    showMessage={'level': 'success', 'message': 'Done!'}
                )
    """

    def is_htmx_request(self, request):
        """
        Check if request originated from HTMX.

        Args:
            request: Django HTTP request

        Returns:
            bool: True if request has HX-Request header
        """
        return request.headers.get('HX-Request') == 'true'

    def htmx_response(self, content='', status=200, **triggers):
        """
        Create response with HX-Trigger header.

        Args:
            content: Response body content (default: empty string)
            status: HTTP status code (default: 200)
            **triggers: Keyword arguments become HX-Trigger events

        Returns:
            HttpResponse with HX-Trigger header if triggers provided

        Example:
            return self.htmx_response(
                status=204,
                rowDeleted={'id': 123},
                showMessage={'level': 'success', 'message': 'Deleted!'}
            )
        """
        response = HttpResponse(content, status=status)
        if triggers:
            response['HX-Trigger'] = json.dumps(triggers)
        return response

    def htmx_redirect(self, url):
        """
        Trigger client-side redirect via HTMX.

        This returns a 204 response with HX-Redirect header,
        causing HTMX to perform a client-side redirect.

        Args:
            url: URL to redirect to

        Returns:
            HttpResponse with HX-Redirect header
        """
        response = HttpResponse(status=204)
        response['HX-Redirect'] = url
        return response

    def htmx_refresh(self):
        """
        Trigger full page refresh via HTMX.

        Returns:
            HttpResponse with HX-Refresh header
        """
        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true'
        return response

    def htmx_push_url(self, url, content='', status=200):
        """
        Push URL to browser history.

        Args:
            url: URL to push to history
            content: Response body content
            status: HTTP status code

        Returns:
            HttpResponse with HX-Push-Url header
        """
        response = HttpResponse(content, status=status)
        response['HX-Push-Url'] = url
        return response


class HtmxFormMixin(HtmxResponseMixin):
    """
    Mixin for HTMX form handling.

    This mixin overrides form_valid and form_invalid to return
    HTMX-compatible responses with appropriate status codes.

    Usage:
        class MyFormView(HtmxFormMixin, FormView):
            form_class = MyForm
            template_name = 'my_form.html'
            success_message = 'Form submitted successfully!'
    """

    success_message = 'Saved successfully.'

    def form_invalid(self, form):
        """
        Return form with 422 status for HTMX to swap.

        HTMX will still swap content on 422 responses,
        allowing the form with errors to be displayed.

        Args:
            form: Invalid form instance

        Returns:
            Response with 422 status code
        """
        response = super().form_invalid(form)
        response.status_code = 422  # Unprocessable Entity
        return response

    def form_valid(self, form):
        """
        Save and return success trigger.

        Args:
            form: Valid form instance

        Returns:
            204 response with HX-Trigger for success message
        """
        self.object = form.save()
        return self.htmx_response(
            status=204,
            formSuccess=True,
            showMessage={
                'level': 'success',
                'message': self.get_success_message()
            }
        )

    def get_success_message(self):
        """
        Get the success message to display.

        Override this method to customize the success message.

        Returns:
            str: Success message
        """
        if hasattr(self, 'object') and self.object:
            return f'{self.object} saved successfully.'
        return self.success_message


class HtmxDeleteMixin(HtmxResponseMixin):
    """
    Mixin for HTMX delete operations.

    Usage:
        class MyDeleteView(HtmxDeleteMixin, DeleteView):
            model = MyModel
    """

    delete_message = '{object} deleted successfully.'

    def delete(self, request, *args, **kwargs):
        """
        Handle delete with HTMX response.

        Returns:
            204 response with HX-Trigger for deletion animation
        """
        self.object = self.get_object()
        obj_display = str(self.object)
        pk = self.object.pk
        self.object.delete()

        return self.htmx_response(
            status=204,
            rowDeleted={'id': str(pk)},
            showMessage={
                'level': 'success',
                'message': self.delete_message.format(object=obj_display)
            }
        )

    # Django 4.0+ uses form_valid for deletion
    def form_valid(self, form):
        """Handle delete for Django 4.0+ style DeleteView."""
        return self.delete(self.request)
