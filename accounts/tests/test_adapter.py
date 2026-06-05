from unittest.mock import MagicMock

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.adapters import StrativOnlyAdapter


class StrativOnlyAdapterTests(TestCase):
    def _make_sociallogin(self, email):
        sociallogin = MagicMock()
        sociallogin.account.extra_data = {"email": email}
        return sociallogin

    def test_strativ_email_passes(self):
        adapter = StrativOnlyAdapter()
        sociallogin = self._make_sociallogin("alice@strativ.se")
        # Should not raise
        adapter.pre_social_login(request=MagicMock(), sociallogin=sociallogin)

    def test_non_strativ_email_raises(self):
        adapter = StrativOnlyAdapter()
        sociallogin = self._make_sociallogin("alice@gmail.com")
        with self.assertRaises(PermissionDenied):
            adapter.pre_social_login(request=MagicMock(), sociallogin=sociallogin)

    def test_empty_email_raises(self):
        adapter = StrativOnlyAdapter()
        sociallogin = self._make_sociallogin("")
        with self.assertRaises(PermissionDenied):
            adapter.pre_social_login(request=MagicMock(), sociallogin=sociallogin)

    def test_case_insensitive_domain(self):
        adapter = StrativOnlyAdapter()
        sociallogin = self._make_sociallogin("Alice@STRATIV.SE")
        # Should not raise — adapter lowercases before checking
        adapter.pre_social_login(request=MagicMock(), sociallogin=sociallogin)
