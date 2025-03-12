from django.urls import path
from django.shortcuts import redirect
from .views import register_view, login_view, logout_view, dashboard_view, users_view, edit_profile_view, verify_email_view, send_test_email

urlpatterns = [
    path('', lambda request: redirect('login')),
    path("accounts/register/", register_view, name="register"),
    path("accounts/login/", login_view, name="login"),
    path("accounts/verify/<uidb64>/<token>/", verify_email_view, name="verify_email"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("users/", users_view, name="users"),
    path('edit-profile/', edit_profile_view, name='edit_profile'),
    # path('test-email/', send_test_email)
]
