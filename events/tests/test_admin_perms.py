from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class AdminPermTests(TestCase):
    def test_anonymous_manage_redirects_to_login(self):
        response = self.client.get(reverse("manage_event_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/", response["Location"])

    def test_non_staff_manage_returns_403(self):
        user = User.objects.create_user(email="voter@strativ.se", password="pass", is_staff=False)
        self.client.force_login(user)
        response = self.client.get(reverse("manage_event_list"))
        self.assertEqual(response.status_code, 403)

    def test_staff_manage_returns_200(self):
        staff = User.objects.create_user(email="admin@strativ.se", password="pass", is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("manage_event_list"))
        self.assertEqual(response.status_code, 200)
