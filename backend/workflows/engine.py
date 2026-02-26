"""
Workflow Engine Core

Implements a state machine for multi-step government service workflows.
Supports:
- Step-by-step guidance with prompts
- Entity extraction and validation
- State persistence for interruption/resumption
- Voice-friendly responses (short mode)
- Bilingual support (English/Kiswahili)
"""

import uuid
import re
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AWAITING_INPUT = "awaiting_input"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Type of workflow step."""
    PROMPT = "prompt"           # Ask user for information
    CONFIRM = "confirm"         # Ask user to confirm details
    ACTION = "action"           # Execute an action (API call, SMS, etc.)
    BRANCH = "branch"           # Conditional branching
    INFO = "info"               # Provide information only
    COMPLETE = "complete"       # Workflow completion


@dataclass
class ValidationResult:
    """Result of input validation."""
    valid: bool
    value: Any = None
    error_message: Optional[str] = None
    error_message_sw: Optional[str] = None  # Kiswahili error


@dataclass
class StepDefinition:
    """Definition of a single workflow step."""
    step_id: str
    step_type: StepType
    prompt_en: str
    prompt_sw: str
    next_step: Optional[str] = None
    entity_name: Optional[str] = None           # Name of entity to extract
    validator: Optional[str] = None             # Validator function name
    required: bool = True
    branches: Optional[Dict[str, str]] = None   # For BRANCH type: condition -> next_step
    action_handler: Optional[str] = None        # For ACTION type: handler function
    retry_prompt_en: Optional[str] = None       # Prompt on validation failure
    retry_prompt_sw: Optional[str] = None
    max_retries: int = 3
    skip_conditions: Optional[List[str]] = None  # Conditions to skip this step


@dataclass
class WorkflowDefinition:
    """Definition of a complete workflow."""
    workflow_id: str
    name_en: str
    name_sw: str
    description_en: str
    description_sw: str
    agency: str
    steps: List[StepDefinition]
    initial_step: str
    completion_message_en: str
    completion_message_sw: str
    requires_auth: bool = False
    estimated_time_minutes: int = 5
    
    def get_step(self, step_id: str) -> Optional[StepDefinition]:
        """Get step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None


@dataclass
class WorkflowState:
    """Current state of a workflow execution."""
    execution_id: str
    workflow_id: str
    session_id: str
    status: WorkflowStatus
    current_step: str
    entities: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    error_message: Optional[str] = None
    language: str = "en"  # User's preferred language
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "entities": self.entities,
            "history": self.history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "language": self.language
        }


@dataclass 
class WorkflowContext:
    """Context for workflow execution."""
    session_id: str
    user_id: Optional[str] = None
    language: str = "en"
    voice_mode: bool = False
    short_responses: bool = False  # For voice accessibility
    entities: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """
    Executes workflows using a state machine pattern.
    
    Usage:
        engine = WorkflowEngine()
        result = await engine.start_workflow("ntsa_driving_license", session_id)
        result = await engine.process_input(execution_id, user_input)
    """
    
    # Validators for common entity types
    VALIDATORS = {
        "phone_ke": r"^(\+254|254|0)?[17]\d{8}$",
        "national_id": r"^\d{7,8}$",
        "kra_pin": r"^[A-Z]\d{9}[A-Z]$",
        "email": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        "date": r"^\d{4}-\d{2}-\d{2}$",
        "yes_no": r"^(yes|no|ndio|hapana|y|n)$",
        "name": r"^[a-zA-Z\s\-\']{2,100}$",
    }
    
    def __init__(self):
        """Initialize workflow engine."""
        self._executions: Dict[str, WorkflowState] = {}
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._action_handlers: Dict[str, Callable] = {}
        
        # Register built-in action handlers
        self._register_default_handlers()
        
        logger.info("WorkflowEngine initialized")
    
    def _register_default_handlers(self):
        """Register default action handlers."""
        self._action_handlers["send_sms_confirmation"] = self._handle_send_sms
        self._action_handlers["create_booking"] = self._handle_create_booking
        self._action_handlers["log_audit"] = self._handle_audit_log
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition."""
        self._workflows[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.workflow_id}")
    
    def register_action_handler(self, name: str, handler: Callable):
        """Register a custom action handler."""
        self._action_handlers[name] = handler
    
    async def start_workflow(
        self,
        workflow_id: str,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """
        Start a new workflow execution.
        
        Args:
            workflow_id: ID of workflow to start
            context: Workflow context with session info
            
        Returns:
            Initial prompt and execution state
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return {
                "success": False,
                "error": f"Workflow '{workflow_id}' not found",
                "available_workflows": list(self._workflows.keys())
            }
        
        # Create execution state
        execution_id = str(uuid.uuid4())[:12]
        state = WorkflowState(
            execution_id=execution_id,
            workflow_id=workflow_id,
            session_id=context.session_id,
            status=WorkflowStatus.AWAITING_INPUT,
            current_step=workflow.initial_step,
            entities=context.entities.copy(),
            language=context.language
        )
        
        self._executions[execution_id] = state
        
        # Get initial step prompt
        step = workflow.get_step(workflow.initial_step)
        if not step:
            return {
                "success": False,
                "error": f"Initial step '{workflow.initial_step}' not found"
            }
        
        # Log workflow start
        state.history.append({
            "event": "workflow_started",
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "step": workflow.initial_step
        })
        
        prompt = step.prompt_sw if context.language == "sw" else step.prompt_en
        
        return {
            "success": True,
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow.name_sw if context.language == "sw" else workflow.name_en,
            "current_step": step.step_id,
            "prompt": prompt,
            "entity_expected": step.entity_name,
            "status": state.status.value,
            "requires_input": step.step_type in [StepType.PROMPT, StepType.CONFIRM]
        }
    
    async def process_input(
        self,
        execution_id: str,
        user_input: str,
        context: Optional[WorkflowContext] = None
    ) -> Dict[str, Any]:
        """
        Process user input and advance workflow.
        
        Args:
            execution_id: Workflow execution ID
            user_input: User's response
            context: Optional updated context
            
        Returns:
            Next prompt or completion status
        """
        state = self._executions.get(execution_id)
        if not state:
            return {
                "success": False,
                "error": "Workflow execution not found",
                "execution_id": execution_id
            }
        
        if state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return {
                "success": False,
                "error": f"Workflow is already {state.status.value}",
                "execution_id": execution_id
            }
        
        workflow = self._workflows.get(state.workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow definition not found"}
        
        current_step = workflow.get_step(state.current_step)
        if not current_step:
            return {"success": False, "error": f"Step '{state.current_step}' not found"}
        
        lang = context.language if context else state.language
        
        # Validate input if required
        if current_step.validator:
            validation = self._validate_input(user_input, current_step.validator)
            if not validation.valid:
                state.retry_count += 1
                
                if state.retry_count >= current_step.max_retries:
                    state.status = WorkflowStatus.FAILED
                    state.error_message = "Maximum retries exceeded"
                    return {
                        "success": False,
                        "error": "Maximum retries exceeded. Please start again.",
                        "execution_id": execution_id,
                        "status": state.status.value
                    }
                
                retry_prompt = (
                    current_step.retry_prompt_sw if lang == "sw" else current_step.retry_prompt_en
                ) or (
                    validation.error_message_sw if lang == "sw" else validation.error_message
                )
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "current_step": current_step.step_id,
                    "prompt": retry_prompt or "Invalid input. Please try again.",
                    "validation_error": True,
                    "retry_count": state.retry_count,
                    "requires_input": True
                }
            
            user_input = validation.value  # Use normalized value
        
        # Store entity if this step extracts one
        if current_step.entity_name:
            state.entities[current_step.entity_name] = user_input
            state.history.append({
                "event": "entity_captured",
                "timestamp": datetime.utcnow().isoformat(),
                "entity": current_step.entity_name,
                "step": current_step.step_id
            })
        
        # Determine next step
        next_step_id = self._determine_next_step(current_step, user_input, state)
        
        if not next_step_id:
            # Workflow complete
            state.status = WorkflowStatus.COMPLETED
            state.updated_at = datetime.utcnow()
            state.history.append({
                "event": "workflow_completed",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            completion_msg = workflow.completion_message_sw if lang == "sw" else workflow.completion_message_en
            
            # Substitute entities into completion message
            completion_msg = self._substitute_entities(completion_msg, state.entities)
            
            return {
                "success": True,
                "execution_id": execution_id,
                "status": state.status.value,
                "prompt": completion_msg,
                "entities": state.entities,
                "requires_input": False,
                "workflow_complete": True
            }
        
        # Move to next step
        next_step = workflow.get_step(next_step_id)
        if not next_step:
            return {"success": False, "error": f"Next step '{next_step_id}' not found"}
        
        state.current_step = next_step_id
        state.retry_count = 0
        state.updated_at = datetime.utcnow()
        
        state.history.append({
            "event": "step_transition",
            "timestamp": datetime.utcnow().isoformat(),
            "from_step": current_step.step_id,
            "to_step": next_step_id
        })
        
        # Handle ACTION steps
        if next_step.step_type == StepType.ACTION:
            action_result = await self._execute_action(next_step, state, context)
            if not action_result.get("success"):
                state.status = WorkflowStatus.FAILED
                state.error_message = action_result.get("error")
                return action_result
            
            # After action, move to next step
            return await self.process_input(execution_id, "", context)
        
        # Handle INFO steps (auto-advance)
        if next_step.step_type == StepType.INFO:
            prompt = next_step.prompt_sw if lang == "sw" else next_step.prompt_en
            prompt = self._substitute_entities(prompt, state.entities)
            
            # Auto-advance to next step if defined
            if next_step.next_step:
                state.current_step = next_step.next_step
                state.history.append({
                    "event": "info_displayed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "step": next_step_id
                })
                
                following_step = workflow.get_step(next_step.next_step)
                if following_step:
                    following_prompt = following_step.prompt_sw if lang == "sw" else following_step.prompt_en
                    prompt += "\n\n" + self._substitute_entities(following_prompt, state.entities)
                    return {
                        "success": True,
                        "execution_id": execution_id,
                        "current_step": next_step.next_step,
                        "prompt": prompt,
                        "entity_expected": following_step.entity_name,
                        "requires_input": following_step.step_type in [StepType.PROMPT, StepType.CONFIRM],
                        "status": state.status.value
                    }
        
        prompt = next_step.prompt_sw if lang == "sw" else next_step.prompt_en
        prompt = self._substitute_entities(prompt, state.entities)
        
        return {
            "success": True,
            "execution_id": execution_id,
            "current_step": next_step_id,
            "prompt": prompt,
            "entity_expected": next_step.entity_name,
            "requires_input": next_step.step_type in [StepType.PROMPT, StepType.CONFIRM],
            "status": state.status.value
        }
    
    def _validate_input(self, value: str, validator_name: str) -> ValidationResult:
        """Validate user input against a validator."""
        value = value.strip()
        
        if validator_name in self.VALIDATORS:
            pattern = self.VALIDATORS[validator_name]
            if re.match(pattern, value, re.IGNORECASE):
                # Normalize certain values
                if validator_name == "phone_ke":
                    value = self._normalize_phone(value)
                elif validator_name == "kra_pin":
                    value = value.upper()
                elif validator_name == "yes_no":
                    value = "yes" if value.lower() in ["yes", "y", "ndio"] else "no"
                
                return ValidationResult(valid=True, value=value)
            else:
                return ValidationResult(
                    valid=False,
                    error_message=f"Invalid format for {validator_name}",
                    error_message_sw=f"Muundo batili kwa {validator_name}"
                )
        
        # Custom validators can be added here
        return ValidationResult(valid=True, value=value)
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize Kenyan phone number to +254 format."""
        phone = re.sub(r'[\s\-]', '', phone)
        if phone.startswith('0'):
            return '+254' + phone[1:]
        elif phone.startswith('254'):
            return '+' + phone
        elif not phone.startswith('+'):
            return '+254' + phone
        return phone
    
    def _determine_next_step(
        self,
        current: StepDefinition,
        user_input: str,
        state: WorkflowState
    ) -> Optional[str]:
        """Determine the next step based on current step and input."""
        
        # Handle branching
        if current.step_type == StepType.BRANCH and current.branches:
            normalized_input = user_input.lower().strip()
            for condition, next_step in current.branches.items():
                if condition.lower() in normalized_input or normalized_input in condition.lower():
                    return next_step
            # Default branch
            return current.branches.get("default", current.next_step)
        
        # Handle confirmation
        if current.step_type == StepType.CONFIRM:
            if user_input.lower() in ["yes", "y", "ndio", "confirm", "proceed"]:
                return current.next_step
            else:
                return current.branches.get("no") if current.branches else None
        
        return current.next_step
    
    def _substitute_entities(self, text: str, entities: Dict[str, Any]) -> str:
        """Substitute entity placeholders in text."""
        for key, value in entities.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text
    
    async def _execute_action(
        self,
        step: StepDefinition,
        state: WorkflowState,
        context: Optional[WorkflowContext]
    ) -> Dict[str, Any]:
        """Execute an action step."""
        if not step.action_handler:
            return {"success": True}
        
        handler = self._action_handlers.get(step.action_handler)
        if not handler:
            logger.warning(f"Action handler '{step.action_handler}' not found")
            return {"success": True}  # Skip if handler not found
        
        try:
            return await handler(state, context)
        except Exception as e:
            logger.error(f"Action handler '{step.action_handler}' failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Default action handlers
    async def _handle_send_sms(
        self,
        state: WorkflowState,
        context: Optional[WorkflowContext]
    ) -> Dict[str, Any]:
        """Send SMS confirmation."""
        from services.sms_service import sms_service
        
        phone = state.entities.get("phone_number")
        if not phone:
            return {"success": False, "error": "No phone number in entities"}
        
        # Build message from entities
        message = f"Rafiki Confirmation: Your {state.workflow_id.replace('_', ' ')} request has been received. "
        if state.entities.get("booking_id"):
            message += f"Reference: {state.entities['booking_id']}. "
        message += "Thank you for using Rafiki."
        
        result = await sms_service.send_sms(phone, message)
        return result
    
    async def _handle_create_booking(
        self,
        state: WorkflowState,
        context: Optional[WorkflowContext]
    ) -> Dict[str, Any]:
        """Create a booking record."""
        from services.booking_service import booking_service
        from models.schemas import ServiceType, TimeSlot
        
        try:
            service_type = ServiceType(state.entities.get("service_type", "driving_license"))
            time_slot = TimeSlot(state.entities.get("time_slot", "08:00-12:00"))
            
            from datetime import date, timedelta
            # Default to next business day if not specified
            appointment_date = state.entities.get("appointment_date")
            if not appointment_date:
                appointment_date = date.today() + timedelta(days=1)
            elif isinstance(appointment_date, str):
                appointment_date = date.fromisoformat(appointment_date)
            
            result = await booking_service.create_booking(
                service_type=service_type,
                user_name=state.entities.get("full_name", "Unknown"),
                phone_number=state.entities.get("phone_number", ""),
                time_slot=time_slot,
                appointment_date=appointment_date,
                additional_notes=state.entities.get("notes"),
                send_sms=True
            )
            
            if result.get("success"):
                state.entities["booking_id"] = result.get("booking_id")
            
            return result
        except Exception as e:
            logger.error(f"Booking creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_audit_log(
        self,
        state: WorkflowState,
        context: Optional[WorkflowContext]
    ) -> Dict[str, Any]:
        """Log to audit trail."""
        # This will be implemented with the audit service
        logger.info(f"AUDIT: Workflow {state.workflow_id} completed for session {state.session_id}")
        return {"success": True}
    
    # Utility methods
    def get_execution(self, execution_id: str) -> Optional[WorkflowState]:
        """Get workflow execution state."""
        return self._executions.get(execution_id)
    
    def get_session_executions(self, session_id: str) -> List[WorkflowState]:
        """Get all executions for a session."""
        return [
            ex for ex in self._executions.values()
            if ex.session_id == session_id
        ]
    
    async def pause_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Pause a workflow execution."""
        state = self._executions.get(execution_id)
        if not state:
            return {"success": False, "error": "Execution not found"}
        
        if state.status not in [WorkflowStatus.IN_PROGRESS, WorkflowStatus.AWAITING_INPUT]:
            return {"success": False, "error": f"Cannot pause workflow in {state.status.value} state"}
        
        state.status = WorkflowStatus.PAUSED
        state.updated_at = datetime.utcnow()
        state.history.append({
            "event": "workflow_paused",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {"success": True, "execution_id": execution_id, "status": "paused"}
    
    async def resume_workflow(
        self,
        execution_id: str,
        context: Optional[WorkflowContext] = None
    ) -> Dict[str, Any]:
        """Resume a paused workflow."""
        state = self._executions.get(execution_id)
        if not state:
            return {"success": False, "error": "Execution not found"}
        
        if state.status != WorkflowStatus.PAUSED:
            return {"success": False, "error": f"Workflow is not paused (status: {state.status.value})"}
        
        state.status = WorkflowStatus.AWAITING_INPUT
        state.updated_at = datetime.utcnow()
        state.history.append({
            "event": "workflow_resumed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        workflow = self._workflows.get(state.workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow definition not found"}
        
        step = workflow.get_step(state.current_step)
        if not step:
            return {"success": False, "error": "Current step not found"}
        
        lang = context.language if context else state.language
        prompt = step.prompt_sw if lang == "sw" else step.prompt_en
        prompt = self._substitute_entities(prompt, state.entities)
        
        return {
            "success": True,
            "execution_id": execution_id,
            "current_step": state.current_step,
            "prompt": f"Welcome back! {prompt}",
            "entity_expected": step.entity_name,
            "requires_input": True,
            "status": state.status.value
        }
    
    async def cancel_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Cancel a workflow execution."""
        state = self._executions.get(execution_id)
        if not state:
            return {"success": False, "error": "Execution not found"}
        
        state.status = WorkflowStatus.CANCELLED
        state.updated_at = datetime.utcnow()
        state.history.append({
            "event": "workflow_cancelled",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "execution_id": execution_id,
            "message": "Workflow has been cancelled."
        }


# Global workflow engine instance
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get or create the workflow engine singleton."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
        # Register all workflow definitions
        from workflows.definitions import register_all_workflows
        from workflows.handlers import register_action_handlers
        register_all_workflows(_workflow_engine)
        register_action_handlers(_workflow_engine)
    return _workflow_engine
