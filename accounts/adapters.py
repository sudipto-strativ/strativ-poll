from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied


class StrativOnlyAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = (sociallogin.account.extra_data.get("email") or "").lower()
        if not email.endswith("@strativ.se"):
            raise PermissionDenied("Only @strativ.se accounts may sign in.")

    def is_auto_signup_allowed(self, request, sociallogin):
        # Domain check already enforced in pre_social_login; always auto-create the account.
        return True
