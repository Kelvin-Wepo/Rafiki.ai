# eCitizen Voice Assistant API Documentation

## Overview

The eCitizen Voice Assistant API provides endpoints for voice-enabled access to Kenyan government services. This API is designed with accessibility in mind, enabling visually impaired users to interact with eCitizen services through voice commands.

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

## Support

For API support, contact:
- Email: api-support@ecitizen.go.ke
- Documentation: https://docs.ecitizen.go.ke/api
