from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("account/avatar/", views.set_avatar, name="set_avatar"),
    # چت آنلاین عمومی
    path("livechat/widget/", views.livechat_widget, name="livechat_widget"),
    path("livechat/start/", views.livechat_start, name="livechat_start"),
    path("livechat/send/", views.livechat_send, name="livechat_send"),
    path("livechat/poll/", views.livechat_poll, name="livechat_poll"),
    path("livechat/close/", views.livechat_close_visitor, name="livechat_close"),
]
