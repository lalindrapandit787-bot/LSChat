from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion
class Migration(migrations.Migration):
 initial=True
 dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
 operations=[migrations.CreateModel(name="Message",fields=[
 ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
 ("message_type",models.CharField(choices=[("text","Text"),("image","Image"),("file","File"),("voice","Voice")],default="text",max_length=10)),
 ("text",models.TextField(blank=True)),("attachment",models.FileField(blank=True,null=True,upload_to="chat_uploads/%Y/%m/")),
 ("original_name",models.CharField(blank=True,max_length=255)),("created_at",models.DateTimeField(auto_now_add=True)),
 ("delivered",models.BooleanField(default=False)),("seen",models.BooleanField(default=False)),
 ("receiver",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="received_chat_messages",to=settings.AUTH_USER_MODEL)),
 ("sender",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="sent_chat_messages",to=settings.AUTH_USER_MODEL))],options={"ordering":["created_at"]})]
