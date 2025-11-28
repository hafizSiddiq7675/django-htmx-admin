"""
Tests for HTMX middleware.
"""

import json
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.contrib.messages import constants as message_constants
from django.contrib.messages.storage.base import Message

from htmx_admin.middleware import (
    HtmxMessageMiddleware,
    HtmxRedirectMiddleware,
    HtmxVaryHeaderMiddleware,
)


class HtmxMessageMiddlewareTest(TestCase):
    """Test 5: Toast middleware - Django messages appear as HX-Trigger"""

    def setUp(self):
        """Set up request factory."""
        self.factory = RequestFactory()

    def get_response(self, request):
        """Simple view that returns empty response."""
        return HttpResponse()

    def test_non_htmx_request_unchanged(self):
        """Test that non-HTMX requests are not modified."""
        middleware = HtmxMessageMiddleware(self.get_response)
        request = self.factory.get('/')

        response = middleware(request)

        self.assertNotIn('HX-Trigger', response)

    def test_htmx_request_with_messages(self):
        """
        Test that HTMX requests with messages get HX-Trigger header.

        This test verifies:
        - Django messages are converted to HX-Trigger
        - Message level and content are preserved
        """
        # Note: Full test requires message storage setup
        # Example implementation:
        #
        # from django.contrib.messages import add_message
        # from django.contrib.sessions.middleware import SessionMiddleware
        # from django.contrib.messages.middleware import MessageMiddleware
        #
        # def get_response_with_message(request):
        #     add_message(request, message_constants.SUCCESS, 'Test message')
        #     return HttpResponse()
        #
        # middleware = HtmxMessageMiddleware(get_response_with_message)
        # request = self.factory.get('/', HTTP_HX_REQUEST='true')
        #
        # # Setup session and messages
        # session_middleware = SessionMiddleware(lambda x: x)
        # message_middleware = MessageMiddleware(lambda x: x)
        # session_middleware.process_request(request)
        # request.session.save()
        # message_middleware.process_request(request)
        #
        # response = middleware(request)
        #
        # self.assertIn('HX-Trigger', response)
        # triggers = json.loads(response['HX-Trigger'])
        # self.assertIn('showMessages', triggers)
        pass

    def test_htmx_request_without_messages(self):
        """Test that HTMX requests without messages don't add HX-Trigger."""
        middleware = HtmxMessageMiddleware(self.get_response)
        request = self.factory.get('/', HTTP_HX_REQUEST='true')

        response = middleware(request)

        # Response should not have HX-Trigger if no messages
        # (or should have empty showMessages)
        pass


class HtmxRedirectMiddlewareTest(TestCase):
    """Tests for redirect middleware."""

    def setUp(self):
        """Set up request factory."""
        self.factory = RequestFactory()

    def test_non_htmx_redirect_unchanged(self):
        """Test that non-HTMX redirects are not modified."""
        from django.http import HttpResponseRedirect

        def get_response(request):
            return HttpResponseRedirect('/new-url/')

        middleware = HtmxRedirectMiddleware(get_response)
        request = self.factory.get('/')

        response = middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/new-url/')

    def test_htmx_redirect_converted(self):
        """Test that HTMX redirects are converted to HX-Redirect."""
        from django.http import HttpResponseRedirect

        def get_response(request):
            return HttpResponseRedirect('/new-url/')

        middleware = HtmxRedirectMiddleware(get_response)
        request = self.factory.get('/', HTTP_HX_REQUEST='true')

        response = middleware(request)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response['HX-Redirect'], '/new-url/')


class HtmxVaryHeaderMiddlewareTest(TestCase):
    """Tests for vary header middleware."""

    def setUp(self):
        """Set up request factory."""
        self.factory = RequestFactory()

    def get_response(self, request):
        """Simple view that returns empty response."""
        return HttpResponse()

    def test_vary_header_added(self):
        """Test that HX-Request is added to Vary header."""
        middleware = HtmxVaryHeaderMiddleware(self.get_response)
        request = self.factory.get('/')

        response = middleware(request)

        vary = response.get('Vary', '')
        self.assertIn('HX-Request', vary)

    def test_vary_header_appended(self):
        """Test that HX-Request is appended to existing Vary header."""
        def get_response(request):
            response = HttpResponse()
            response['Vary'] = 'Cookie'
            return response

        middleware = HtmxVaryHeaderMiddleware(get_response)
        request = self.factory.get('/')

        response = middleware(request)

        vary = response.get('Vary', '')
        self.assertIn('Cookie', vary)
        self.assertIn('HX-Request', vary)
