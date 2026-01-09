# eCitizen Voice Assistant API Documentation

## Overview

The Rafiki Government Voice Assistant API provides endpoints for voice-enabled access to Kenyan government services. This API is designed with accessibility in mind, enabling visually impaired users to interact with eCitizen services through voice commands.

**Base URL:** `http://localhost:8000/api/v1`

---

## Authentication

Currently, the API uses session-based authentication. Each client receives a unique session ID that must be included in subsequent requests.

### Create Session
```http
POST /session/create
```

**Response:**
```json
{
  "session_id": "uuid-v4-session-id",
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-15T11:00:00Z"
}
```

---

## Voice Endpoints

### Process Voice Input
```http
POST /voice/process
Content-Type: multipart/form-data
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| audio | file | Audio file (WAV, MP3, or WEBM) |
| session_id | string | User session ID |
| language | string | Language code (default: en-KE) |

**Response:**
```json
{
  "success": true,
  "transcript": "I want to apply for a passport",
  "intent": "passport_application",
  "response": "I'll help you apply for a passport. Do you need a new passport or renewal?",
  "audio_response_url": "/voice/audio/response-123.mp3"
}
```

### Get Text-to-Speech Audio
```http
GET /voice/speak
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| text | string | Text to convert to speech |
| language | string | Language code (default: en) |
| voice | string | Voice preference (optional) |

**Response:** Audio file (MP3)

### Stream Voice Response
```http
GET /voice/stream/{response_id}
```

**Response:** Server-Sent Events (SSE) stream with audio chunks

---

## Booking Endpoints

### Get Available Services
```http
GET /services
```

**Response:**
```json
{
  "services": [
    {
      "id": "passport",
      "name": "Passport Application",
      "description": "Apply for a new Kenyan passport or renew existing",
      "requirements": ["National ID", "2 passport photos", "Birth certificate"],
      "fee": 4550,
      "processing_time": "10 working days"
    },
    {
      "id": "national_id",
      "name": "National ID",
      "description": "Apply for or replace National ID",
      "requirements": ["Birth certificate", "School leaving certificate"],
      "fee": 0,
      "processing_time": "30 working days"
    }
  ]
}
```

### Get Service Details
```http
GET /services/{service_id}
```

**Response:**
```json
{
  "id": "passport",
  "name": "Passport Application",
  "description": "Apply for a new Kenyan passport or renew existing",
  "requirements": [
    "Original and copy of National ID",
    "2 passport-size photos (white background)",
    "Birth certificate (for new applications)",
    "Old passport (for renewals)"
  ],
  "fee": 4550,
  "processing_time": "10 working days",
  "locations": ["Nyayo House", "Huduma Centre GPO", "Huduma Centre Eastleigh"]
}
```

### Get Available Time Slots
```http
GET /booking/slots
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| service_id | string | Service identifier |
| date | string | Date (YYYY-MM-DD) |
| location | string | Location identifier |

**Response:**
```json
{
  "date": "2024-01-20",
  "location": "Huduma Centre GPO",
  "slots": [
    {"time": "08:00", "available": true},
    {"time": "08:30", "available": true},
    {"time": "09:00", "available": false},
    {"time": "09:30", "available": true}
  ]
}
```

### Create Booking
```http
POST /booking/create
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_id": "user-session-id",
  "service_id": "passport",
  "date": "2024-01-20",
  "time": "09:30",
  "location": "Huduma Centre GPO",
  "user_details": {
    "full_name": "John Doe",
    "phone_number": "+254712345678",
    "id_number": "12345678",
    "email": "john@example.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "booking": {
    "id": "booking-uuid",
    "reference_number": "ECZ-2024-001234",
    "service": "Passport Application",
    "date": "2024-01-20",
    "time": "09:30",
    "location": "Huduma Centre GPO",
    "status": "confirmed"
  },
  "sms_sent": true,
  "message": "Your appointment has been confirmed. An SMS has been sent to +254712345678"
}
```

### Get User Bookings
```http
GET /booking/user/{session_id}
```

**Response:**
```json
{
  "bookings": [
    {
      "id": "booking-uuid",
      "reference_number": "ECZ-2024-001234",
      "service_name": "Passport Application",
      "date": "2024-01-20",
      "time": "09:30",
      "location": "Huduma Centre GPO",
      "status": "confirmed",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Cancel Booking
```http
DELETE /booking/{booking_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Booking cancelled successfully",
  "sms_sent": true
}
```

### Confirm Booking
```http
POST /booking/{booking_id}/confirm
```

**Response:**
```json
{
  "success": true,
  "booking": {
    "id": "booking-uuid",
    "status": "confirmed"
  }
}
```

---

## Session Endpoints

### Get Session Info
```http
GET /session/{session_id}
```

**Response:**
```json
{
  "session_id": "uuid-v4-session-id",
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-15T11:00:00Z",
  "context": {
    "current_service": "passport",
    "booking_step": "select_date"
  }
}
```

### Update Session Context
```http
PUT /session/{session_id}/context
Content-Type: application/json
```

**Request Body:**
```json
{
  "current_service": "passport",
  "booking_step": "select_time",
  "selected_date": "2024-01-20"
}
```

### Delete Session
```http
DELETE /session/{session_id}
```

---

## Chat Endpoints

### Process Chat Message
```http
POST /chat/message
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_id": "user-session-id",
  "message": "I want to apply for a passport",
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "response": "I'll help you apply for a passport. You'll need your National ID, 2 passport photos, and birth certificate. Would you like to book an appointment?",
  "intent": "passport_application",
  "entities": {
    "service": "passport"
  },
  "suggested_actions": [
    {"label": "Book Appointment", "action": "book_appointment"},
    {"label": "View Requirements", "action": "view_requirements"},
    {"label": "Check Fees", "action": "check_fees"}
  ]
}
```

---

## Error Responses

All endpoints return errors in the following format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Phone number is required",
    "details": {
      "field": "phone_number",
      "constraint": "required"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid input data |
| UNAUTHORIZED | 401 | Invalid or expired session |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMITED | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | External service unavailable |

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **60 requests per minute** per session
- **1000 requests per hour** per IP address

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1705315800
```

---

## Webhooks

### SMS Delivery Status
Configure your Africa's Talking account to send delivery reports to:
```
POST /webhooks/sms/delivery
```

### Booking Reminders
The system automatically sends SMS reminders 24 hours before appointments.

---

## WebSocket Endpoints

### Real-time Voice Streaming
```
WS /ws/voice/{session_id}
```

**Message Types:**

**Client → Server:**
```json
{
  "type": "audio_chunk",
  "data": "base64-encoded-audio"
}
```

**Server → Client:**
```json
{
  "type": "transcript",
  "text": "I want to apply for a passport",
  "is_final": true
}
```

```json
{
  "type": "response",
  "text": "I'll help you with that.",
  "audio_url": "/voice/audio/response-123.mp3"
}
```

---

## SDK Examples

### Python
```python
import requests

# Create session
session = requests.post('http://localhost:8000/api/v1/session/create').json()
session_id = session['session_id']

# Send chat message
response = requests.post(
    'http://localhost:8000/api/v1/chat/message',
    json={
        'session_id': session_id,
        'message': 'I want to book a passport appointment'
    }
)
print(response.json()['response'])
```

### JavaScript
```javascript
// Create session
const session = await fetch('/api/v1/session/create', {
  method: 'POST'
}).then(r => r.json());

// Send chat message
const response = await fetch('/api/v1/chat/message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session.session_id,
    message: 'I want to book a passport appointment'
  })
}).then(r => r.json());

console.log(response.response);
```

---

## Avatar Animation Endpoints

The avatar animation system provides talking head videos with lip-sync, supporting multiple personalities for different interaction contexts.

### Get Current Personality
```http
GET /api/avatar/personality
```

**Response:**
```json
{
  "success": true,
  "personality": "friendly",
  "available_personalities": ["friendly", "professional", "excited", "calm"]
}
```

### Set Avatar Personality
```http
POST /api/avatar/personality
Content-Type: multipart/form-data
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| personality | string | One of: friendly, professional, excited, calm |

**Response:**
```json
{
  "success": true,
  "personality": "excited",
  "message": "Avatar personality set to 'excited'"
}
```

**Personality Descriptions:**
- `friendly`: Default, moderate expressions, natural head movement (expression_scale: 1.2)
- `professional`: Subdued expressions, minimal movement (expression_scale: 0.8)
- `excited`: Exaggerated expressions, active movement (expression_scale: 1.5)
- `calm`: Subtle expressions, stable pose (expression_scale: 0.6)

### Generate Video from Text
```http
POST /api/avatar/text-to-video
Content-Type: multipart/form-data
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| text | string | Text to speak (max 2000 chars) |
| avatar_id | string | Avatar identifier (default: rafiki_avatar) |
| language | string | Language code (default: en) |
| use_elevenlabs | boolean | Use ElevenLabs TTS (default: true) |
| personality | string | Avatar personality (default: friendly) |

**Response:**
- Success: Video file (video/mp4)
- Fallback: Audio file (audio/mpeg) with header `X-Fallback-Mode: audio-only`

**Example:**
```bash
curl -X POST http://localhost:8000/api/avatar/text-to-video \
  -F "text=Welcome! How can I help you today?" \
  -F "avatar_id=rafiki_avatar" \
  -F "personality=friendly" \
  -F "use_elevenlabs=true"
```

### Animate from Audio
```http
POST /api/avatar/animate
Content-Type: multipart/form-data
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| audio_file | file | Audio file (WAV, MP3, OGG, max 50MB) |
| avatar_id | string | Avatar identifier (default: habari) |
| preprocess | string | Preprocessing mode: crop, resize, full (default: crop) |
| still_mode | boolean | Only animate mouth, no head movement (default: false) |
| expression_scale | float | Expression intensity 0.0-2.0 (default: 1.0) |

**Response:**
- Video file (video/mp4)

**Example:**
```bash
curl -X POST http://localhost:8000/api/avatar/animate \
  -F "audio_file=@message.wav" \
  -F "avatar_id=rafiki_avatar" \
  -F "still_mode=false" \
  -F "expression_scale=1.2"
```

### Get Available Avatars
```http
GET /api/avatar/list
```

**Response:**
```json
{
  "avatars": [
    {
      "id": "rafiki_avatar",
      "name": "Rafiki Avatar",
      "path": "/backend/assets/avatars/rafiki_avatar.png"
    },
    {
      "id": "habari",
      "name": "Habari (Default)",
      "path": null
    }
  ]
}
```

### Health Check
```http
GET /api/avatar/health
```

**Response:**
```json
{
  "status": "healthy",
  "sadtalker_available": false,
  "mode": "api",
  "api_url": "http://localhost:7860"
}
```

---

## Avatar Personality System

The avatar supports 8 distinct personalities that control expression intensity, movement, and animation style. Personalities can be set globally or used for individual generations.

### Get All Personalities
```http
GET /api/avatar/personality
```

**Response:**
```json
{
  "success": true,
  "current_personality": "friendly",
  "personalities": {
    "friendly": {
      "name": "friendly",
      "description": "Warm and welcoming with moderate expressions",
      "expression_scale": 1.2,
      "still_mode": false
    },
    "professional": {
      "name": "professional",
      "description": "Composed and formal with minimal head movement",
      "expression_scale": 0.8,
      "still_mode": true
    },
    "excited": {
      "name": "excited",
      "description": "Energetic and enthusiastic with vivid expressions",
      "expression_scale": 1.5,
      "still_mode": false
    },
    "calm": {
      "name": "calm",
      "description": "Peaceful and soothing with gentle movements",
      "expression_scale": 0.6,
      "still_mode": true
    },
    "energetic": {
      "name": "energetic",
      "description": "Highly animated with dynamic expressions and movement",
      "expression_scale": 1.8,
      "still_mode": false
    },
    "empathetic": {
      "name": "empathetic",
      "description": "Compassionate and understanding with soft expressions",
      "expression_scale": 1.1,
      "still_mode": false
    },
    "humorous": {
      "name": "humorous",
      "description": "Playful and lighthearted with expressive animations",
      "expression_scale": 1.4,
      "still_mode": false
    },
    "serious": {
      "name": "serious",
      "description": "Focused and businesslike with controlled movements",
      "expression_scale": 0.7,
      "still_mode": true
    }
  }
}
```

### Set Personality
```http
POST /api/avatar/personality
Content-Type: multipart/form-data
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| personality | string | Personality name (friendly, professional, excited, calm, energetic, empathetic, humorous, serious) |

**Response:**
```json
{
  "success": true,
  "personality": "excited",
  "message": "Avatar personality set to 'excited'"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/avatar/personality \
  -F "personality=professional"
```

### Personality Usage

Personalities can be applied in two ways:

1. **Global Setting**: Use `/api/avatar/personality` to set the default personality for all subsequent generations
2. **Per-Generation**: Pass `personality` parameter to `/api/avatar/text-to-video` for one-time use

**Personality Characteristics:**

| Personality | Expression Scale | Still Mode | Best For |
|------------|-----------------|-----------|----------|
| Friendly | 1.2 | No | Customer service, greetings |
| Professional | 0.8 | Yes | Formal announcements, business |
| Excited | 1.5 | No | Promotions, celebrations |
| Calm | 0.6 | Yes | Instructions, meditation |
| Energetic | 1.8 | No | High-energy content, sports |
| Empathetic | 1.1 | No | Support, counseling |
| Humorous | 1.4 | No | Entertainment, jokes |
| Serious | 0.7 | Yes | Important news, warnings |

---

## Support

For API support, contact:
- Email: api-support@rafiki.co.ke
- Documentation: https://docs.rafiki.co.ke/api

