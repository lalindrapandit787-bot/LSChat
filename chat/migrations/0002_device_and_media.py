from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("chat", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="message_type",
            field=models.CharField(
                choices=[
                    ("text", "Text"), ("image", "Image"), ("video", "Video"),
                    ("file", "File"), ("voice", "Voice"), ("audio", "Audio"),
                ],
                default="text",
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name="DeviceSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("device_token", models.CharField(max_length=96, unique=True)),
                ("session_key", models.CharField(blank=True, max_length=40)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="chat_device_session", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
