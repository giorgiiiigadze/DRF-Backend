# Live Caption API

A Django REST Framework backend for a macOS app that captures audio and sends transcript text for persistence and summarization. Audio capture and speech-to-text are deliberately outside this service.

## Setup

Requires Python 3.9+. On macOS, use a Homebrew Python rather than the Xcode-supplied `/usr/bin/python3`, which is linked with an older LibreSSL build.

```bash
brew install python@3.12
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Export the variables from `.env` with your preferred environment loader, or set them in your shell. `OPENAI_API_KEY` and `OPENAI_MODEL` are required only when creating a summary. Never commit `.env`.

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o-mini"
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/api/`. Create an admin user with `python manage.py createsuperuser` and visit `/admin/` to manage data.

## Endpoints

All endpoints except registration and login require `Authorization: Bearer <access-token>`.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register/` | Create an account |
| POST | `/api/auth/login/` | Obtain access and refresh JWTs |
| POST | `/api/auth/token/refresh/` | Refresh an access JWT |
| POST | `/api/auth/google/` | Exchange a verified Google ID token for application JWTs |
| POST | `/api/auth/apple/` | Exchange a verified Apple identity token for application JWTs |
| GET, POST | `/api/sessions/` | List or create the current user's sessions |
| GET, PATCH | `/api/sessions/{id}/` | Read or update one session with segments and summaries |
| POST | `/api/sessions/{id}/segments/` | Add transcript text |
| GET, POST | `/api/sessions/{id}/summary/` | Read summaries or generate one |
| GET, PUT, PATCH | `/api/preferences/` | Read or update current-user preferences |

Sessions and their transcript segments/summaries are scoped to their owner; another user receives `404` for an inaccessible session.

## Google and Apple sign-in

The native macOS app completes the provider sign-in flow, then posts the returned provider token to this backend. The backend verifies the token and returns the same access/refresh JWT format as password login.

```json
POST /api/auth/google/
{"id_token":"GOOGLE_ID_TOKEN"}

POST /api/auth/apple/
{"identity_token":"APPLE_IDENTITY_TOKEN"}
```

Set `GOOGLE_OAUTH_CLIENT_ID` to the Google OAuth client ID used by the macOS app. Set `APPLE_CLIENT_ID` to the registered Apple bundle ID for native app sign-in, or the Services ID when using a web/server callback. Provider secrets and Apple private keys are not stored by this backend in the native-token flow.

Sessions, transcript segments, summaries, and preferences include audit timestamps. Sessions also have an `active`/`completed` status and an `ended_at` timestamp, which is automatically set when a session is marked completed with `PATCH /api/sessions/{id}/`.

## Example requests

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alex","password":"secure-password-123","email":"alex@example.com"}'

curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alex","password":"secure-password-123"}'

curl -X POST http://127.0.0.1:8000/api/sessions/ \
  -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' \
  -d '{"title":"Design review","language":"en"}'

curl -X POST http://127.0.0.1:8000/api/sessions/1/segments/ \
  -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' \
  -d '{"text":"We agreed to ship on Friday.","timestamp":12.4,"speaker_label":"Alex"}'

curl -X POST http://127.0.0.1:8000/api/sessions/1/summary/ \
  -H 'Authorization: Bearer ACCESS_TOKEN'
```

## Tests

```bash
.venv/bin/python manage.py test
```

`api.services.Summarizer` isolates the OpenAI SDK integration. Replace that class with a local PyTorch-backed implementation later without changing any endpoint or view.
