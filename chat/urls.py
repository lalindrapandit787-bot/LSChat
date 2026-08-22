from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("session/ping/", views.session_ping, name="session_ping"),
    path("", views.home, name="home"),
    path("chat/<int:user_id>/", views.chat_room, name="chat_room"),
    path("chat/<int:user_id>/upload/", views.upload_message, name="upload_message"),
    path("chat/<int:user_id>/state/", views.message_state, name="message_state"),
]
