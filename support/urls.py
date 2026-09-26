from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    path("track/", views.track_result, name="track"),
    path("register/", views.register_case, name="register"),
]
