from django.conf import settings
from django.db import models


class Event(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.title} ({self.status})"


class Entry(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="entries")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    submitter_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def hero(self):
        for img in self.images.all():
            if img.is_hero:
                return img
        return self.images.first()


class EntryImage(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="entries/%Y/%m/")
    is_hero = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image {self.id} for {self.entry}"


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "entry")]

    def __str__(self):
        return f"{self.user} → {self.entry}"
