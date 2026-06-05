from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from events.models import Entry, Event, Vote
from events.templatetags.rank_extras import with_ranks


def make_user(email="voter@strativ.se"):
    return User.objects.create_user(email=email, password="pass")


def make_staff(email="admin@strativ.se"):
    return User.objects.create_user(email=email, password="pass", is_staff=True)


def make_event(creator, status=Event.STATUS_CLOSED):
    return Event.objects.create(title="Leaderboard Event", status=status, created_by=creator)


def make_entry(event, title="Entry", submitter="Alice"):
    return Entry.objects.create(event=event, title=title, submitter_name=submitter)


class RankFilterTests(TestCase):
    def test_no_ties(self):
        admin = make_staff()
        event = make_event(admin)
        users = [make_user(f"u{i}@strativ.se") for i in range(4)]
        entries = [make_entry(event, f"E{i}") for i in range(4)]
        # Give entries 4, 3, 2, 1 votes
        for i, entry in enumerate(entries):
            for u in users[: 4 - i]:
                Vote.objects.create(user=u, entry=entry)

        from django.db.models import Count
        qs = list(
            event.entries
            .annotate(vote_count=Count("votes"))
            .order_by("-vote_count", "created_at")
        )
        ranked = with_ranks(qs)
        self.assertEqual([e.rank for e in ranked], [1, 2, 3, 4])

    def test_ties_produce_competition_ranks(self):
        admin = make_staff()
        event = make_event(admin)
        u1 = make_user("u1@strativ.se")
        u2 = make_user("u2@strativ.se")
        entries = [make_entry(event, f"E{i}") for i in range(4)]
        # votes: 3, 2, 2, 1
        Vote.objects.create(user=u1, entry=entries[0])
        Vote.objects.create(user=u2, entry=entries[0])
        v3 = make_user("u3@strativ.se")
        Vote.objects.create(user=v3, entry=entries[0])
        Vote.objects.create(user=u1, entry=entries[1])
        Vote.objects.create(user=u2, entry=entries[1])
        Vote.objects.create(user=u1, entry=entries[2])
        Vote.objects.create(user=u2, entry=entries[2])
        Vote.objects.create(user=u1, entry=entries[3])

        from django.db.models import Count
        qs = list(
            event.entries
            .annotate(vote_count=Count("votes"))
            .order_by("-vote_count", "created_at")
        )
        ranked = with_ranks(qs)
        self.assertEqual([e.rank for e in ranked], [1, 2, 2, 4])

    def test_tie_breaker_earlier_created_at_first(self):
        admin = make_staff()
        event = make_event(admin)
        u1 = make_user("u1@strativ.se")
        e1 = make_entry(event, "Earlier")
        e2 = make_entry(event, "Later")
        Vote.objects.create(user=u1, entry=e1)
        Vote.objects.create(user=u1, entry=e2)
        # Both have 1 vote; e1 was created first

        from django.db.models import Count
        qs = list(
            event.entries
            .annotate(vote_count=Count("votes"))
            .order_by("-vote_count", "created_at")
        )
        self.assertEqual(qs[0].title, "Earlier")


class LeaderboardVisibilityTests(TestCase):
    def setUp(self):
        self.admin = make_staff()
        self.voter = make_user()

    def test_submitter_name_not_in_open_event_response(self):
        event = make_event(self.admin, status=Event.STATUS_OPEN)
        make_entry(event, submitter="SecretPerson")
        self.client.force_login(self.voter)
        response = self.client.get(reverse("event_detail", args=[event.id]))
        self.assertNotContains(response, "SecretPerson")

    def test_submitter_name_in_closed_event_response(self):
        event = make_event(self.admin, status=Event.STATUS_CLOSED)
        make_entry(event, submitter="RevealedPerson")
        self.client.force_login(self.voter)
        response = self.client.get(reverse("event_detail", args=[event.id]))
        self.assertContains(response, "RevealedPerson")
