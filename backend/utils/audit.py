"""
Audit Logging Service for Kenya Government Voice Assistant

Provides immutable, compliance-ready audit logging for:
- User actions
- System decisions
- Workflow transitions
- Security events
- API calls
- SMS/notifications sent

Features:
- Immutable log entries with SHA-256 chaining
- PII redaction
- Structured JSON format
- Async file + database logging
- Log rotation support
"""

import json
import hashlib
import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
import aiofiles

from utils.logger import get_logger
from utils.encryption import get_pii_detector

logger = get_logger(__name__)


class AuditEventType(str, Enum):
    """Types of auditable events."""
    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_INPUT = "user_input"
    
    # Session events
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_STEP = "workflow_step"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    
    # Service events
    BOOKING_CREATED = "booking_created"
    BOOKING_CANCELLED = "booking_cancelled"
    SMS_SENT = "sms_sent"
    SMS_FAILED = "sms_failed"
    
    # Security events
    AUTH_FAILED = "auth_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    FRAUD_DETECTED = "fraud_detected"
    SUSPICIOUS_INPUT = "suspicious_input"
    
    # Citizen interaction
    FEEDBACK_SUBMITTED = "feedback_submitted"
    EMERGENCY_REPORTED = "emergency_reported"
    CORRUPTION_REPORTED = "corruption_reported"
    
    # System events
    API_CALL = "api_call"
    ERROR = "error"
    RAG_QUERY = "rag_query"
    TTS_GENERATED = "tts_generated"
    STT_PROCESSED = "stt_processed"


class RiskLevel(str, Enum):
    """Risk level for security events."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    session_id: Optional[str]
    user_id: Optional[str]
    request_id: Optional[str]
    action: str
    details: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.INFO
    ip_hash: Optional[str] = None
    user_agent_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "action": self.action,
            "details": self.details,
            "risk_level": self.risk_level.value,
            "ip_hash": self.ip_hash,
            "user_agent_hash": self.user_agent_hash,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash
        }
    
    def compute_hash(self, previous_hash: Optional[str] = None) -> str:
        """Compute SHA-256 hash of entry for immutability chain."""
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "action": self.action,
            "previous_hash": previous_hash
        }
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class AuditService:
    """
    Immutable audit logging service.
    
    Usage:
        audit = get_audit_service()
        await audit.log(
            event_type=AuditEventType.WORKFLOW_STARTED,
            session_id="abc123",
            action="Started NTSA driving license workflow",
            details={"workflow_id": "ntsa_driving_license"}
        )
    """
    
    def __init__(
        self,
        log_dir: str = "./logs/audit",
        enable_file_logging: bool = True,
        enable_db_logging: bool = False,
        redact_pii: bool = True
    ):
        """
        Initialize audit service.
        
        Args:
            log_dir: Directory for audit log files
            enable_file_logging: Write to JSON files
            enable_db_logging: Write to database (requires setup)
            redact_pii: Automatically redact PII from logs
        """
        self.log_dir = Path(log_dir)
        self.enable_file_logging = enable_file_logging
        self.enable_db_logging = enable_db_logging
        self.redact_pii = redact_pii
        
        self._last_hash: Optional[str] = None
        self._entry_count = 0
        self._lock = asyncio.Lock()
        self._pii_detector = get_pii_detector() if redact_pii else None
        
        # Create log directory
        if enable_file_logging:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AuditService initialized (file={enable_file_logging}, db={enable_db_logging})")
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        return f"evt_{uuid.uuid4().hex[:16]}"
    
    def _hash_value(self, value: str) -> str:
        """Hash a value for privacy."""
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def _redact_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Redact PII from details dictionary."""
        if not self._pii_detector or not details:
            return details
        
        redacted = {}
        for key, value in details.items():
            if isinstance(value, str):
                # Check for common PII field names
                if key.lower() in ['phone', 'phone_number', 'email', 'national_id', 'kra_pin', 'password']:
                    redacted[key] = f"[REDACTED:{len(value)}chars]"
                else:
                    redacted[key] = self._pii_detector.mask(value)
            elif isinstance(value, dict):
                redacted[key] = self._redact_details(value)
            else:
                redacted[key] = value
        
        return redacted
    
    async def log(
        self,
        event_type: AuditEventType,
        action: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        risk_level: RiskLevel = RiskLevel.INFO,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditEntry:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Human-readable action description
            session_id: Associated session ID
            user_id: Associated user ID (if authenticated)
            request_id: Request correlation ID
            details: Additional event details (will be PII-redacted)
            risk_level: Security risk level
            client_ip: Client IP (will be hashed)
            user_agent: User agent (will be hashed)
            
        Returns:
            The created audit entry
        """
        async with self._lock:
            # Create entry
            entry = AuditEntry(
                event_id=self._generate_event_id(),
                event_type=event_type,
                timestamp=datetime.utcnow().isoformat() + "Z",
                session_id=session_id,
                user_id=user_id,
                request_id=request_id,
                action=action,
                details=self._redact_details(details or {}),
                risk_level=risk_level,
                ip_hash=self._hash_value(client_ip) if client_ip else None,
                user_agent_hash=self._hash_value(user_agent) if user_agent else None,
                previous_hash=self._last_hash
            )
            
            # Compute hash chain
            entry.entry_hash = entry.compute_hash(self._last_hash)
            self._last_hash = entry.entry_hash
            self._entry_count += 1
            
            # Write to file
            if self.enable_file_logging:
                await self._write_to_file(entry)
            
            # Write to database
            if self.enable_db_logging:
                await self._write_to_db(entry)
            
            # Log high-risk events to application log
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                logger.warning(
                    f"AUDIT [{risk_level.value}]: {event_type.value} - {action}",
                    extra={"event_id": entry.event_id}
                )
            
            return entry
    
    async def _write_to_file(self, entry: AuditEntry):
        """Write entry to audit log file."""
        try:
            # Daily rotation
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"audit_{date_str}.jsonl"
            
            async with aiofiles.open(log_file, mode='a') as f:
                await f.write(json.dumps(entry.to_dict()) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    async def _write_to_db(self, entry: AuditEntry):
        """Write entry to database (stub for now)."""
        # TODO: Implement database logging when db models are ready
        pass
    
    async def log_workflow_event(
        self,
        event_type: AuditEventType,
        workflow_id: str,
        execution_id: str,
        session_id: str,
        step_id: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None
    ):
        """Convenience method for workflow audit logging."""
        await self.log(
            event_type=event_type,
            action=f"Workflow {workflow_id}: {event_type.value}",
            session_id=session_id,
            details={
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "step_id": step_id,
                "entities": entities or {}
            }
        )
    
    async def log_security_event(
        self,
        event_type: AuditEventType,
        action: str,
        risk_level: RiskLevel,
        session_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Convenience method for security audit logging."""
        await self.log(
            event_type=event_type,
            action=action,
            session_id=session_id,
            risk_level=risk_level,
            client_ip=client_ip,
            details=details
        )
    
    async def log_sms_event(
        self,
        success: bool,
        phone_masked: str,
        message_type: str,
        session_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log SMS send event."""
        await self.log(
            event_type=AuditEventType.SMS_SENT if success else AuditEventType.SMS_FAILED,
            action=f"SMS {message_type}: {'sent' if success else 'failed'}",
            session_id=session_id,
            details={
                "phone_masked": phone_masked,
                "message_type": message_type,
                "error": error
            },
            risk_level=RiskLevel.INFO if success else RiskLevel.LOW
        )
    
    async def log_citizen_report(
        self,
        report_type: str,
        reference_id: str,
        is_anonymous: bool,
        session_id: Optional[str] = None
    ):
        """Log citizen report (feedback, emergency, corruption)."""
        event_map = {
            "feedback": AuditEventType.FEEDBACK_SUBMITTED,
            "emergency": AuditEventType.EMERGENCY_REPORTED,
            "corruption": AuditEventType.CORRUPTION_REPORTED
        }
        
        await self.log(
            event_type=event_map.get(report_type, AuditEventType.FEEDBACK_SUBMITTED),
            action=f"Citizen {report_type} report submitted",
            session_id=session_id,
            details={
                "reference_id": reference_id,
                "is_anonymous": is_anonymous,
                "report_type": report_type
            }
        )
    
    async def get_session_audit_trail(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all audit entries for a session (from today's log)."""
        try:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"audit_{date_str}.jsonl"
            
            if not log_file.exists():
                return []
            
            entries = []
            async with aiofiles.open(log_file, mode='r') as f:
                async for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("session_id") == session_id:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to read audit trail: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit service statistics."""
        return {
            "total_entries": self._entry_count,
            "last_hash": self._last_hash,
            "file_logging": self.enable_file_logging,
            "db_logging": self.enable_db_logging,
            "pii_redaction": self.redact_pii
        }


# Global audit service instance
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Get or create the audit service singleton."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
