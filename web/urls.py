from django.urls import path

from web.views import AppView

urlpatterns = [
    path("", AppView.as_view(), name="app_home"),
]
