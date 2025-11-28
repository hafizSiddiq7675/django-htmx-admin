"""
Toast message middleware for django-htmx-admin.

This middleware intercepts Django's messages framework and converts
messages to HTMX triggers for toast notifications.
"""

import json
from django.contrib import messages


class HtmxMessageMiddleware:
    """
    Convert Django messages to HTMX triggers.

    This middleware checks if the request is an HTMX request, and if so,
    converts any pending Django messages into HX-Trigger headers that
    can be handled by the frontend JavaScript.

    Installation:
        Add to MIDDLEWARE in settings.py:

        MIDDLEWARE = [
            ...
            'htmx_admin.middleware.HtmxMessageMiddleware',
            ...
        ]

    The middleware should be placed after Django's MessageMiddleware.
    """

    def __init__(self, get_response):
        """
        Initialize middleware.

        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process request and response.

        For HTMX requests, converts Django messages to HX-Trigger headers.

        Args:
            request: Django HTTP request

        Returns:
            HttpResponse, potentially with HX-Trigger header added
        """
        response = self.get_response(request)

        # Only process HTMX requests
        if not request.headers.get('HX-Request'):
            return response

        # Get any pending messages
        storage = messages.get_messages(request)
        if storage:
            message_list = []
            for message in storage:
                message_list.append({
                    'level': message.level_tag,
                    'message': str(message)
                })

            if message_list:
                # Merge with existing HX-Trigger
                existing = response.get('HX-Trigger', '{}')
                try:
                    triggers = json.loads(existing)
                except json.JSONDecodeError:
                    # If existing trigger is a simple string, convert to dict
                    if existing and existing != '{}':
                        triggers = {existing: True}
                    else:
                        triggers = {}

                triggers['showMessages'] = message_list
                response['HX-Trigger'] = json.dumps(triggers)

        return response


class HtmxRedirectMiddleware:
    """
    Handle redirects for HTMX requests.

    When a view returns a redirect response for an HTMX request,
    this middleware converts it to an HX-Redirect header response
    so HTMX can handle the redirect on the client side.

    Installation:
        Add to MIDDLEWARE in settings.py:

        MIDDLEWARE = [
            ...
            'htmx_admin.middleware.HtmxRedirectMiddleware',
            ...
        ]
    """

    def __init__(self, get_response):
        """
        Initialize middleware.

        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process request and response.

        For HTMX requests with redirect responses, converts to HX-Redirect.

        Args:
            request: Django HTTP request

        Returns:
            HttpResponse, potentially converted from redirect to HX-Redirect
        """
        from django.http import HttpResponse

        response = self.get_response(request)

        # Only process HTMX requests with redirect responses
        if not request.headers.get('HX-Request'):
            return response

        # Check if this is a redirect response (3xx status)
        if 300 <= response.status_code < 400:
            redirect_url = response.get('Location', '')
            if redirect_url:
                # Convert to HX-Redirect
                htmx_response = HttpResponse(status=204)
                htmx_response['HX-Redirect'] = redirect_url
                return htmx_response

        return response


class HtmxVaryHeaderMiddleware:
    """
    Add Vary header for HTMX requests.

    This middleware adds 'HX-Request' to the Vary header to ensure
    proper caching behavior when the same URL returns different
    content for HTMX vs non-HTMX requests.

    Installation:
        Add to MIDDLEWARE in settings.py:

        MIDDLEWARE = [
            ...
            'htmx_admin.middleware.HtmxVaryHeaderMiddleware',
            ...
        ]
    """

    def __init__(self, get_response):
        """
        Initialize middleware.

        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process request and response.

        Adds HX-Request to Vary header for proper caching.

        Args:
            request: Django HTTP request

        Returns:
            HttpResponse with updated Vary header
        """
        from django.utils.cache import patch_vary_headers

        response = self.get_response(request)

        # Add HX-Request to Vary header
        patch_vary_headers(response, ['HX-Request'])

        return response
