from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from events.models import Entry, Event, Vote


def make_user(email="voter@strativ.se", staff=False):
    return User.objects.create_user(email=email, password="pass", is_staff=staff)


def make_event(user, status=Event.STATUS_OPEN):
    return Event.objects.create(title="Test Event", status=status, created_by=user)


def make_entry(event, title="Entry 1"):
    return Entry.objects.create(event=event, title=title)


class ToggleVoteTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.admin = make_user("admin@strativ.se", staff=True)
        self.event = make_event(self.admin, status=Event.STATUS_OPEN)
        self.entry = make_entry(self.event)

    def _vote_url(self):
        return reverse("toggle_vote", args=[self.event.id, self.entry.id])

    def test_vote_creates_row(self):
        self.client.force_login(self.user)
        self.client.post(self._vote_url())
        self.assertEqual(Vote.objects.filter(user=self.user, entry=self.entry).count(), 1)

    def test_second_vote_deletes_row(self):
        self.client.force_login(self.user)
        self.client.post(self._vote_url())
        self.client.post(self._vote_url())
        self.assertEqual(Vote.objects.filter(user=self.user, entry=self.entry).count(), 0)

    def test_vote_on_draft_returns_403(self):
        self.client.force_login(self.user)
        draft_event = make_event(self.admin, status=Event.STATUS_DRAFT)
        entry = make_entry(draft_event)
        url = reverse("toggle_vote", args=[draft_event.id, entry.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_vote_on_closed_returns_403(self):
        self.client.force_login(self.user)
        self.event.status = Event.STATUS_CLOSED
        self.event.save()
        response = self.client.post(self._vote_url())
        self.assertEqual(response.status_code, 403)

    def test_unique_together_prevents_double_insert(self):
        Vote.objects.create(user=self.user, entry=self.entry)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Vote.objects.create(user=self.user, entry=self.entry)

    def test_anonymous_vote_redirects(self):
        response = self.client.post(self._vote_url())
        self.assertIn(response.status_code, [302, 403])
