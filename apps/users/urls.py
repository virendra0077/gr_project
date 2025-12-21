from django.urls import path
from apps.users import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("create_new/", views.user_create_view, name="user_create_new"),
]
