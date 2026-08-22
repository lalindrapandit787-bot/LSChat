import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ludochat.settings")
import django
django.setup()

from django.contrib.auth.models import User

USERS = [
    ("iamL", "panditlk123"),
    ("iamS", "sandhiya123"),
]

for username, password in USERS:
    u, created = User.objects.get_or_create(username=username)
    u.set_password(password)
    u.is_active = True
    u.save()
    print(("Created" if created else "Updated"), username)
