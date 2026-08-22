from django.conf import settings
from django.db import models


class Message(models.Model):
    TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("file", "File"),
        ("voice", "Voice"),
        ("audio", "Audio"),
    ]
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_chat_messages")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_chat_messages")
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="text")
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to="chat_uploads/%Y/%m/", blank=True, null=True)
    original_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at", "id"]

    def as_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "type": self.message_type,
            "text": self.text,
            "url": self.attachment.url if self.attachment else "",
            "name": self.original_name,
            "time": self.created_at.strftime("%H:%M"),
            "delivered": self.delivered,
            "seen": self.seen,
        }


class DeviceSession(models.Model):
    """Exactly one persistent device slot per account."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_device_session",
    )
    device_token = models.CharField(max_length=96, unique=True)
    session_key = models.CharField(max_length=40, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
