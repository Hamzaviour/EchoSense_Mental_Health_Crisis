# Echo Sense API

Base URL: `http://localhost:5000`

## Auth

- `POST /api/auth/register` — Patient signup
- `POST /api/auth/login` — Returns JWT tokens
- `POST /api/auth/refresh` — Refresh access token
- `POST /api/auth/register-counselor` — Create counselor (demo)

## Patient

- `GET /api/patient/profile`
- `POST /api/patient/consent` — `{ consent, privacy_accepted }`

## Chat

- `GET /api/chat/greeting`
- `POST /api/chat/message` — `{ content }`
- `POST /api/chat/voice` — multipart `audio`
- `GET /api/chat/history`

## Assessments

- `GET /api/assessments/{PHQ9|GAD7|WHO5}`
- `POST /api/assessments/{type}/submit` — `{ responses: [{value}] }`

## Counselor

- `GET /api/counselor/queue`
- `GET /api/counselor/patients/:id`
- `POST /api/counselor/messages`
- `POST /api/counselor/copilot`
- `POST /api/counselor/triage`
- `GET /api/counselor/notifications`

## Escalations

- `GET /api/escalations`
- `GET /api/escalations/:id/pdf`

## Admin

- `GET /api/admin/analytics`
