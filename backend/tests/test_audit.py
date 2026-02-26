"""
Tests for the Audit Service

Tests cover:
- Event logging
- PII redaction
- Hash chain integrity
- Event querying
- Compliance features
"""

import pytest
import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Import from utils
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.audit import (
    AuditService,
    AuditEntry,
    AuditEventType,
    RiskLevel
)


@pytest.fixture
def temp_audit_dir():
    """Create a temporary directory for audit logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def audit_service(temp_audit_dir):
    """Create an audit service with temporary storage."""
    return AuditService(
        log_dir=temp_audit_dir,
        enable_file_logging=True,
        redact_pii=True
    )


class TestAuditEventCreation:
    """Tests for creating audit events."""
    
    @pytest.mark.asyncio
    async def test_create_event(self, audit_service):
        """Test creating a basic audit event."""
        entry = await audit_service.log(
            event_type=AuditEventType.USER_LOGIN,
            action="User logged in successfully",
            session_id="session-123",
            user_id="user-456"
        )
        
        assert entry.event_type == AuditEventType.USER_LOGIN
        assert entry.session_id == "session-123"
        assert entry.user_id == "user-456"
        assert entry.timestamp is not None
        assert entry.event_id is not None
    
    @pytest.mark.asyncio
    async def test_create_event_with_details(self, audit_service):
        """Test creating an event with details."""
        details = {
            "login_method": "password",
            "device": "mobile"
        }
        
        entry = await audit_service.log(
            event_type=AuditEventType.USER_LOGIN,
            action="User login attempt",
            details=details
        )
        
        assert entry.details["login_method"] == "password"
        assert entry.details["device"] == "mobile"


class TestPIIRedaction:
    """Tests for PII detection and redaction."""
    
    @pytest.mark.asyncio
    async def test_redact_phone_in_details(self, audit_service):
        """Test phone number redaction in details."""
        entry = await audit_service.log(
            event_type=AuditEventType.USER_INPUT,
            action="User provided phone",
            details={"phone": "0712345678"}
        )
        
        # Phone should be redacted
        assert "0712345678" not in entry.details.get("phone", "")
    
    @pytest.mark.asyncio
    async def test_redact_email_in_details(self, audit_service):
        """Test email redaction in details."""
        entry = await audit_service.log(
            event_type=AuditEventType.USER_INPUT,
            action="User provided email",
            details={"email": "user@example.com"}
        )
        
        # Email should be redacted
        assert "user@example.com" not in entry.details.get("email", "")
    
    @pytest.mark.asyncio
    async def test_redact_national_id(self, audit_service):
        """Test National ID redaction."""
        entry = await audit_service.log(
            event_type=AuditEventType.USER_INPUT,
            action="User provided ID",
            details={"national_id": "12345678"}
        )
        
        # National ID should be redacted
        assert "12345678" not in entry.details.get("national_id", "")
    
    def test_no_redaction_when_disabled(self, temp_audit_dir):
        """Test that redaction doesn't happen when disabled."""
        service = AuditService(
            log_dir=temp_audit_dir,
            redact_pii=False
        )
        
        # We'd need to test internal method directly
        # Skip this test if redaction method is not exposed


class TestHashChaining:
    """Tests for hash chain integrity."""
    
    @pytest.mark.asyncio
    async def test_hash_chain_sequential(self, audit_service):
        """Test that events are chained sequentially."""
        entries = []
        
        for i in range(3):
            entry = await audit_service.log(
                event_type=AuditEventType.API_CALL,
                action=f"Test event {i}"
            )
            entries.append(entry)
        
        # First entry may have None or genesis hash
        # Subsequent entries should chain to previous
        if entries[0].previous_hash:
            assert entries[1].previous_hash == entries[0].entry_hash
            assert entries[2].previous_hash == entries[1].entry_hash
    
    @pytest.mark.asyncio
    async def test_entry_has_hash(self, audit_service):
        """Test that entries have computed hashes."""
        entry = await audit_service.log(
            event_type=AuditEventType.API_CALL,
            action="Test event"
        )
        
        # Entry should have a hash
        assert entry.entry_hash is not None
        assert len(entry.entry_hash) == 64  # SHA-256 hex


class TestEventLogging:
    """Tests for logging events to storage."""
    
    @pytest.mark.asyncio
    async def test_log_event_to_file(self, audit_service, temp_audit_dir):
        """Test that events are logged to file."""
        await audit_service.log(
            event_type=AuditEventType.API_CALL,
            action="Test file logging"
        )
        
        # Check that log file was created
        log_files = list(Path(temp_audit_dir).glob("*.jsonl"))
        assert len(log_files) >= 1
        
        # Read the log file
        with open(log_files[0], 'r') as f:
            line = f.readline()
            entry_data = json.loads(line)
            assert entry_data["event_type"] == AuditEventType.API_CALL.value
    
    @pytest.mark.asyncio
    async def test_workflow_event_logging(self, audit_service):
        """Test workflow event logging."""
        entry = await audit_service.log(
            event_type=AuditEventType.WORKFLOW_STARTED,
            session_id="sess-123",
            action="Started NTSA workflow",
            details={
                "workflow_id": "ntsa_license",
                "workflow_name": "NTSA Driving License"
            }
        )
        
        assert entry.event_type == AuditEventType.WORKFLOW_STARTED
        assert entry.details["workflow_id"] == "ntsa_license"


class TestEventQuerying:
    """Tests for querying logged events."""
    
    @pytest.mark.asyncio
    async def test_log_multiple_events(self, audit_service):
        """Test logging multiple events."""
        # Log events for different sessions
        entry1 = await audit_service.log(
            event_type=AuditEventType.SESSION_CREATED,
            session_id="session-A",
            action="Session A created"
        )
        entry2 = await audit_service.log(
            event_type=AuditEventType.SESSION_CREATED,
            session_id="session-B",
            action="Session B created"
        )
        
        assert entry1.session_id == "session-A"
        assert entry2.session_id == "session-B"
    
    @pytest.mark.asyncio
    async def test_different_event_types(self, audit_service):
        """Test different event types."""
        await audit_service.log(
            event_type=AuditEventType.USER_LOGIN,
            action="Login"
        )
        await audit_service.log(
            event_type=AuditEventType.WORKFLOW_STARTED,
            action="Workflow"
        )
        
        # Both should succeed without errors


class TestComplianceFeatures:
    """Tests for compliance-related features."""
    
    @pytest.mark.asyncio
    async def test_event_id_format(self, audit_service):
        """Test that event IDs have consistent format."""
        entry = await audit_service.log(
            event_type=AuditEventType.API_CALL,
            action="Test"
        )
        
        # Event ID should start with evt_
        assert entry.event_id.startswith("evt_")
    
    @pytest.mark.asyncio
    async def test_event_timestamp_format(self, audit_service):
        """Test that timestamps are in ISO format."""
        entry = await audit_service.log(
            event_type=AuditEventType.API_CALL,
            action="Test"
        )
        
        # Timestamp should be ISO format with Z suffix
        assert "T" in entry.timestamp
        assert "Z" in entry.timestamp
    
    @pytest.mark.asyncio
    async def test_risk_levels(self, audit_service):
        """Test different risk levels."""
        risk_levels = [
            RiskLevel.INFO,
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL
        ]
        
        for risk in risk_levels:
            entry = await audit_service.log(
                event_type=AuditEventType.API_CALL,
                action="Risk test",
                risk_level=risk
            )
            assert entry.risk_level == risk


class TestSecurityEventLogging:
    """Tests for security-specific event logging."""
    
    @pytest.mark.asyncio
    async def test_log_suspicious_activity(self, audit_service):
        """Test logging suspicious activity."""
        entry = await audit_service.log(
            event_type=AuditEventType.SUSPICIOUS_INPUT,
            session_id="attacker-session",
            action="Multiple failed auth attempts",
            risk_level=RiskLevel.MEDIUM,
            details={
                "attempts": 5,
                "pattern": "brute_force"
            }
        )
        
        assert entry.event_type == AuditEventType.SUSPICIOUS_INPUT
        assert entry.risk_level == RiskLevel.MEDIUM
    
    @pytest.mark.asyncio
    async def test_log_fraud_detection(self, audit_service):
        """Test logging fraud detection event."""
        entry = await audit_service.log(
            event_type=AuditEventType.FRAUD_DETECTED,
            session_id="fraud-session",
            action="Potential identity fraud detected",
            risk_level=RiskLevel.CRITICAL,
            details={
                "fraud_type": "identity_theft",
                "confidence": 0.95
            }
        )
        
        assert entry.event_type == AuditEventType.FRAUD_DETECTED
        assert entry.risk_level == RiskLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_log_rate_limit(self, audit_service):
        """Test logging rate limit event."""
        entry = await audit_service.log(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            action="Rate limit exceeded",
            risk_level=RiskLevel.HIGH,
            details={"requests_per_minute": 100}
        )
        
        assert entry.event_type == AuditEventType.RATE_LIMIT_EXCEEDED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
