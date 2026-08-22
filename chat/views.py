from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST

from .models import DeviceSession, Message

DEVICE_COOKIE = "lschat_device"
ALLOWED_USERS = {"iaml": "iamL", "iams": "iamS"}
ALLOWED_USERNAMES = tuple(ALLOWED_USERS.values())
MAX_DEVICES = 2


def _device_token(request):
    return request.COOKIES.get(DEVICE_COOKIE)


def _set_device_cookie(response, token):
    response.set_cookie(
        DEVICE_COOKIE,
        token,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="Lax",
        secure=not settings.DEBUG,
    )
    return response


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = AuthenticationForm(request, data=request.POST or None)
    device_cookie = _device_token(request)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        username = user.username.casefold()

        if username not in ALLOWED_USERS:
            form.add_error(None, "Only the two LSChat accounts can sign in.")
            return render(request, "chat/login.html", {"form": form})

        own = DeviceSession.objects.filter(user=user).first()

        # Re-login from the already registered device is allowed.
        if own and device_cookie == own.device_token:
            login(request, user)
            own.session_key = request.session.session_key or ""
            own.save(update_fields=["session_key", "last_seen"])
            return _set_device_cookie(redirect("home"), own.device_token)

        # One device per account. Lalindar and Sandhiya can be active together.
        if own:
            form.add_error(None, "This account is already active on another device. Logout there first.")
            return render(request, "chat/login.html", {"form": form})

        # No third account/device slot.
        if DeviceSession.objects.count() >= MAX_DEVICES:
            form.add_error(None, "Both LSChat device slots are already in use.")
            return render(request, "chat/login.html", {"form": form})

        token = get_random_string(80)
        with transaction.atomic():
            DeviceSession.objects.create(
                user=user,
                device_token=token,
                session_key=request.session.session_key or "",
            )
        login(request, user)
        return _set_device_cookie(redirect("home"), token)

    return render(request, "chat/login.html", {"form": form})


@login_required
def logout_view(request):
    token = _device_token(request)
    DeviceSession.objects.filter(user=request.user, device_token=token).delete()
    logout(request)
    response = redirect("login")
    response.delete_cookie(DEVICE_COOKIE)
    return response


@login_required
@require_POST
def session_ping(request):
    token = _device_token(request)
    updated = DeviceSession.objects.filter(user=request.user, device_token=token).update(
        session_key=request.session.session_key or ""
    )
    if not updated:
        logout(request)
        return JsonResponse({"ok": False, "error": "device_session_invalid"}, status=403)
    return JsonResponse({"ok": True})


@login_required
def home(request):
    users = User.objects.filter(username__in=ALLOWED_USERNAMES).exclude(pk=request.user.pk).order_by("username")
    from .consumers import ONLINE_USERS
    return render(request, "chat/home.html", {"users": users, "online_ids": ONLINE_USERS})


@login_required
def chat_room(request, user_id):
    other = get_object_or_404(User, pk=user_id, username__in=ALLOWED_USERNAMES)
    if other == request.user:
        return redirect("home")
    # Disappearing-after-seen policy: a message is kept visible while the
    # chat is live. Once it has been seen, the next page refresh removes it.
    # This is deliberately done before loading the room so refresh is the
    # boundary for deletion rather than the moment the seen event arrives.
    Message.objects.filter(
        Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user),
        seen=True,
    ).delete()

    messages = list(
        Message.objects.filter(Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user))
        .select_related("sender", "receiver")
        .order_by("created_at", "id")
    )
    return render(request, "chat/room.html", {"other": other, "messages": messages})


@login_required
@require_POST
def upload_message(request, user_id):
    other = get_object_or_404(User, pk=user_id, username__in=ALLOWED_USERNAMES)
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "No file"}, status=400)

    ct = (f.content_type or "").lower()
    name = (f.name or "file").lower()
    if ct.startswith("image/"):
        kind = "image"
    elif ct.startswith("video/"):
        kind = "video"
    elif ct.startswith("audio/"):
        kind = "voice" if ct in {"audio/webm", "audio/ogg", "audio/mp4"} or "voice" in name else "audio"
    else:
        kind = "file"

    from .consumers import ONLINE_USERS
    msg = Message.objects.create(
        sender=request.user,
        receiver=other,
        message_type=kind,
        attachment=f,
        original_name=f.name,
        delivered=(other.id in ONLINE_USERS),
    )

    # IMPORTANT: upload and websocket broadcast happen in the same request.
    # This makes photo/video/audio/voice/document delivery live on both clients.
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    room = "chat_%s_%s" % tuple(sorted([request.user.id, other.id]))
    async_to_sync(get_channel_layer()).group_send(
        room,
        {"type": "message_event", "message": msg.as_dict()},
    )
    return JsonResponse(msg.as_dict())


@login_required
@require_POST
def message_state(request, user_id):
    """Small fallback endpoint used only when a browser temporarily loses WebSocket."""
    other = get_object_or_404(User, pk=user_id, username__in=ALLOWED_USERNAMES)
    try:
        after_id = int(request.POST.get("after_id", "0"))
    except ValueError:
        after_id = 0
    rows = Message.objects.filter(
        Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user),
        id__gt=after_id,
    ).order_by("id")[:100]
    return JsonResponse({"messages": [m.as_dict() for m in rows]})
