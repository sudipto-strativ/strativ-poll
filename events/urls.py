from django.urls import path

from . import views

urlpatterns = [
    # Public / voter
    path("", views.home, name="home"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
    path("events/<int:event_id>/entries/<int:entry_id>/", views.entry_detail, name="entry_detail"),
    path("events/<int:event_id>/entries/<int:entry_id>/vote/", views.toggle_vote, name="toggle_vote"),

    # Admin (is_staff required)
    path("manage/", views.manage_event_list, name="manage_event_list"),
    path("manage/events/new/", views.manage_event_create, name="manage_event_create"),
    path("manage/events/<int:event_id>/", views.manage_event_detail, name="manage_event_detail"),
    path("manage/events/<int:event_id>/edit/", views.manage_event_edit, name="manage_event_edit"),
    path("manage/events/<int:event_id>/open/", views.manage_event_open, name="manage_event_open"),
    path("manage/events/<int:event_id>/close/", views.manage_event_close, name="manage_event_close"),
    path("manage/events/<int:event_id>/reopen/", views.manage_event_reopen, name="manage_event_reopen"),
    path("manage/events/<int:event_id>/delete/", views.manage_event_delete, name="manage_event_delete"),
    path("manage/events/<int:event_id>/entries/new/", views.manage_entry_create, name="manage_entry_create"),
    path("manage/events/<int:event_id>/entries/<int:entry_id>/edit/", views.manage_entry_edit, name="manage_entry_edit"),
    path("manage/events/<int:event_id>/entries/<int:entry_id>/delete/", views.manage_entry_delete, name="manage_entry_delete"),
]
