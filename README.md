# LSChat Final v2.5

Private real-time two-account chat.

## Login
- `iamL` / `panditlk123`
- `iamS` / `sandhiya123`

## Important behavior
- One persistent device per account; both accounts can be active at the same time.
- No third device/account slot.
- Text, photo, camera image, video, audio, voice recording and documents are broadcast live over WebSocket.
- Messages are delivered without a browser refresh.
- Seen status is sent live as `✓✓`.
- A seen message is **not deleted immediately**. It stays visible during the current live session.
- When the chat page is refreshed/reopened, messages already marked seen are deleted before the room is rendered.
- Password field has an eye toggle on the login page.
- Cloudflared/HTTPS can be used for mobile camera and microphone permissions.

## Start
```powershell
python manage.py migrate
python create_demo_users.py
python -m daphne -b 127.0.0.1 -p 8000 ludochat.asgi:application
```
