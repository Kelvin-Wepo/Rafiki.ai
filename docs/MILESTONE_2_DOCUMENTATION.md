# Milestone 2: Security, Privacy & Knowledge Integration

**Project:** Rafiki.ai - Kenya Government AI Voice Assistant  
**Milestone:** Week 2 Implementation  
**Date Completed:** February 4, 2026  
**Status:** ✅ Complete

---

## Executive Summary

Milestone 2 focused on implementing enterprise-grade security features, privacy protection mechanisms, and an intelligent knowledge retrieval system (RAG) to enable Rafiki to answer questions about Kenyan government services, the Constitution, and tax regulations with accuracy and proper citations.

---

## Features Implemented

### 1. Encryption Service (`backend/utils/encryption.py`)

A comprehensive encryption module providing data protection at rest and in transit.

#### Components:
- **EncryptionService**: AES-256-GCM encryption for sensitive data
- **PIIDetector**: Pattern-based detection for Kenyan PII formats
- **SecureHasher**: Argon2-based password hashing with salt

#### Key Features:
```python
# Encryption
encryption_service = EncryptionService()
encrypted = encryption_service.encrypt("sensitive data")
decrypted = encryption_service.decrypt(encrypted)

# PII Detection
pii_detector = PIIDetector()
detected = pii_detector.detect("My ID is 12345678")
# Returns: {'national_id': ['12345678']}

masked = pii_detector.mask("Call me on 0712345678")
# Returns: "Call me on [PHONE REDACTED]"
```

#### Supported PII Types:
| Type | Pattern | Example |
|------|---------|---------|
| National ID | 8 digits | 12345678 |
| KRA PIN | A + 9 digits + letter | A123456789B |
| Phone Number | 07/01/+254 formats | 0712345678 |
| Email | Standard format | user@example.com |
| Passport | 2 letters + 7 digits | AB1234567 |

---

### 2. Encrypted Session Manager (`backend/utils/session_manager.py`)

Secure session management with encrypted storage and automatic cleanup.

#### Features:
- **Encrypted session data** - All session context is encrypted at rest
- **Automatic expiration** - Sessions expire after configurable timeout (default: 30 minutes)
- **Secure session IDs** - Cryptographically random session identifiers
- **Context persistence** - Maintains conversation history and booking state

#### Usage:
```python
session_manager = EncryptedSessionManager()

# Create session
session = await session_manager.create_session()

# Update with encrypted data
await session_manager.update_session(
    session.session_id,
    conversation_context={"history": [...]},
    booking_state={"service_type": "passport"}
)

# Automatic cleanup runs every 5 minutes
```

---

### 3. RAG (Retrieval-Augmented Generation) Service (`backend/services/rag_service.py`)

An intelligent document retrieval system that enables Rafiki to answer questions using official government documents.

#### Architecture:
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  User Question  │────▶│  RAG Service │────▶│  ChromaDB       │
└─────────────────┘     └──────────────┘     │  Vector Store   │
                               │              └─────────────────┘
                               ▼                      │
                        ┌──────────────┐              │
                        │   Gemini AI  │◀─────────────┘
                        │  + Context   │     Retrieved Chunks
                        └──────────────┘
```

#### Document Sources:
| Document | Description | Chunks |
|----------|-------------|--------|
| Constitution of Kenya 2010 | Full constitutional text | ~50 |
| KRA Tax Guide | Tax filing procedures, nil returns | ~15 |
| eCitizen Services | Government service procedures | ~10 |

#### Key Methods:
```python
rag_service = ConstitutionRAG()

# Load all documents
rag_service.load_all_documents()

# Query with citations
results = rag_service.query_with_citations(
    query_text="What does the Constitution say about citizenship?",
    language="en",
    top_k=3
)

# Returns:
{
    "context": "Article 15 states that...",
    "citations": [
        {"citation": "Constitution of Kenya 2010, Chapter 3, Article 15"},
        ...
    ],
    "spoken_citations": ["According to the Constitution of Kenya 2010"],
    "verified": True
}
```

#### Knowledge Query Detection:
The system automatically detects knowledge queries using pattern matching:
- Constitution keywords: `constitution`, `katiba`, `law`, `sheria`, `article`, `chapter`
- Citizenship keywords: `citizenship`, `uraia`, `rights`, `haki`
- Tax keywords: `kra`, `itax`, `tax`, `nil returns`, `pin`
- Service keywords: `ecitizen`, `passport`, `id card`, `license`, `permit`

---

### 4. Gemini Service with RAG Integration (`backend/services/gemini_service.py`)

Enhanced Gemini AI service with PII protection and RAG-powered knowledge responses.

#### Features:
- **Dual API Support**: Compatible with both `google-genai` (new) and `google-generativeai` (legacy)
- **PII Detection**: Sanitizes inputs before processing, masks PII in logs
- **RAG Integration**: Automatically retrieves context for knowledge queries
- **Bilingual Support**: English and Kiswahili responses

#### Flow:
```
User Message
     │
     ▼
┌─────────────────────┐
│  PII Detection      │ ─── Log warning if PII found
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Knowledge Query?   │ ─── Yes ──▶ Query RAG Service
└─────────────────────┘              │
     │                               │
     ▼                               ▼
┌─────────────────────┐     ┌─────────────────────┐
│  Build Prompt       │◀────│  Add RAG Context    │
└─────────────────────┘     └─────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Gemini Generate    │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Parse Response     │ ─── Strip markdown, extract JSON
└─────────────────────┘
     │
     ▼
  Response with Citations
```

---

### 5. Fraud Detection Service (`backend/services/fraud_service.py`)

Real-time fraud detection for government service transactions.

#### Risk Factors Monitored:
| Factor | Weight | Description |
|--------|--------|-------------|
| Velocity | 0.3 | Multiple requests in short time |
| Geo-anomaly | 0.25 | Unusual location patterns |
| Device fingerprint | 0.2 | New or suspicious devices |
| Behavioral | 0.15 | Unusual interaction patterns |
| Time-based | 0.1 | Requests at unusual hours |

#### Risk Levels:
- **LOW** (0-30): Normal transaction, proceed
- **MEDIUM** (31-60): Additional verification recommended
- **HIGH** (61-80): Manual review required
- **CRITICAL** (81-100): Block transaction, alert security

#### Usage:
```python
fraud_service = FraudDetectionService()

result = await fraud_service.assess_risk(
    user_id="user123",
    action="kra_nil_returns",
    context={
        "ip_address": "196.201.x.x",
        "device_id": "device_fingerprint",
        "session_duration": 300
    }
)

# Returns:
{
    "risk_score": 25,
    "risk_level": "LOW",
    "factors": {...},
    "recommendation": "proceed",
    "requires_verification": False
}
```

---

### 6. Alert Notification Service (`backend/services/alert_service.py`)

Multi-channel alert system for security events and user notifications.

#### Supported Channels:
- **SMS** (Africa's Talking): Transaction confirmations, OTPs
- **Email** (SendGrid/SMTP): Detailed reports, account alerts
- **Push Notifications**: Real-time security alerts
- **Internal Logging**: Audit trail for compliance

#### Alert Types:
```python
class AlertType(Enum):
    SECURITY = "security"           # Security-related alerts
    FRAUD = "fraud"                 # Fraud detection alerts
    TRANSACTION = "transaction"     # Transaction confirmations
    SYSTEM = "system"               # System health alerts
    USER = "user"                   # User activity alerts
```

#### Usage:
```python
alert_service = AlertService()

# Send security alert
await alert_service.send_alert(
    alert_type=AlertType.SECURITY,
    severity=AlertSeverity.HIGH,
    title="Suspicious Login Attempt",
    message="Multiple failed login attempts detected",
    recipient="security@rafiki.ai",
    channels=["email", "sms"]
)

# Send transaction confirmation
await alert_service.send_transaction_confirmation(
    phone_number="+254712345678",
    transaction_type="KRA Nil Returns",
    reference="NIL-2026-0001",
    amount=0
)
```

---

## API Endpoints

### Voice/Chat Endpoint with RAG
```http
POST /voice/chat
Content-Type: application/json

{
    "message": "What does the Constitution say about citizenship?",
    "language": "en",
    "session_id": "optional-session-id"
}
```

**Response:**
```json
{
    "text": "According to the Constitution of Kenya 2010, citizenship can be acquired through birth, registration, or naturalization...",
    "intent": "service_inquiry",
    "entities": {},
    "session_id": "generated-session-id",
    "requires_input": true,
    "suggested_actions": ["Ask about other provisions", "Learn about registration"],
    "sources": ["Constitution of Kenya 2010, Chapter 3"],
    "verified": true
}
```

### Health Check with Service Status
```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-02-04T12:00:00Z",
    "services": {
        "gemini": true,
        "dialogflow": true,
        "voice": true,
        "sms": true,
        "elevenlabs": true
    }
}
```

---

## Configuration

### Environment Variables
```bash
# Gemini API
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash

# Encryption
ENCRYPTION_KEY=your_32_byte_key_base64_encoded

# SMS (Africa's Talking)
AT_API_KEY=your_api_key
AT_USERNAME=your_username

# ElevenLabs TTS
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_VOICE_ID=your_voice_id

# Alert Service
ALERT_EMAIL=alerts@rafiki.ai
SMTP_HOST=smtp.example.com
SMTP_PORT=587
```

---

## Testing

### Test Results Summary
All 6 core tests passed:

| Test | Status | Description |
|------|--------|-------------|
| Encryption & PII | ✅ PASS | Encrypt/decrypt, PII detection, masking |
| Session Manager | ✅ PASS | Create, update, retrieve, expire sessions |
| Gemini + PII | ✅ PASS | PII detection in AI pipeline |
| RAG Service | ✅ PASS | Document loading, query, citations (74 chunks) |
| Fraud Detection | ✅ PASS | Risk assessment, scoring, recommendations |
| Alert Service | ✅ PASS | Multi-channel notifications |

### Running Tests
```bash
cd backend
pytest tests/ -v --cov=services --cov-report=html
```

---

## Security Considerations

### Data Protection
- All PII is detected and masked before logging
- Session data is encrypted with AES-256-GCM
- Encryption keys are stored securely (environment variables)
- No sensitive data is stored in plain text

### API Security
- Rate limiting on all endpoints
- Session-based authentication
- Input sanitization and validation
- CORS protection enabled

### Compliance
- GDPR-ready PII handling
- Kenya Data Protection Act compliance
- Audit logging for all sensitive operations

---

## Known Limitations

1. **RAG Document Coverage**: Currently limited to Constitution, KRA, and eCitizen documents. More government documents can be added.

2. **Offline Mode**: RAG requires ChromaDB to be running. No offline fallback.

3. **Language Support**: Full support for English, partial for Kiswahili (depends on document availability).

4. **Fraud Detection**: Currently uses rule-based scoring. ML models planned for future.

---

## Future Enhancements (Milestone 3+)

- [ ] ML-based fraud detection models
- [ ] Additional government document sources
- [ ] Voice biometrics for authentication
- [ ] WhatsApp integration for notifications
- [ ] Real-time KRA API integration
- [ ] Multi-factor authentication

---

## Contributors

- **Development Team**: Rafiki.ai Engineering
- **AI Integration**: Google Gemini 2.5 Flash
- **Document Processing**: ChromaDB + Google Embeddings

---

## References

- [Constitution of Kenya 2010](https://kenyalaw.org)
- [KRA iTax Portal](https://itax.kra.go.ke)
- [eCitizen Portal](https://ecitizen.go.ke)
- [Google Gemini API](https://ai.google.dev)
- [ChromaDB Documentation](https://docs.trychroma.com)

---

*Documentation generated: February 4, 2026*
