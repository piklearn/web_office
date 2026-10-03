from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("account/avatar/", views.set_avatar, name="set_avatar"),
]
