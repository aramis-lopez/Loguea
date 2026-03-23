from django.urls import path

from accounts.views import HealthView, LoginView, RefreshTokenView

urlpatterns = [
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("health/", HealthView.as_view(), name="health"),
]
