from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="analytics-dashboard"),
    path("users/", views.users_analytics, name="analytics-users"),
    path("resumes/", views.resumes_analytics, name="analytics-resumes"),
    path("subscriptions/", views.subscriptions_analytics, name="analytics-subscriptions"),
    path("credits/", views.credits_analytics, name="analytics-credits"),
    path("vacancies/", views.vacancies_analytics, name="analytics-vacancies"),
    path("referrals/", views.referrals_analytics, name="analytics-referrals"),
    path("api-usage/", views.api_usage, name="analytics-api-usage"),
    path("health/", views.health, name="analytics-health"),
    path("track-event/", views.track_event, name="analytics-track-event"),
    path("user-events/", views.user_events_analytics, name="analytics-user-events"),
    path("active-users/", views.active_users_analytics, name="analytics-active-users"),
]
