"""
Advanced fraud detection service with pattern recognition and alerts.

Features:
- Rate limiting with sliding window
- Behavioral pattern analysis
- Risk scoring
- Real-time alert generation
- Multiple fraud detection algorithms

For production, swap the storage layer with Redis for distributed state.
"""

import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from utils.logger import get_logger

logger = get_logger(__name__)


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of fraud alerts"""
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    MULTIPLE_FAILURES = "multiple_failures"
    UNUSUAL_TIME = "unusual_time"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    RAPID_REQUESTS = "rapid_requests"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SESSION_HIJACK = "session_hijack"


@dataclass
class FraudAlert:
    """Represents a fraud alert"""
    alert_id: str
    alert_type: AlertType
    risk_level: RiskLevel
    identifier: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'risk_level': self.risk_level.value,
            'identifier': self.identifier,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'resolved': self.resolved
        }


@dataclass
class BehaviorProfile:
    """Tracks behavioral patterns for a user/session"""
    identifier: str
    request_times: List[float] = field(default_factory=list)
    request_intervals: List[float] = field(default_factory=list)
    failed_attempts: int = 0
    successful_attempts: int = 0
    services_accessed: List[str] = field(default_factory=list)
    last_activity: Optional[float] = None
    risk_score: float = 0.0
    
    def add_request(self, timestamp: float, success: bool = True, service: str = None):
        """Record a request"""
        if self.last_activity:
            interval = timestamp - self.last_activity
            self.request_intervals.append(interval)
        
        self.request_times.append(timestamp)
        self.last_activity = timestamp
        
        if success:
            self.successful_attempts += 1
        else:
            self.failed_attempts += 1
        
        if service:
            self.services_accessed.append(service)
        
        # Keep only last 100 entries
        if len(self.request_times) > 100:
            self.request_times = self.request_times[-100:]
        if len(self.request_intervals) > 100:
            self.request_intervals = self.request_intervals[-100:]


class FraudService:
    """
    Advanced fraud detection service with pattern recognition.
    """

    def __init__(self, enable_alerts: bool = True):
        self._events: Dict[str, list[float]] = {}
        self._blocklist: Dict[str, float] = {}
        self._profiles: Dict[str, BehaviorProfile] = {}
        self._alerts: List[FraudAlert] = []
        self._alert_callbacks: List[callable] = []
        
        self.enable_alerts = enable_alerts

        # OTP thresholds
        self.otp_limit = 5
        self.otp_window = 30 * 60
        self.otp_block_duration = 60 * 60

        self.otp_fail_limit = 5
        self.otp_fail_window = 60 * 60
        self.otp_fail_block_duration = 30 * 60
        
        # Pattern detection thresholds
        self.rapid_request_threshold = 10
        self.rapid_request_window = 60
        self.unusual_hours_start = 23
        self.unusual_hours_end = 5
        self.high_failure_ratio = 0.7
        
        # Risk thresholds
        self.risk_thresholds = {
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.9
        }
        
        logger.info("Advanced FraudService initialized")

    def _now(self) -> float:
        return time.time()

    def _prune(self, key: str, window: int) -> None:
        now = self._now()
        entries = self._events.get(key, [])
        self._events[key] = [t for t in entries if t >= now - window]

    def record_event(self, key: str, success: bool = True, service: str = None) -> None:
        """Record an event occurrence."""
        now = self._now()
        self._events.setdefault(key, []).append(now)
        
        if key not in self._profiles:
            self._profiles[key] = BehaviorProfile(identifier=key)
        self._profiles[key].add_request(now, success, service)
        
        logger.debug(f"FraudService: recorded event for {key}")

    def check_rate_limit(self, key: str, limit: int, window: int, block_duration: int) -> Dict[str, Any]:
        """Check and enforce sliding window rate limit."""
        now = self._now()

        if key in self._blocklist and self._blocklist[key] <= now:
            del self._blocklist[key]

        if key in self._blocklist:
            retry_after = int(self._blocklist[key] - now)
            return {"allow": False, "count": 0, "retry_after": max(retry_after, 0), "blocked": True}

        self._prune(key, window)
        count = len(self._events.get(key, []))

        if count >= limit:
            self._blocklist[key] = now + block_duration
            
            if self.enable_alerts:
                self._create_alert(
                    AlertType.RATE_LIMIT_EXCEEDED,
                    RiskLevel.MEDIUM,
                    key,
                    f"Rate limit exceeded: {count} requests in {window}s",
                    {'count': count, 'limit': limit}
                )
            
            return {"allow": False, "count": count, "retry_after": block_duration, "blocked": True}

        return {"allow": True, "count": count, "retry_after": None, "blocked": False}

    def analyze_behavior(self, identifier: str) -> Dict[str, Any]:
        """Analyze behavioral patterns for fraud indicators."""
        profile = self._profiles.get(identifier)
        
        if not profile:
            return {
                'risk_score': 0.0,
                'risk_level': RiskLevel.LOW.value,
                'indicators': [],
                'profile_exists': False
            }
        
        indicators = []
        risk_score = 0.0
        
        # Check failure ratio
        total_attempts = profile.successful_attempts + profile.failed_attempts
        if total_attempts > 5:
            failure_ratio = profile.failed_attempts / total_attempts
            if failure_ratio >= self.high_failure_ratio:
                indicators.append('high_failure_rate')
                risk_score += 0.3
                
                if self.enable_alerts:
                    self._create_alert(
                        AlertType.MULTIPLE_FAILURES,
                        RiskLevel.MEDIUM,
                        identifier,
                        f"High failure rate: {failure_ratio:.0%}",
                        {'failure_ratio': failure_ratio}
                    )
        
        # Check rapid requests
        now = self._now()
        recent_requests = [t for t in profile.request_times if t >= now - self.rapid_request_window]
        if len(recent_requests) >= self.rapid_request_threshold:
            indicators.append('rapid_requests')
            risk_score += 0.25
            
            if self.enable_alerts:
                self._create_alert(
                    AlertType.RAPID_REQUESTS,
                    RiskLevel.HIGH,
                    identifier,
                    f"Rapid requests: {len(recent_requests)} in {self.rapid_request_window}s",
                    {'request_count': len(recent_requests)}
                )
        
        # Check bot-like patterns
        if len(profile.request_intervals) >= 5:
            intervals = profile.request_intervals[-10:]
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            
            if variance < 0.5 and avg_interval < 5:
                indicators.append('bot_like_pattern')
                risk_score += 0.35
        
        # Check unusual hours
        current_hour = datetime.now().hour
        if current_hour >= self.unusual_hours_start or current_hour < self.unusual_hours_end:
            indicators.append('unusual_hours')
            risk_score += 0.1
        
        # Determine risk level
        risk_level = RiskLevel.LOW
        for level, threshold in self.risk_thresholds.items():
            if risk_score >= threshold:
                risk_level = level
        
        profile.risk_score = min(risk_score, 1.0)
        
        return {
            'risk_score': profile.risk_score,
            'risk_level': risk_level.value,
            'indicators': indicators,
            'profile_exists': True,
            'total_requests': len(profile.request_times),
            'failure_rate': profile.failed_attempts / max(total_attempts, 1)
        }

    def detect_credential_stuffing(self, phone: str, session_id: str = None) -> bool:
        """Detect potential credential stuffing attack."""
        key = f"otp_fail:{phone}"
        self._prune(key, self.otp_fail_window)
        failures = len(self._events.get(key, []))
        
        if failures >= 3:
            analysis = self.analyze_behavior(f"otp_req:{phone}")
            if analysis['risk_score'] >= 0.5:
                self._create_alert(
                    AlertType.CREDENTIAL_STUFFING,
                    RiskLevel.CRITICAL,
                    phone,
                    f"Potential credential stuffing: {failures} failures",
                    {'failures': failures, 'session_id': session_id}
                )
                return True
        
        return False

    def _create_alert(
        self,
        alert_type: AlertType,
        risk_level: RiskLevel,
        identifier: str,
        description: str,
        metadata: Dict[str, Any] = None
    ) -> FraudAlert:
        """Create and store a fraud alert."""
        alert_id = hashlib.md5(
            f"{alert_type.value}:{identifier}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        alert = FraudAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            risk_level=risk_level,
            identifier=identifier,
            description=description,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self._alerts.append(alert)
        
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]
        
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        logger.warning(f"FRAUD ALERT: [{risk_level.value}] {alert_type.value} - {description}")
        
        return alert

    def register_alert_callback(self, callback: callable):
        """Register a callback for new alerts."""
        self._alert_callbacks.append(callback)

    def get_alerts(
        self,
        risk_level: RiskLevel = None,
        alert_type: AlertType = None,
        limit: int = 100,
        unresolved_only: bool = False
    ) -> List[FraudAlert]:
        """Get alerts with optional filtering."""
        alerts = self._alerts
        
        if risk_level:
            alerts = [a for a in alerts if a.risk_level == risk_level]
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        
        return alerts[-limit:]

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                return True
        return False

    def get_risk_assessment(self, identifier: str) -> Dict[str, Any]:
        """Get comprehensive risk assessment."""
        otp_check = self.check_otp_request(identifier.replace('otp_req:', ''))
        behavior = self.analyze_behavior(f"otp_req:{identifier.replace('otp_req:', '')}")
        
        recent_alerts = [
            a.to_dict() for a in self._alerts[-20:]
            if identifier in a.identifier
        ]
        
        return {
            'identifier': identifier,
            'rate_limit_status': otp_check,
            'behavior_analysis': behavior,
            'recent_alerts': recent_alerts,
            'is_blocked': otp_check.get('blocked', False),
            'recommendation': self._get_recommendation(behavior, otp_check)
        }
    
    def _get_recommendation(self, behavior: Dict, rate_limit: Dict) -> str:
        """Get action recommendation based on risk assessment."""
        if rate_limit.get('blocked'):
            return "BLOCK: User is currently blocked"
        
        risk_score = behavior.get('risk_score', 0)
        
        if risk_score >= 0.9:
            return "BLOCK: Critical risk level"
        elif risk_score >= 0.7:
            return "CHALLENGE: High risk - require verification"
        elif risk_score >= 0.5:
            return "MONITOR: Medium risk"
        elif risk_score >= 0.3:
            return "CAUTION: Some risk indicators"
        else:
            return "ALLOW: Low risk"

    def check_otp_request(self, phone: str) -> Dict[str, Any]:
        key = f"otp_req:{phone}"
        return self.check_rate_limit(
            key, 
            limit=self.otp_limit, 
            window=self.otp_window, 
            block_duration=self.otp_block_duration
        )

    def record_otp_request(self, phone: str, success: bool = True) -> None:
        self.record_event(f"otp_req:{phone}", success=success, service="otp")

    def check_otp_failures(self, phone: str) -> Dict[str, Any]:
        key = f"otp_fail:{phone}"
        return self.check_rate_limit(
            key, 
            limit=self.otp_fail_limit, 
            window=self.otp_fail_window, 
            block_duration=self.otp_fail_block_duration
        )

    def record_otp_failure(self, phone: str) -> None:
        self.record_event(f"otp_fail:{phone}", success=False, service="otp")
        self.detect_credential_stuffing(phone)

    def get_stats(self) -> Dict[str, Any]:
        """Get fraud service statistics."""
        total_alerts = len(self._alerts)
        unresolved = sum(1 for a in self._alerts if not a.resolved)
        
        alerts_by_type = defaultdict(int)
        alerts_by_risk = defaultdict(int)
        
        for alert in self._alerts:
            alerts_by_type[alert.alert_type.value] += 1
            alerts_by_risk[alert.risk_level.value] += 1
        
        return {
            'total_alerts': total_alerts,
            'unresolved_alerts': unresolved,
            'alerts_by_type': dict(alerts_by_type),
            'alerts_by_risk': dict(alerts_by_risk),
            'active_blocks': len(self._blocklist),
            'tracked_profiles': len(self._profiles),
            'alert_callbacks_registered': len(self._alert_callbacks)
        }


# Singleton accessor
_fraud_service: Optional[FraudService] = None


def get_fraud_service() -> FraudService:
    global _fraud_service
    if _fraud_service is None:
        _fraud_service = FraudService()
    return _fraud_service


def set_fraud_service(service: FraudService) -> None:
    """Replace the global singleton."""
    global _fraud_service
    _fraud_service = service
