"""
Workflow Integration Service

Bridges voice processing with the workflow engine.
Detects workflow intents and routes input to appropriate workflows.
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import re

from workflows.engine import get_workflow_engine, WorkflowContext, WorkflowStatus
from workflows.definitions import list_workflows
from utils.logger import get_logger

logger = get_logger(__name__)


# Intent to Workflow mapping
INTENT_WORKFLOW_MAP = {
    # NTSA
    "service_driving_license": "ntsa_driving_license",
    "book_driving_license": "ntsa_driving_license",
    "ntsa_appointment": "ntsa_driving_license",
    "driving_license": "ntsa_driving_license",
    "leseni": "ntsa_driving_license",
    
    # KRA
    "kra_nil_returns": "kra_nil_returns",
    "nil_returns": "kra_nil_returns",
    "file_returns": "kra_nil_returns",
    "tax_returns": "kra_nil_returns",
    "zero_returns": "kra_nil_returns",
    
    # DCI
    "service_good_conduct": "dci_good_conduct",
    "good_conduct": "dci_good_conduct",
    "police_clearance": "dci_good_conduct",
    "dci_certificate": "dci_good_conduct",
    
    # Huduma Centre
    "huduma_centre": "huduma_centre_lookup",
    "huduma_center": "huduma_centre_lookup",
    "nearest_huduma": "huduma_centre_lookup",
    "find_huduma": "huduma_centre_lookup",
    
    # Constitution
    "constitutional_qa": "constitution_query",
    "constitution": "constitution_query",
    "katiba": "constitution_query",
    "bill_of_rights": "constitution_query",
    
    # Feedback
    "feedback": "feedback_submission",
    "submit_feedback": "feedback_submission",
    "complain": "feedback_submission",
    "maoni": "feedback_submission",
    
    # Emergency
    "emergency": "emergency_report",
    "report_emergency": "emergency_report",
    "dharura": "emergency_report",
}

# Keyword patterns for detecting workflow intents
WORKFLOW_PATTERNS = [
    # NTSA Driving License
    (r"\b(book|schedule|appointment|miadi).*(driving|license|leseni)\b", "ntsa_driving_license"),
    (r"\b(driving|driver'?s?)\s*(license|licence|leseni)\b", "ntsa_driving_license"),
    (r"\b(renew|renewal|get)\s*(license|licence|leseni)\b", "ntsa_driving_license"),
    (r"\bntsa\s+(appointment|booking)\b", "ntsa_driving_license"),
    
    # KRA Nil Returns
    (r"\b(nil|zero|empty)\s*returns?\b", "kra_nil_returns"),
    (r"\b(file|submit|kufile)\s*(nil\s*)?returns?\b", "kra_nil_returns"),
    (r"\bkra\s+(nil\s*)?returns?\b", "kra_nil_returns"),
    (r"\bitax\s+(nil\s*)?returns?\b", "kra_nil_returns"),
    
    # DCI Good Conduct
    (r"\b(good\s*conduct|police\s*clearance)\b", "dci_good_conduct"),
    (r"\bdci\s*(certificate|clearance)\b", "dci_good_conduct"),
    (r"\b(certificate\s*of\s*good\s*conduct)\b", "dci_good_conduct"),
    
    # Huduma Centre
    (r"\b(nearest|find|where)\s*(is\s*)?(huduma|center|centre)\b", "huduma_centre_lookup"),
    (r"\bhuduma\s*(centre|center)\b", "huduma_centre_lookup"),
    (r"\bkituo\s*cha\s*huduma\b", "huduma_centre_lookup"),
    
    # Constitution
    (r"\b(constitution|katiba)\b", "constitution_query"),
    (r"\b(bill\s*of\s*rights|haki)\b", "constitution_query"),
    (r"\b(article|chapter|sehemu)\s*\d+\b", "constitution_query"),
    (r"\b(what\s*does\s*the\s*(constitution|law)\s*say)\b", "constitution_query"),
    
    # Feedback
    (r"\b(submit|give|leave)\s*(feedback|comment|suggestion)\b", "feedback_submission"),
    (r"\b(maoni|pendekezo|malalamiko)\b", "feedback_submission"),
    (r"\bwant\s*to\s*(complain|report)\b", "feedback_submission"),
    
    # Emergency
    (r"\b(emergency|urgent|dharura)\b", "emergency_report"),
    (r"\b(help\s*me|in\s*danger|hatari)\b", "emergency_report"),
    (r"\b(police|fire|ambulance)\s*(help|emergency)\b", "emergency_report"),
]


@dataclass
class WorkflowDetectionResult:
    """Result of workflow intent detection."""
    detected: bool
    workflow_id: Optional[str] = None
    confidence: float = 0.0
    trigger_keywords: List[str] = None
    
    def __post_init__(self):
        if self.trigger_keywords is None:
            self.trigger_keywords = []


class WorkflowIntegrationService:
    """
    Integrates workflow engine with voice/chat processing.
    
    Responsibilities:
    - Detect workflow intents from user input
    - Start appropriate workflows
    - Route input to active workflows
    - Return formatted responses
    """
    
    def __init__(self):
        self._engine = None
        self._active_sessions: Dict[str, str] = {}  # session_id -> execution_id
        logger.info("WorkflowIntegrationService initialized")
    
    @property
    def engine(self):
        """Lazy-load workflow engine."""
        if self._engine is None:
            self._engine = get_workflow_engine()
        return self._engine
    
    def detect_workflow_intent(
        self,
        text: str,
        current_intent: Optional[str] = None,
        confidence: float = 0.0
    ) -> WorkflowDetectionResult:
        """
        Detect if user input triggers a workflow.
        
        Args:
            text: User input text
            current_intent: Intent from dialogflow/existing detection
            confidence: Confidence of existing detection
            
        Returns:
            WorkflowDetectionResult with workflow_id if detected
        """
        text_lower = text.lower().strip()
        
        # 1. Check if current_intent maps to a workflow
        if current_intent and current_intent in INTENT_WORKFLOW_MAP:
            workflow_id = INTENT_WORKFLOW_MAP[current_intent]
            logger.info(f"Mapped intent '{current_intent}' to workflow '{workflow_id}'")
            return WorkflowDetectionResult(
                detected=True,
                workflow_id=workflow_id,
                confidence=max(confidence, 0.8),
                trigger_keywords=[current_intent]
            )
        
        # 2. Pattern matching against workflow keywords
        for pattern, workflow_id in WORKFLOW_PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                logger.info(f"Pattern matched: '{pattern}' -> '{workflow_id}'")
                return WorkflowDetectionResult(
                    detected=True,
                    workflow_id=workflow_id,
                    confidence=0.85,
                    trigger_keywords=[match.group(0)]
                )
        
        # 3. No workflow detected
        return WorkflowDetectionResult(detected=False)
    
    def has_active_workflow(self, session_id: str) -> bool:
        """Check if session has an active workflow."""
        if session_id not in self._active_sessions:
            return False
        
        execution_id = self._active_sessions[session_id]
        state = self.engine.get_execution(execution_id)
        
        if state is None:
            del self._active_sessions[session_id]
            return False
        
        return state.status in [
            WorkflowStatus.AWAITING_INPUT,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.PAUSED
        ]
    
    def get_active_execution_id(self, session_id: str) -> Optional[str]:
        """Get active execution ID for session."""
        return self._active_sessions.get(session_id)
    
    async def start_workflow(
        self,
        workflow_id: str,
        session_id: str,
        language: str = "en",
        voice_mode: bool = True,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a workflow for the session.
        
        Args:
            workflow_id: ID of workflow to start
            session_id: User session ID
            language: Language code (en/sw)
            voice_mode: Whether this is voice interaction
            user_id: Optional user ID
            
        Returns:
            Workflow start response
        """
        # Cancel any existing workflow for this session
        if session_id in self._active_sessions:
            old_execution_id = self._active_sessions[session_id]
            try:
                await self.engine.cancel_workflow(old_execution_id)
            except Exception:
                pass
        
        # Create workflow context
        context = WorkflowContext(
            session_id=session_id,
            user_id=user_id,
            language=language,
            voice_mode=voice_mode
        )
        
        # Start the workflow
        result = await self.engine.start_workflow(workflow_id, context)
        
        if result.get("success"):
            execution_id = result["execution_id"]
            self._active_sessions[session_id] = execution_id
            logger.info(f"Started workflow '{workflow_id}' for session '{session_id}' -> execution '{execution_id}'")
        
        return result
    
    async def process_input(
        self,
        session_id: str,
        user_input: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process user input for active workflow.
        
        Args:
            session_id: User session ID
            user_input: User's input text
            language: Language code
            
        Returns:
            Workflow response
        """
        execution_id = self._active_sessions.get(session_id)
        
        if not execution_id:
            return {
                "success": False,
                "error": "No active workflow",
                "requires_workflow_detection": True
            }
        
        context = WorkflowContext(
            session_id=session_id,
            language=language
        )
        
        result = await self.engine.process_input(execution_id, user_input, context)
        
        # Clean up completed/cancelled workflows
        if result.get("workflow_complete") or result.get("status") == "cancelled":
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
        
        return result
    
    async def handle_voice_input(
        self,
        user_text: str,
        session_id: str,
        language: str = "en",
        current_intent: Optional[str] = None,
        intent_confidence: float = 0.0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Main entry point for voice input handling.
        
        Returns:
            Tuple of (handled_by_workflow, response_dict)
        """
        # 1. Check for active workflow first
        if self.has_active_workflow(session_id):
            logger.info(f"[WORKFLOW] Active workflow for session '{session_id}', routing input")
            result = await self.process_input(session_id, user_text, language)
            return True, self._format_workflow_response(result, language)
        
        # 2. Detect if this should start a workflow
        detection = self.detect_workflow_intent(
            user_text,
            current_intent,
            intent_confidence
        )
        
        if detection.detected and detection.workflow_id:
            logger.info(f"[WORKFLOW] Starting workflow '{detection.workflow_id}' for session '{session_id}'")
            result = await self.start_workflow(
                detection.workflow_id,
                session_id,
                language=language,
                voice_mode=True
            )
            return True, self._format_workflow_response(result, language)
        
        # 3. Not a workflow request
        return False, {}
    
    def _format_workflow_response(
        self,
        result: Dict[str, Any],
        language: str
    ) -> Dict[str, Any]:
        """Format workflow result for voice response."""
        if not result.get("success"):
            error_msg = result.get("error", "An error occurred")
            if language == "sw":
                error_msg = result.get("error_sw", error_msg)
            return {
                "text": error_msg,
                "intent": "workflow_error",
                "requires_input": True,
                "workflow_active": False
            }
        
        response = {
            "text": result.get("prompt", ""),
            "intent": f"workflow_{result.get('workflow_id', 'unknown')}",
            "requires_input": result.get("requires_input", True),
            "workflow_active": not result.get("workflow_complete", False),
            "workflow_context": {
                "workflow_id": result.get("workflow_id"),
                "workflow_name": result.get("workflow_name"),
                "current_step": result.get("current_step"),
                "progress": result.get("progress"),
                "execution_id": result.get("execution_id")
            }
        }
        
        # Add validation error info if present
        if result.get("validation_error"):
            response["validation_error"] = True
            response["retry_count"] = result.get("retry_count", 0)
        
        # Add completion info if workflow is done
        if result.get("workflow_complete"):
            response["workflow_complete"] = True
            response["entities"] = result.get("entities", {})
        
        return response
    
    async def cancel_workflow(self, session_id: str) -> Dict[str, Any]:
        """Cancel active workflow for session."""
        execution_id = self._active_sessions.get(session_id)
        
        if not execution_id:
            return {"success": False, "error": "No active workflow"}
        
        result = await self.engine.cancel_workflow(execution_id)
        
        if result.get("success"):
            del self._active_sessions[session_id]
        
        return result
    
    async def pause_workflow(self, session_id: str) -> Dict[str, Any]:
        """Pause active workflow for session."""
        execution_id = self._active_sessions.get(session_id)
        
        if not execution_id:
            return {"success": False, "error": "No active workflow"}
        
        return await self.engine.pause_workflow(execution_id)
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows."""
        return [
            {
                "id": wf_id,
                "name": info.get("name_en", wf_id),
                "name_sw": info.get("name_sw", wf_id),
                "description": info.get("description_en", ""),
                "agency": info.get("agency", "")
            }
            for wf_id, info in list_workflows().items()
        ]


# Singleton instance
_workflow_integration: Optional[WorkflowIntegrationService] = None


def get_workflow_integration() -> WorkflowIntegrationService:
    """Get workflow integration service singleton."""
    global _workflow_integration
    if _workflow_integration is None:
        _workflow_integration = WorkflowIntegrationService()
    return _workflow_integration
