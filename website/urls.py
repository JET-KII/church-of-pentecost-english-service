from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("sermons/", views.sermons, name="sermons"),
    path("events/", views.events, name="events"),
    path("contact/", views.contact, name="contact"),
    path("accounts/signup/", views.signup, name="account_signup"),
    path(
        "accounts/login/",
        LoginView.as_view(
            template_name="website/accounts/login.html",
            authentication_form=LoginForm,
            extra_context={
                **views.build_base_context(),
                "page_title": "Log In | Church of Pentecost, New Kyekyere District English Service",
                "meta_description": "Log in to access the English Service member portal or staff dashboard.",
            },
        ),
        name="account_login",
    ),
    path("accounts/logout/", LogoutView.as_view(), name="account_logout"),
    path("accounts/verification-sent/", views.verification_sent, name="account_verification_sent"),
    path("accounts/verify/<uuid:token>/", views.verify_account, name="account_verify"),
    path("portal/", views.portal, name="portal"),
    path("portal/requests/<int:pk>/", views.portal_request_detail, name="portal_request_detail"),
    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("dashboard/requests/", views.dashboard_requests, name="dashboard_requests"),
    path("dashboard/requests/<int:pk>/", views.dashboard_request_detail, name="dashboard_request_detail"),
    path("dashboard/<slug:section>/", views.dashboard_section_list, name="dashboard_section"),
    path("dashboard/<slug:section>/new/", views.dashboard_section_create, name="dashboard_section_create"),
    path("dashboard/<slug:section>/<int:pk>/edit/", views.dashboard_section_edit, name="dashboard_section_edit"),
    path("dashboard/<slug:section>/<int:pk>/delete/", views.dashboard_section_delete, name="dashboard_section_delete"),
]
