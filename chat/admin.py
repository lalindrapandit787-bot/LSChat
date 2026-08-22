from django.contrib import admin
from .models import DeviceSession, Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "receiver", "message_type", "delivered", "seen", "created_at")
    list_filter = ("message_type", "delivered", "seen")
    search_fields = ("sender__username", "receiver__username", "text", "original_name")

@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "device_token", "session_key", "created_at", "last_seen")
    search_fields = ("user__username", "session_key", "device_token")
