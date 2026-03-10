# Complete API Reference - Rafiki.ai Render Deployment

## Table of Contents
1. [Third-Party External APIs](#third-party-external-apis)
2. [Backend Internal APIs](#backend-internal-apis)
3. [Frontend Integration Points](#frontend-integration-points)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Checklist](#deployment-checklist)

---

## THIRD-PARTY EXTERNAL APIs

### 1. Google Gemini API
**Purpose:** Natural Language Understanding & AI Responses

**API Details:**
- **Service:** `generativeai.googleapis.com`
- **Auth Method:** API Key
- **Environment Variable:** `GEMINI_API_KEY`
- **Model:** `gemini-2.5-flash` (configurable)

**Endpoints Used:**
```
POST https://generativeai.googleapis.com/v1beta/models/{model}:generateContent
Authorization: Bearer {GEMINI_API_KEY}

Request:
{
  "contents": [
    {
      "parts": [
        {
          "text": "What government services can you help me with?"
        }
      ]
    }
  ]
}

Response:
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "I can help you with passport application, national ID, driving license, etc."
          }
        ]
      }
    }
  ]
}
```

**Backend Integration:** [backend/services/gemini_service.py](backend/services/gemini_service.py)

---

### 2. Google Dialogflow API
**Purpose:** Intent Detection & Conversation Flow

**API Details:**
- **Service:** `dialogflow.googleapis.com`
- **Auth Method:** Google Cloud Service Account JSON
- **Environment Variable:** `GOOGLE_APPLICATION_CREDENTIALS`
- **Project ID:** `DIALOGFLOW_PROJECT_ID`
- **Language:** `en` (configured via `DIALOGFLOW_LANGUAGE_CODE`)

**Endpoints Used:**
```
POST https://dialogflow.googleapis.com/v2/projects/{projectId}/agent/sessions/{sessionId}:detectIntent
Authorization: Bearer {service_account_token}

Request:
{
  "queryInput": {
    "text": {
      "text": "I want to check my driving license",
      "languageCode": "en"
    }
  }
}

Response:
{
  "responseId": "abc123...",
  "queryResult": {
    "queryText": "I want to check my driving license",
    "intent": {
      "name": "projects/{projectId}/agent/intents/driving_license_check",
      "displayName": "Check Driving License"
    },
    "intentDetectionConfidence": 0.95,
    "fulfillmentText": "I can help you check your driving license status..."
  }
}
```

**Backend Integration:** [backend/services/dialogflow_service.py](backend/services/dialogflow_service.py)

---

### 3. Google Cloud Text-to-Speech API
**Purpose:** Convert Text to Natural Speech Audio

**API Details:**
- **Service:** `texttospeech.googleapis.com`
- **Auth Method:** Google Cloud API Key or Service Account
- **Environment Variable:** `GOOGLE_API_KEY` or service account JSON

**Endpoints Used:**
```
POST https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_API_KEY}

Request:
{
  "input": {
    "text": "Your appointment is confirmed for tomorrow at 2 PM"
  },
  "voice": {
    "languageCode": "en-KE",
    "name": "en-KE-Standard-A"
  },
  "audioConfig": {
    "audioEncoding": "MP3",
    "pitch": 0.0,
    "speakingRate": 1.0
  }
}

Response:
{
  "audioContent": "base64_encoded_mp3_audio..."
}
```

**Backend Integration:** [backend/services/google_tts_service.py](backend/services/google_tts_service.py)

---

### 4. ElevenLabs Conversational AI API
**Purpose:** Real-time Voice Conversations & TTS with Natural Voices

**API Details:**
- **Service:** `api.elevenlabs.io`
- **Auth Method:** API Key (Header)
- **API Key:** `ELEVENLABS_API_KEY`
- **Agent ID:** `ELEVENLABS_AGENT_ID`
- **Branch ID:** `ELEVENLABS_BRANCH_ID`
- **Voice ID:** `ELEVENLABS_VOICE_ID` (Default: Rachel - `21m00Tcm4TlvDq8ikWAM`)

**Endpoints Used:**

#### Get Signed WebSocket URL
```
GET https://api.elevenlabs.io/v1/convai/conversation/get_signed_url?agent_id={AGENT_ID}
Authorization: Bearer {ELEVENLABS_API_KEY}

Response:
{
  "signed_url": "wss://...signed websocket url..."
}
```

#### Text-to-Speech
```
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream
Authorization: Bearer {ELEVENLABS_API_KEY}

Request:
{
  "text": "Let me help you with your passport application",
  "model_id": "eleven_turbo_v2_5",
  "optimize_streaming_latency": 3
}

Response:
Audio stream (MP3)
```

**Backend Integration:** [backend/services/elevenlabs_service.py](backend/services/elevenlabs_service.py)

**Frontend Integration:** Real-time WebSocket connection for voice conversations

---

### 5. Africa's Talking SMS API
**Purpose:** Send SMS Notifications (OTP, Confirmations, Reminders)

**API Details:**
- **Service:** `api.sandbox.africastalking.com` (testing) / `api.africastalking.com` (production)
- **Auth Method:** Username & API Key
- **Username:** `AFRICASTALKING_USERNAME`
- **API Key:** `AFRICASTALKING_API_KEY`
- **Sender ID:** `AFRICASTALKING_SENDER_ID`

**Endpoints Used:**

#### Send SMS
```
POST https://api.sandbox.africastalking.com/version1/messaging

Headers:
Accept: application/json
Content-Type: application/x-www-form-urlencoded
ApiKey: {AFRICASTALKING_API_KEY}

Body:
username={AFRICASTALKING_USERNAME}
message=Your appointment is confirmed for Dec 15, 2024 at 2:00 PM. Reference: AP001
recipients=%2B254712345678

Response:
{
  "SMSMessageData": {
    "Message": "Sent to 1/1 Valid Message.",
    "Recipients": [
      {
        "statusCode": 101,
        "number": "+254712345678",
        "status": "Success",
        "cost": "KES 0.80",
        "messageId": "ATXid_..."
      }
    ]
  }
}
```

**Backend Integration:** [backend/services/sms_service.py](backend/services/sms_service.py)

**Use Cases:**
- Appointment confirmations
- OTP verification
- Appointment reminders (24 hours before)
- Payment confirmations

---

### 6. Paystack API (M-PESA Payments)
**Purpose:** Process Mobile Money Payments via M-PESA

**API Details:**
- **Service:** `api.paystack.co`
- **Auth Method:** Secret Key (Authorization Header)
- **Secret Key:** `PAYSTACK_SECRET_KEY`
- **Currency:** KES (Kenyan Shilling)
- **Provider:** mpesa

**Endpoints Used:**

#### Initialize Payment / STK Push
```
POST https://api.paystack.co/charge

Headers:
Authorization: Bearer {PAYSTACK_SECRET_KEY}
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "amount": 500000,
  "phone_number": "254712345678",
  "reference": "PAY-20240315-001",
  "currency": "KES",
  "metadata": {
    "service": "passport_application",
    "booking_id": "BOOK-001"
  }
}

Response:
{
  "status": true,
  "message": "Charge initiated",
  "data": {
    "reference": "PAY-20240315-001",
    "amount": 500000,
    "currency": "KES",
    "status": "pending"
  }
}
```

#### Verify Payment
```
GET https://api.paystack.co/transaction/verify/{reference}?reference={reference}

Headers:
Authorization: Bearer {PAYSTACK_SECRET_KEY}

Response:
{
  "status": true,
  "message": "Authorization URL created",
  "data": {
    "amount": 500000,
    "currency": "KES",
    "reference": "PAY-20240315-001",
    "status": "success",
    "paid_at": "2024-03-15T14:30:00.000Z"
  }
}
```

**Backend Integration:** [backend/services/paystack_service.py](backend/services/paystack_service.py)

---

### 7. Google Maps API
**Purpose:** Huduma Centre Location & Directions

**API Details:**
- **Service:** `maps.googleapis.com`
- **Auth Method:** API Key
- **API Key:** `GOOGLE_MAPS_API_KEY`
- **Fallback:** Static data available if API unavailable

**Endpoints Used:**

#### Find Nearby Places
```
GET https://maps.googleapis.com/maps/api/place/nearbysearch/json?key={GOOGLE_MAPS_API_KEY}&location={latitude},{longitude}&radius=50000&keyword=huduma

Response:
{
  "results": [
    {
      "name": "Huduma Centre GPO",
      "vicinity": "Kenyatta Avenue, Nairobi",
      "geometry": {
        "location": {
          "lat": -1.2833,
          "lng": 36.8167
        }
      },
      "formatted_address": "GPO Building, Kenyatta Avenue, Nairobi"
    }
  ]
}
```

#### Get Directions
```
GET https://maps.googleapis.com/maps/api/directions/json?key={GOOGLE_MAPS_API_KEY}&origin={origin}&destination={destination}&mode=driving

Response:
{
  "routes": [
    {
      "distance": {
        "text": "15.2 km",
        "value": 15200
      },
      "duration": {
        "text": "35 mins",
        "value": 2100
      },
      "legs": [...directions steps...]
    }
  ]
}
```

**Backend Integration:** [backend/services/maps_service.py](backend/services/maps_service.py)

---

### 8. KRA (Kenya Revenue Authority) API (OPTIONAL)
**Purpose:** Tax Services - PIN Verification, Compliance Checks

**API Details:**
- **Service:** `itax.kra.go.ke/api`
- **Auth Method:** OAuth2 (Client ID & Secret)
- **API URL:** `KRA_API_URL`
- **Client ID:** `KRA_CLIENT_ID`
- **Client Secret:** `KRA_CLIENT_SECRET`
- **Status:** Optional - set `KRA_ENABLED=true` to activate

**Endpoints Exposed via Backend:**
```
POST /kra/verify-pin
{
  "pin": "A123456789B"
}

Response:
{
  "success": true,
  "pin_valid": true,
  "taxpayer_name": "John Doe",
  "status": "Active"
}

---

POST /kra/compliance-check
{
  "pin": "A123456789B"
}

Response:
{
  "success": true,
  "compliant": true,
  "status": "Compliant",
  "last_filing": "2024-01-15"
}

---

POST /kra/request-compliance-certificate
{
  "pin": "A123456789B",
  "email": "taxpayer@example.com"
}

Response:
{
  "success": true,
  "request_id": "CC-2024-12345",
  "status": "Pending",
  "estimated_time": "2-5 business days"
}

---

GET /kra/status
Response:
{
  "enabled": true,
  "initialized": true,
  "api_url": "https://itax.kra.go.ke/api",
  "message": "KRA service is operational"
}
```

**Backend Integration:** [backend/services/agency_workflows.py](backend/services/agency_workflows.py)

---

## BACKEND INTERNAL APIs

### Authentication Endpoints
**Base URL:** `http://localhost:8000` (or your Render domain)

#### 1. Sign Up
```
POST /auth/signup
Content-Type: application/json

Request:
{
  "phone": "+254712345678",
  "password": "secure_password"
}

Response:
{
  "success": true,
  "user_id": "user_abc123",
  "phone_masked": "+254712***678",
  "otp_sent": true,
  "message": "OTP sent to your phone"
}
```

#### 2. Verify OTP
```
POST /auth/verify-otp
Content-Type: application/json

Request:
{
  "phone": "+254712345678",
  "otp": "123456"
}

Response:
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "user_abc123",
    "phone_masked": "+254712***678",
    "status": "verified"
  }
}
```

#### 3. Login
```
POST /auth/login
Content-Type: application/json

Request:
{
  "phone": "+254712345678",
  "password": "secure_password"
}

Response:
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 4. Refresh Token
```
POST /auth/refresh-token
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "access_token": "new_token...",
  "expires_in": 3600
}
```

---

### Voice Processing Endpoints

#### 1. Process Voice Input
```
POST /voice/process
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

Form Data:
- audio_file: [WAV/MP3 file]
- language: "en-KE"
- session_id: "session_abc123"

Response:
{
  "success": true,
  "transcript": "I want to apply for a passport",
  "intent": "passport_application",
  "response": "I can help you apply for a passport. Let me guide you through the process...",
  "confidence": 0.95,
  "session_id": "session_abc123"
}
```

#### 2. Text-to-Speech
```
POST /voice/text-to-speech
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "text": "Your appointment is confirmed for tomorrow at 2 PM",
  "language": "en-KE",
  "voice_id": "21m00Tcm4TlvDq8ikWAM"
}

Response:
{
  "success": true,
  "audio_url": "https://your-domain.com/audio/tts_12345.mp3",
  "duration_seconds": 3.5
}
```

#### 3. Voice Health Check
```
GET /voice/health
Authorization: Bearer {access_token}

Response:
{
  "status": "healthy",
  "speech_recognition": "operational",
  "text_to_speech": "operational",
  "version": "1.0.0"
}
```

---

### Session Management Endpoints

#### 1. Create Session
```
POST /session/create
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "user_id": "user_abc123",
  "language": "en"
}

Response:
{
  "success": true,
  "session_id": "session_xyz789",
  "created_at": "2024-03-15T10:30:00Z",
  "expires_at": "2024-03-15T11:30:00Z"
}
```

#### 2. Get Session Details
```
GET /session/{session_id}
Authorization: Bearer {access_token}

Response:
{
  "session_id": "session_xyz789",
  "user_id": "user_abc123",
  "status": "active",
  "created_at": "2024-03-15T10:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "I want to apply for a passport",
      "timestamp": "2024-03-15T10:31:00Z"
    },
    {
      "role": "assistant",
      "content": "I can help you with that...",
      "timestamp": "2024-03-15T10:31:05Z"
    }
  ]
}
```

#### 3. End Session
```
DELETE /session/{session_id}
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "message": "Session terminated"
}
```

---

### Services & Booking Endpoints

#### 1. Get All Services
```
GET /services
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "services": [
    {
      "id": "passport_new",
      "name": "Passport Application",
      "description": "Apply for a new Kenyan passport",
      "agency": "DCRS",
      "fee": 4550,
      "processing_time": "10 working days",
      "requirements": [
        "Valid National ID",
        "3 Passport-size photos",
        "Birth certificate"
      ]
    },
    {
      "id": "driving_license_renewal",
      "name": "Driving License Renewal",
      "description": "Renew your Kenyan driving license",
      "agency": "NTSA",
      "fee": 3000,
      "processing_time": "7 working days"
    }
  ]
}
```

#### 2. Get Service Details
```
GET /services/{service_id}
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "service": {
    "id": "passport_new",
    "name": "Passport Application",
    "description": "Apply for a new Kenyan passport",
    "agency": "DCRS",
    "fee": 4550,
    "processing_time": "10 working days",
    "locations": [
      "Nyayo House, Nairobi",
      "Huduma Centre GPO",
      "County Offices"
    ],
    "availability": {
      "monday": "08:00-17:00",
      "tuesday": "08:00-17:00",
      "wednesday": "08:00-17:00",
      "thursday": "08:00-17:00",
      "friday": "08:00-17:00",
      "saturday": "closed",
      "sunday": "closed"
    }
  }
}
```

#### 3. Create Booking
```
POST /booking/create
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "service_id": "passport_new",
  "date": "2024-03-25",
  "time_slot": "14:00",
  "location": "Huduma Centre GPO",
  "user_name": "John Doe",
  "email": "john@example.com",
  "phone": "+254712345678"
}

Response:
{
  "success": true,
  "booking": {
    "booking_id": "BOOK-20240315-001",
    "service_id": "passport_new",
    "date": "2024-03-25",
    "time_slot": "14:00",
    "status": "confirmed",
    "confirmation_code": "ABC123DEF456",
    "created_at": "2024-03-15T10:35:00Z"
  },
  "payment_required": {
    "amount": 4550,
    "currency": "KES",
    "payment_ref": "PAY-20240315-001"
  }
}
```

#### 4. Get Available Time Slots
```
GET /booking/slots?service_id={service_id}&date={YYYY-MM-DD}
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "date": "2024-03-25",
  "available_slots": [
    "08:00",
    "08:30",
    "09:00",
    "09:30",
    "14:00",
    "14:30",
    "15:00"
  ]
}
```

#### 5. Get Booking Details
```
GET /booking/{booking_id}
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "booking": {
    "booking_id": "BOOK-20240315-001",
    "service_id": "passport_new",
    "service_name": "Passport Application",
    "date": "2024-03-25",
    "time_slot": "14:00",
    "location": "Huduma Centre GPO",
    "status": "confirmed",
    "payment_status": "paid",
    "confirmation_code": "ABC123DEF456",
    "created_at": "2024-03-15T10:35:00Z"
  }
}
```

#### 6. Cancel Booking
```
DELETE /booking/{booking_id}
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "message": "Booking cancelled successfully",
  "cancellation_id": "CANCEL-20240315-001"
}
```

---

### Avatar Animation Endpoints

#### 1. List Avatars
```
GET /api/avatar/avatars
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "avatars": [
    {
      "id": "rafiki_avatar",
      "name": "Rafiki Avatar",
      "description": "Official Rafiki mascot avatar",
      "image_url": "https://your-domain.com/avatars/rafiki.png"
    },
    {
      "id": "professional_avatar",
      "name": "Professional Avatar",
      "description": "Professional government assistant"
    }
  ]
}
```

#### 2. Generate Talking Video from Audio
```
POST /api/avatar/generate-talking-video
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

Form Data:
- audio: [WAV/MP3 file, max 50MB]
- avatar_id: "rafiki_avatar"
- language: "en-KE"
- preprocess: "crop" (crop, resize, or full)
- still_mode: false (only animate mouth if true)
- expression_scale: 1.0 (0.0-2.0)

Response:
{
  "success": true,
  "video_id": "VID-20240315-001",
  "video_url": "https://your-domain.com/videos/avatar_20240315_001.mp4",
  "duration_seconds": 15.3,
  "created_at": "2024-03-15T10:40:00Z"
}
```

#### 3. Text-to-Video (Text + Avatar)
```
POST /api/avatar/text-to-video
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "text": "Welcome to the eCitizen platform. I am your voice assistant.",
  "avatar_id": "rafiki_avatar",
  "language": "en-KE",
  "use_elevenlabs": true,
  "voice_id": "21m00Tcm4TlvDq8ikWAM"
}

Response:
{
  "success": true,
  "video_id": "VID-20240315-002",
  "video_url": "https://your-domain.com/videos/avatar_20240315_002.mp4",
  "duration_seconds": 8.5,
  "audio_url": "https://your-domain.com/audio/tts_20240315_001.mp3"
}
```

#### 4. Avatar Health Check
```
GET /api/avatar/health
Authorization: Bearer {access_token}

Response:
{
  "status": "healthy",
  "avatars_available": 2,
  "video_generation": "operational",
  "gpu_available": true,
  "average_generation_time": 45.3
}
```

---

### Agencies (Workflows) Endpoints

#### 1. Agency Chat
```
POST /api/agencies/chat
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "session_id": "agency_session_123",
  "message": "I want to apply for a good conduct certificate",
  "agency": null  # null first, then specific agency like "DCI"
}

Response:
{
  "session_id": "agency_session_123",
  "response": "Welcome to DCI. I can help you apply for a Good Conduct Certificate. What is your full name?",
  "step": "collect_name",
  "agency": "DCI",
  "service": "good_conduct_cert",
  "awaiting_payment": false,
  "payment_amount": null
}
```

#### 2. Initiate Payment
```
POST /api/agencies/pay
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "session_id": "agency_session_123",
  "phone": "+254712345678",
  "amount_ksh": 1000,
  "service": "good_conduct_cert",
  "email": "user@example.com"
}

Response:
{
  "success": true,
  "reference": "PAY-20240315-001",
  "amount": 1000,
  "currency": "KES",
  "status": "pending",
  "message": "STK push sent to your phone. Enter your M-PESA PIN to complete payment."
}
```

#### 3. Verify Payment
```
POST /api/agencies/verify-payment
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "session_id": "agency_session_123",
  "reference": "PAY-20240315-001"
}

Response:
{
  "success": true,
  "payment_status": "paid",
  "reference": "PAY-20240315-001",
  "amount": 1000,
  "paid_at": "2024-03-15T10:45:00Z"
}
```

#### 4. Get Available Workflows
```
GET /api/agencies/workflows
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "workflows": [
    {
      "id": "driving_license",
      "name": "Driving License",
      "name_sw": "Leseni ya Kuendesha",
      "description": "Apply for or renew your driving license",
      "agency": "NTSA"
    },
    {
      "id": "passport",
      "name": "Passport",
      "name_sw": "Pasipoti",
      "description": "Apply for or renew your passport",
      "agency": "DCRS"
    },
    {
      "id": "good_conduct_cert",
      "name": "Good Conduct Certificate",
      "name_sw": "Cheti cha Mtu Mwenye Tabia Njema",
      "description": "Apply for a Good Conduct Certificate",
      "agency": "DCI"
    }
  ]
}
```

---

### Location Services Endpoints

#### 1. Get Huduma Centres
```
GET /location/huduma-centres
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "huduma_centres": [
    {
      "id": "huduma_gpo",
      "name": "Huduma Centre GPO",
      "city": "Nairobi",
      "address": "GPO Building, Kenyatta Avenue, Nairobi",
      "coordinates": {
        "lat": -1.2833,
        "lng": 36.8167
      },
      "phone": "0800 221 199",
      "hours": "Mon-Fri: 8:00 AM - 5:00 PM"
    },
    {
      "id": "huduma_eastleigh",
      "name": "Huduma Centre Eastleigh",
      "city": "Nairobi",
      "address": "Eastleigh Shopping Centre, Nairobi",
      "coordinates": {
        "lat": -1.2733,
        "lng": 36.8467
      }
    }
  ]
}
```

#### 2. Get Directions
```
GET /location/directions?origin={origin}&destination={destination}
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "routes": [
    {
      "distance": "15.2 km",
      "duration": "35 mins",
      "steps": [
        {
          "instruction": "Head northwest on Kenyatta Avenue",
          "distance": "1.2 km",
          "duration": "3 mins"
        }
      ]
    }
  ]
}
```

#### 3. Get Nearby Offices
```
GET /location/nearby?latitude={lat}&longitude={lng}&radius=50000
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "nearby_offices": [
    {
      "name": "NTSA Nairobi",
      "type": "Government Agency",
      "distance_km": 3.5,
      "address": "Nairobi",
      "phone": "+254712345678"
    }
  ]
}
```

---

### RAG (Knowledge Base) Endpoints

#### 1. Query Knowledge Base
```
POST /rag/query
Authorization: Bearer {access_token}
Content-Type: application/json

Request:
{
  "query": "What are the requirements for a passport application?",
  "language": "en",
  "top_k": 3
}

Response:
{
  "success": true,
  "query": "What are the requirements for a passport application?",
  "answer": "For a passport application, you need: Valid National ID, 3 passport-size photos...",
  "sources": [
    {
      "document": "Passport Requirements",
      "page": 1,
      "relevance": 0.95
    }
  ]
}
```

#### 2. Search Documents
```
GET /rag/search?keyword=passport&document_type=requirements
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "results": [
    {
      "title": "Passport Application Requirements",
      "document_id": "doc_001",
      "excerpt": "The following documents are required...",
      "relevance_score": 0.92
    }
  ]
}
```

#### 3. Get Available Documents
```
GET /rag/documents
Authorization: Bearer {access_token}

Response:
{
  "success": true,
  "documents": [
    {
      "id": "doc_001",
      "title": "Passport Application Guide",
      "type": "guide",
      "last_updated": "2024-03-01T00:00:00Z"
    },
    {
      "id": "doc_002",
      "title": "Constitution of Kenya",
      "type": "legal",
      "chunks": 450
    }
  ]
}
```

---

### Health & Status Endpoints

#### 1. Server Health Check
```
GET /health
Authorization: Bearer {access_token}

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-03-15T10:50:00Z",
  "services": {
    "database": "connected",
    "gemini": true,
    "dialogflow": true,
    "elevenlabs": true,
    "sms": true,
    "payments": true,
    "maps": true
  },
  "uptime_seconds": 123456
}
```

#### 2. Root Endpoint
```
GET /
Authorization: Bearer {access_token}

Response:
{
  "name": "eCitizen Voice Assistant",
  "version": "1.0.0",
  "description": "Voice-enabled chatbot for eCitizen services",
  "documentation": "/docs",
  "health": "/health",
  "endpoints": {
    "voice": "/voice",
    "booking": "/booking",
    "services": "/services",
    "session": "/session"
  }
}
```

---

## FRONTEND INTEGRATION POINTS

### Base Configuration
**File:** [frontend/src/lib/api.ts](frontend/src/lib/api.ts)

**API Client Setup:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth interceptor adds Bearer token to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('rafiki_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Frontend API Namespace

```typescript
// All available APIs in frontend
import api from '@/lib/api';

// Authentication
await api.auth.login(phone, password)
await api.auth.signup(phone, password)
await api.auth.verifyOtp(phone, otp)
await api.auth.refreshToken()

// Voice
await api.voice.processAudio(audioFile, sessionId)
await api.voice.getTextToSpeech(text, language)
await api.voice.getHealth()

// Sessions
await api.session.create(userId, language)
await api.session.getById(sessionId)
await api.session.delete(sessionId)

// Services & Booking
await api.services.getAll()
await api.services.getById(serviceId)
await api.booking.create(bookingRequest)
await api.booking.getTimeSlots(serviceId, date)
await api.booking.getById(bookingId)

// Avatar
await api.avatar.list()
await api.avatar.generateVideo(audioFile, avatarId)
await api.avatar.textToVideo(text, avatarId, options)
await api.avatar.getHealth()

// Agencies (Workflows)
await api.agencies.chat(sessionId, message)
await api.agencies.initPayment(sessionId, phone, amount)
await api.agencies.verifyPayment(sessionId, reference)

// TTS
await api.tts.generateSpeech(text, language, voiceId)
```

---

## ENVIRONMENT CONFIGURATION

### Required for Render Deployment

Create a `.env` file with all these variables (or configure in Render dashboard):

```bash
# ========== CORE APPLICATION ==========
APP_NAME="eCitizen Voice Assistant"
APP_ENV=production
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=your-secure-random-string-min-32-chars
HOST=0.0.0.0
PORT=8000

# ========== CORS ==========
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-domain.com

# ========== DATABASE (PostgreSQL required for production) ==========
DATABASE_URL=postgresql://user:password@your-db-host:5432/rafiki

# ========== GOOGLE APIS ==========
GEMINI_API_KEY=sk_...your-google-gemini-key...
GOOGLE_API_KEY=AIza...your-google-api-key...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# ========== DIALOGFLOW ==========
DIALOGFLOW_PROJECT_ID=your-dialogflow-project-id
DIALOGFLOW_LANGUAGE_CODE=en

# ========== ELEVENLABS ==========
ELEVENLABS_API_KEY=sk_...your-elevenlabs-key...
ELEVENLABS_AGENT_ID=agent_...
ELEVENLABS_BRANCH_ID=agtbrch_...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# ========== SMS (AFRICA'S TALKING) ==========
AFRICASTALKING_USERNAME=your-username
AFRICASTALKING_API_KEY=atsk_...your-api-key...
AFRICASTALKING_SENDER_ID=20880
AFRICASTALKING_VIRTUAL_NUMBER=+254711082025

# ========== PAYMENTS (PAYSTACK) ==========
PAYSTACK_SECRET_KEY=sk_live_...your-paystack-secret-key...

# ========== GOOGLE MAPS ==========
GOOGLE_MAPS_API_KEY=your-google-maps-key

# ========== KRA (OPTIONAL) ==========
KRA_ENABLED=false
KRA_API_URL=https://itax.kra.go.ke/api
KRA_CLIENT_ID=your-kra-client-id
KRA_CLIENT_SECRET=your-kra-client-secret
KRA_API_KEY=your-kra-api-key

# ========== SESSION ==========
SESSION_TIMEOUT_MINUTES=30
SESSION_SECRET_KEY=your-secure-session-key

# ========== LOGGING ==========
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# ========== RATE LIMITING ==========
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# ========== VOICE SETTINGS ==========
SPEECH_RECOGNITION_LANGUAGE=en-KE
TTS_VOICE_ID=1
TTS_RATE=150

# ========== RAG SYSTEM ==========
RAG_VECTOR_DB_PATH=./backend/data/chroma_db
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=5
```

### Frontend Environment Variables

Create `frontend/.env.local`:
```bash
VITE_API_BASE_URL=https://api.your-render-domain.com
VITE_BACKEND_URL=https://api.your-render-domain.com
```

---

## DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] All environment variables configured in Render dashboard
- [ ] PostgreSQL database provisioned and connection string added
- [ ] All third-party API keys obtained and validated:
  - [ ] Google Gemini API
  - [ ] ElevenLabs API
  - [ ] Africa's Talking API
  - [ ] Paystack API
  - [ ] Google Maps API
  - [ ] Google Cloud (for TTS & Dialogflow)
- [ ] Frontend `.env.local` updated with Render backend URL
- [ ] CORS_ORIGINS updated with your Render domains

### Render Deployment Steps
1. Connect GitHub repository to Render
2. Create Backend service (Python)
3. Add all environment variables
4. Deploy backend
5. Create Frontend service (Static site)
6. Update frontend environment with backend URL
7. Deploy frontend
8. Run health checks:
   ```bash
   curl https://your-api-domain.com/health
   ```

### Post-Deployment Validation
- [ ] Health endpoint returns all services "true"
- [ ] Test authentication flow
- [ ] Test voice processing
- [ ] Test booking creation & payment
- [ ] Test SMS delivery
- [ ] Monitor logs for errors

---

**Last Updated:** March 10, 2026  
**Version:** 1.0.0  
**Status:** Complete API Reference
