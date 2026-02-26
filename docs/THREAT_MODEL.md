# Threat Model Summary

## Kenya Government Voice Assistant - Security Analysis

**Document Version**: 1.0  
**Last Updated**: 2024-02  
**Classification**: Internal

---

## 1. System Overview

The Kenya Government Voice Assistant (Rafiki.ai) is a voice-based interface that helps citizens access government services. It handles sensitive data including:

- National ID numbers
- KRA PIN numbers
- Phone numbers
- Voice recordings
- Service booking confirmations

### System Components

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Frontend  │────▶│   Backend   │────▶│  External    │
│   (React)   │◀────│  (FastAPI)  │◀────│  Services    │
└─────────────┘     └─────────────┘     └──────────────┘
                           │
                    ┌──────┴──────┐
                    │  Database   │
                    │ (PostgreSQL)│
                    └─────────────┘
```

---

## 2. Threat Categories

### 2.1 Data Privacy Threats

| ID | Threat | Impact | Likelihood | Mitigation |
|----|--------|--------|------------|------------|
| DP-01 | PII exposure in logs | High | Medium | Auto-redaction in audit service |
| DP-02 | Voice recording storage | High | Medium | Transient processing, no storage |
| DP-03 | Session hijacking | High | Low | Secure session tokens, expiry |
| DP-04 | Data exfiltration | Critical | Low | Rate limiting, anomaly detection |

### 2.2 Authentication & Authorization Threats

| ID | Threat | Impact | Likelihood | Mitigation |
|----|--------|--------|------------|------------|
| AA-01 | Brute force OTP | Medium | High | Rate limiting, lockout |
| AA-02 | Session token theft | High | Medium | Short expiry, secure cookies |
| AA-03 | Unauthorized API access | Medium | Medium | API key validation |

### 2.3 Injection & Input Threats

| ID | Threat | Impact | Likelihood | Mitigation |
|----|--------|--------|------------|------------|
| IN-01 | Prompt injection | Medium | High | Input sanitization, validation |
| IN-02 | SQL injection | Critical | Low | Parameterized queries, ORM |
| IN-03 | XSS attacks | Medium | Medium | Output encoding, CSP headers |
| IN-04 | Malicious audio files | Low | Low | File validation, sandboxed processing |

### 2.4 Denial of Service Threats

| ID | Threat | Impact | Likelihood | Mitigation |
|----|--------|--------|------------|------------|
| DOS-01 | API flooding | Medium | High | Rate limiting per IP/session |
| DOS-02 | Resource exhaustion | High | Medium | Request timeouts, resource limits |
| DOS-03 | LLM abuse | High | Medium | Token limits, request throttling |

### 2.5 Fraud & Abuse Threats

| ID | Threat | Impact | Likelihood | Mitigation |
|----|--------|--------|------------|------------|
| FR-01 | Fake booking spam | Medium | High | Phone verification, CAPTCHA |
| FR-02 | Identity impersonation | High | Medium | Multi-factor verification |
| FR-03 | False emergency reports | Medium | Medium | Report validation, callback |

---

## 3. Security Controls

### 3.1 Data Protection

- **PII Redaction**: All sensitive data auto-redacted in audit logs
- **Encryption at Rest**: Database encryption enabled
- **Encryption in Transit**: TLS 1.2+ for all connections
- **Data Minimization**: Only necessary data collected

### 3.2 Input Validation

```python
# Example: Kenya-specific validators
VALIDATORS = {
    "phone_ke": r"^(\+?254|0)?[17]\d{8}$",
    "national_id": r"^\d{7,8}$",
    "kra_pin": r"^[AP]\d{9}[A-Z]$",
}
```

### 3.3 Rate Limiting

| Resource | Limit | Window | Action |
|----------|-------|--------|--------|
| API calls | 100/minute | Per IP | 429 response |
| OTP requests | 3/hour | Per phone | Lockout |
| Booking requests | 5/day | Per user | Queue |
| Voice processing | 10/minute | Per session | Throttle |

### 3.4 Audit Logging

Every significant action is logged with:
- Immutable SHA-256 hash chain
- PII auto-redaction
- Risk level classification
- Session correlation

```json
{
  "event_id": "evt_abc123",
  "event_type": "workflow_started",
  "timestamp": "2024-02-26T12:00:00Z",
  "session_id": "sess_xyz",
  "action": "Started NTSA workflow",
  "risk_level": "info",
  "previous_hash": "def456...",
  "entry_hash": "789ghi..."
}
```

---

## 4. Trust Boundaries

### 4.1 External to Backend
- All external input untrusted
- API rate limiting enforced
- Input validation mandatory

### 4.2 Backend to External Services
- API keys stored securely
- HTTPS for all external calls
- Response validation

### 4.3 Backend to Database
- Parameterized queries only
- Connection pooling with limits
- Read replicas for queries

---

## 5. Sensitive Data Flows

### 5.1 National ID Flow
```
User Input → Validation → Masked Storage → Service Call → Audit Log (Redacted)
```

### 5.2 Phone Number Flow
```
User Input → Validation → SMS Service → Confirmation → Audit Log (Redacted)
```

### 5.3 Voice Recording Flow
```
Audio Upload → STT Processing → Text Extraction → Audio Deleted (No Storage)
```

---

## 6. Compliance Considerations

### 6.1 Kenya Data Protection Act 2019
- Consent required for data collection ✅
- Purpose limitation enforced ✅
- Data subject rights supported ✅
- Cross-border transfer controls 🔄

### 6.2 Government Security Standards
- Access control implemented ✅
- Audit trail maintained ✅
- Incident response plan 🔄
- Regular security assessments 🔄

---

## 7. Recommended Actions

### High Priority
1. [ ] Implement CAPTCHA for booking endpoints
2. [ ] Add phone number verification for SMS
3. [ ] Enable WAF for API gateway
4. [ ] Set up security monitoring alerts

### Medium Priority
1. [ ] Conduct penetration testing
2. [ ] Implement API key rotation
3. [ ] Add anomaly detection for fraud
4. [ ] Create incident response runbook

### Low Priority
1. [ ] Add biometric verification option
2. [ ] Implement request signing
3. [ ] Set up security training program

---

## 8. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-02 | Security Team | Initial threat model |

---

*This document should be reviewed quarterly or after significant system changes.*
