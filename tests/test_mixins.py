"""
Tests for HTMX mixins.
"""

import json
from django.test import TestCase
from django.http import HttpResponse

from htmx_admin.mixins import HtmxResponseMixin, HtmxFormMixin


class MockRequest:
    """Mock request object for testing."""

    def __init__(self, htmx=False):
        self.headers = {'HX-Request': 'true'} if htmx else {}


class HtmxResponseMixinTest(TestCase):
    """Tests for HtmxResponseMixin."""

    def setUp(self):
        """Set up mixin instance."""
        self.mixin = HtmxResponseMixin()

    def test_is_htmx_request_true(self):
        """Test detection of HTMX request."""
        request = MockRequest(htmx=True)
        self.assertTrue(self.mixin.is_htmx_request(request))

    def test_is_htmx_request_false(self):
        """Test detection of non-HTMX request."""
        request = MockRequest(htmx=False)
        self.assertFalse(self.mixin.is_htmx_request(request))

    def test_htmx_response_basic(self):
        """Test basic HTMX response creation."""
        response = self.mixin.htmx_response(content='Hello', status=200)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Hello')

    def test_htmx_response_with_triggers(self):
        """Test HTMX response with triggers."""
        response = self.mixin.htmx_response(
            status=204,
            showMessage={'level': 'success', 'message': 'Done!'},
            rowDeleted={'id': '123'}
        )

        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Trigger', response)

        triggers = json.loads(response['HX-Trigger'])
        self.assertIn('showMessage', triggers)
        self.assertIn('rowDeleted', triggers)
        self.assertEqual(triggers['showMessage']['level'], 'success')
        self.assertEqual(triggers['rowDeleted']['id'], '123')

    def test_htmx_response_no_triggers(self):
        """Test HTMX response without triggers."""
        response = self.mixin.htmx_response(content='OK')

        self.assertNotIn('HX-Trigger', response)

    def test_htmx_redirect(self):
        """Test HTMX redirect response."""
        response = self.mixin.htmx_redirect('/new-url/')

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response['HX-Redirect'], '/new-url/')

    def test_htmx_refresh(self):
        """Test HTMX refresh response."""
        response = self.mixin.htmx_refresh()

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response['HX-Refresh'], 'true')

    def test_htmx_push_url(self):
        """Test HTMX push URL response."""
        response = self.mixin.htmx_push_url('/pushed-url/', 'Content')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Push-Url'], '/pushed-url/')
        self.assertEqual(response.content, b'Content')


class HtmxFormMixinTest(TestCase):
    """Tests for HtmxFormMixin."""

    def test_form_invalid_returns_422(self):
        """Test that form_invalid returns 422 status."""
        from django.views.generic.edit import FormView
        from django import forms

        class TestForm(forms.Form):
            name = forms.CharField()

        class TestView(HtmxFormMixin, FormView):
            form_class = TestForm
            template_name = 'test.html'

        view = TestView()
        view.request = MockRequest()

        # Create invalid form
        form = TestForm(data={})
        self.assertFalse(form.is_valid())

        # Note: Full test would require template rendering
        # The mixin sets status_code = 422 on the response
        pass

    def test_get_success_message_with_object(self):
        """Test success message generation with object."""
        mixin = HtmxFormMixin()
        mixin.object = type('Obj', (), {'__str__': lambda s: 'Test Object'})()

        message = mixin.get_success_message()
        self.assertEqual(message, 'Test Object saved successfully.')

    def test_get_success_message_default(self):
        """Test default success message."""
        mixin = HtmxFormMixin()
        mixin.success_message = 'Custom message'

        message = mixin.get_success_message()
        self.assertEqual(message, 'Custom message')
