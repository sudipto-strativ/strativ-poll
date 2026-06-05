from django import forms

from .models import Entry, Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description"]


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ["title", "description", "submitter_name"]
