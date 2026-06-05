from django.contrib import admin

from .models import Entry, EntryImage, Event, Vote


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "created_by", "created_at"]
    list_filter = ["status"]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ["title", "event", "submitter_name", "created_at"]
    list_filter = ["event"]


@admin.register(EntryImage)
class EntryImageAdmin(admin.ModelAdmin):
    list_display = ["entry", "is_hero", "order"]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["user", "entry", "created_at"]
