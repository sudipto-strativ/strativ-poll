from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .models import Entry, Event, Vote


def home(request):
    if not request.user.is_authenticated:
        return render(request, "vote/home.html", {"unauthenticated": True})

    qs = Event.objects.all() if request.user.is_staff else Event.objects.exclude(status=Event.STATUS_DRAFT)
    open_events = qs.filter(status=Event.STATUS_OPEN)
    closed_events = qs.filter(status=Event.STATUS_CLOSED)
    draft_events = qs.filter(status=Event.STATUS_DRAFT) if request.user.is_staff else Event.objects.none()
    return render(request, "vote/home.html", {
        "open_events": open_events,
        "closed_events": closed_events,
        "draft_events": draft_events,
    })


def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if event.status == Event.STATUS_DRAFT:
        if not (request.user.is_authenticated and request.user.is_staff):
            raise Http404
        return redirect("manage_event_detail", event_id=event.id)

    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/events/{event_id}/")

    if event.status == Event.STATUS_OPEN:
        entries = list(event.entries.prefetch_related("images").order_by("created_at"))
        voted_ids = set(
            Vote.objects.filter(user=request.user, entry__event=event)
            .values_list("entry_id", flat=True)
        )
        for entry in entries:
            entry.has_voted = entry.id in voted_ids
        return render(request, "vote/voting.html", {
            "event": event,
            "entries": entries,
        })

    # STATUS_CLOSED
    entries = (
        event.entries
        .annotate(vote_count=Count("votes"))
        .order_by("-vote_count", "created_at")
        .prefetch_related("images")
    )
    return render(request, "vote/leaderboard.html", {"event": event, "entries": entries})


@login_required
def toggle_vote(request, event_id, entry_id):
    if request.method != "POST":
        return HttpResponseForbidden()

    event = get_object_or_404(Event, pk=event_id)
    if event.status != Event.STATUS_OPEN:
        return HttpResponseForbidden()

    entry = get_object_or_404(Entry, pk=entry_id, event=event)
    vote, created = Vote.objects.get_or_create(user=request.user, entry=entry)
    if not created:
        vote.delete()

    return render(request, "vote/_vote_button.html", {
        "event": event,
        "entry": entry,
        "has_voted": created,
    })


def _staff_check(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if not request.user.is_staff:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrapper


@_staff_check
def manage_event_list(request):
    events = Event.objects.select_related("created_by").order_by("-created_at")
    return render(request, "manage/event_list.html", {"events": events})


@_staff_check
def manage_event_create(request):
    from .forms import EventForm
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect("manage_event_detail", event_id=event.id)
    else:
        form = EventForm()
    return render(request, "manage/event_form.html", {"form": form, "action": "Create"})


@_staff_check
def manage_event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    entries = event.entries.prefetch_related("images").annotate(vote_count=Count("votes")).order_by("created_at")
    return render(request, "manage/event_detail.html", {"event": event, "entries": entries})


@_staff_check
def manage_event_edit(request, event_id):
    from .forms import EventForm
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect("manage_event_detail", event_id=event.id)
    else:
        form = EventForm(instance=event)
    return render(request, "manage/event_form.html", {"form": form, "event": event, "action": "Edit"})


@_staff_check
def manage_event_open(request, event_id):
    from django.utils import timezone
    event = get_object_or_404(Event, pk=event_id)
    if event.status != Event.STATUS_DRAFT:
        from django.contrib import messages
        messages.error(request, "Only draft events can be opened.")
        return redirect("manage_event_detail", event_id=event.id)
    if event.entries.count() == 0:
        from django.contrib import messages
        messages.error(request, "Add at least one entry before opening.")
        return redirect("manage_event_detail", event_id=event.id)
    event.status = Event.STATUS_OPEN
    event.opened_at = timezone.now()
    event.save()
    return redirect("manage_event_detail", event_id=event.id)


@_staff_check
def manage_event_close(request, event_id):
    from django.utils import timezone
    event = get_object_or_404(Event, pk=event_id)
    event.status = Event.STATUS_CLOSED
    event.closed_at = timezone.now()
    event.save()
    return redirect("manage_event_detail", event_id=event.id)


@_staff_check
def manage_event_reopen(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.status = Event.STATUS_OPEN
    event.closed_at = None
    event.save()
    return redirect("manage_event_detail", event_id=event.id)


@_staff_check
def manage_event_delete(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.delete()
    return redirect("manage_event_list")


@_staff_check
def manage_entry_create(request, event_id):
    from .forms import EntryForm
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        form = EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.event = event
            entry.save()
            files = request.FILES.getlist("images")
            from .models import EntryImage
            for i, f in enumerate(files):
                EntryImage.objects.create(entry=entry, image=f, is_hero=(i == 0), order=i)
            return redirect("manage_event_detail", event_id=event.id)
    else:
        form = EntryForm()
    return render(request, "manage/entry_form.html", {"form": form, "event": event, "action": "Add"})


@_staff_check
def manage_entry_edit(request, event_id, entry_id):
    from .forms import EntryForm
    from .models import EntryImage
    event = get_object_or_404(Event, pk=event_id)
    entry = get_object_or_404(Entry, pk=entry_id, event=event)
    if request.method == "POST":
        if "make_hero" in request.POST:
            image_id = request.POST["make_hero"]
            entry.images.update(is_hero=False)
            entry.images.filter(pk=image_id).update(is_hero=True)
            return redirect("manage_entry_edit", event_id=event.id, entry_id=entry.id)
        if "delete_image" in request.POST:
            entry.images.filter(pk=request.POST["delete_image"]).delete()
            return redirect("manage_entry_edit", event_id=event.id, entry_id=entry.id)
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            files = request.FILES.getlist("images")
            existing_count = entry.images.count()
            for i, f in enumerate(files):
                EntryImage.objects.create(entry=entry, image=f, is_hero=False, order=existing_count + i)
            return redirect("manage_event_detail", event_id=event.id)
    else:
        form = EntryForm(instance=entry)
    images = entry.images.all()
    return render(request, "manage/entry_form.html", {
        "form": form, "event": event, "entry": entry, "images": images, "action": "Edit",
    })


@login_required
def entry_detail(request, event_id, entry_id):
    event = get_object_or_404(Event, pk=event_id)
    if event.status == Event.STATUS_DRAFT and not request.user.is_staff:
        raise Http404
    entry = get_object_or_404(Entry, pk=entry_id, event=event)
    voters = (
        Vote.objects
        .filter(entry=entry)
        .select_related("user")
        .order_by("created_at")
    )
    return render(request, "manage/entry_detail.html", {
        "event": event,
        "entry": entry,
        "voters": voters,
    })


@_staff_check
def manage_entry_delete(request, event_id, entry_id):
    event = get_object_or_404(Event, pk=event_id)
    entry = get_object_or_404(Entry, pk=entry_id, event=event)
    entry.delete()
    return redirect("manage_event_detail", event_id=event.id)
