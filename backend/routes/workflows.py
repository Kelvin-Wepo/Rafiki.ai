"""
Workflow API Routes

Exposes workflow engine functionality via REST endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from workflows.engine import get_workflow_engine, WorkflowContext
from workflows.definitions import list_workflows, get_workflow
from utils.logger import get_logger
from utils.session_manager import session_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["Workflows"])


# Request/Response Models

class StartWorkflowRequest(BaseModel):
    """Request to start a new workflow."""
    workflow_id: str = Field(..., description="ID of workflow to start")
    session_id: str = Field(..., description="User session ID")
    language: str = Field(default="en", description="Language preference (en/sw)")
    voice_mode: bool = Field(default=False, description="Voice interaction mode")
    initial_entities: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Pre-filled entity values"
    )


class ProcessInputRequest(BaseModel):
    """Request to process user input in a workflow."""
    execution_id: str = Field(..., description="Workflow execution ID")
    user_input: str = Field(..., description="User's response")
    language: Optional[str] = Field(None, description="Language override")


class WorkflowResponse(BaseModel):
    """Standard workflow response."""
    success: bool
    execution_id: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_name: Optional[str] = None
    current_step: Optional[str] = None
    prompt: Optional[str] = None
    prompt_sw: Optional[str] = None
    entity_expected: Optional[str] = None
    requires_input: bool = False
    workflow_complete: bool = False
    entities: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error: Optional[str] = None
    validation_error: bool = False
    retry_count: int = 0


# Endpoints

@router.get(
    "/",
    summary="List available workflows",
    description="Get list of all available government service workflows"
)
async def get_workflows():
    """
    List all available workflows with their descriptions.
    
    Returns workflows for:
    - NTSA (Driving License)
    - KRA (Nil Returns, PIN)
    - DCI (Good Conduct)
    - NRB (National ID)
    - Huduma Centre lookup
    - And more...
    """
    workflows = list_workflows()
    
    return {
        "success": True,
        "workflows": workflows,
        "total_count": len(workflows)
    }


@router.get(
    "/{workflow_id}",
    summary="Get workflow details",
    description="Get detailed information about a specific workflow"
)
async def get_workflow_details(workflow_id: str):
    """
    Get details of a specific workflow including all steps.
    """
    workflow = get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found"
        )
    
    steps_summary = [
        {
            "step_id": step.step_id,
            "type": step.step_type.value,
            "entity": step.entity_name,
            "required": step.required
        }
        for step in workflow.steps
    ]
    
    return {
        "success": True,
        "workflow": {
            "workflow_id": workflow.workflow_id,
            "name_en": workflow.name_en,
            "name_sw": workflow.name_sw,
            "description_en": workflow.description_en,
            "description_sw": workflow.description_sw,
            "agency": workflow.agency,
            "estimated_time_minutes": workflow.estimated_time_minutes,
            "requires_auth": workflow.requires_auth,
            "steps": steps_summary
        }
    }


@router.post(
    "/start",
    response_model=WorkflowResponse,
    summary="Start a workflow",
    description="Start a new workflow execution"
)
async def start_workflow(request: StartWorkflowRequest):
    """
    Start a new workflow execution.
    
    - **workflow_id**: ID of the workflow to start (e.g., 'ntsa_driving_license')
    - **session_id**: Your session ID for tracking
    - **language**: 'en' for English, 'sw' for Kiswahili
    - **voice_mode**: Set to true for shorter, voice-friendly responses
    - **initial_entities**: Pre-fill known values (e.g., name, phone)
    """
    # Validate session
    session = await session_manager.get_session(request.session_id)
    if not session:
        session = await session_manager.create_session()
    
    engine = get_workflow_engine()
    
    context = WorkflowContext(
        session_id=session.session_id,
        language=request.language,
        voice_mode=request.voice_mode,
        entities=request.initial_entities or {}
    )
    
    result = await engine.start_workflow(request.workflow_id, context)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to start workflow")
        )
    
    return WorkflowResponse(
        success=True,
        execution_id=result.get("execution_id"),
        workflow_id=result.get("workflow_id"),
        workflow_name=result.get("workflow_name"),
        current_step=result.get("current_step"),
        prompt=result.get("prompt"),
        entity_expected=result.get("entity_expected"),
        requires_input=result.get("requires_input", True),
        status=result.get("status")
    )


@router.post(
    "/input",
    response_model=WorkflowResponse,
    summary="Process workflow input",
    description="Submit user input to advance a workflow"
)
async def process_workflow_input(request: ProcessInputRequest):
    """
    Process user input for an active workflow.
    
    - **execution_id**: The workflow execution ID from start_workflow
    - **user_input**: User's response to the current prompt
    - **language**: Optional language override
    """
    engine = get_workflow_engine()
    
    state = engine.get_execution(request.execution_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Workflow execution not found"
        )
    
    context = WorkflowContext(
        session_id=state.session_id,
        language=request.language or state.language
    )
    
    result = await engine.process_input(
        request.execution_id,
        request.user_input,
        context
    )
    
    return WorkflowResponse(
        success=result.get("success", False),
        execution_id=request.execution_id,
        current_step=result.get("current_step"),
        prompt=result.get("prompt"),
        entity_expected=result.get("entity_expected"),
        requires_input=result.get("requires_input", False),
        workflow_complete=result.get("workflow_complete", False),
        entities=result.get("entities"),
        status=result.get("status"),
        error=result.get("error"),
        validation_error=result.get("validation_error", False),
        retry_count=result.get("retry_count", 0)
    )


@router.get(
    "/execution/{execution_id}",
    summary="Get workflow execution state",
    description="Get the current state of a workflow execution"
)
async def get_execution_state(execution_id: str):
    """
    Get the current state of a workflow execution.
    """
    engine = get_workflow_engine()
    state = engine.get_execution(execution_id)
    
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Workflow execution not found"
        )
    
    return {
        "success": True,
        "execution": state.to_dict()
    }


@router.post(
    "/execution/{execution_id}/pause",
    summary="Pause workflow",
    description="Pause a workflow execution for later resumption"
)
async def pause_workflow(execution_id: str):
    """
    Pause an active workflow. Can be resumed later.
    """
    engine = get_workflow_engine()
    result = await engine.pause_workflow(execution_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to pause workflow")
        )
    
    return result


@router.post(
    "/execution/{execution_id}/resume",
    response_model=WorkflowResponse,
    summary="Resume workflow",
    description="Resume a paused workflow"
)
async def resume_workflow(execution_id: str, language: Optional[str] = "en"):
    """
    Resume a paused workflow execution.
    """
    engine = get_workflow_engine()
    state = engine.get_execution(execution_id)
    
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Workflow execution not found"
        )
    
    context = WorkflowContext(
        session_id=state.session_id,
        language=language
    )
    
    result = await engine.resume_workflow(execution_id, context)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to resume workflow")
        )
    
    return WorkflowResponse(
        success=True,
        execution_id=execution_id,
        current_step=result.get("current_step"),
        prompt=result.get("prompt"),
        entity_expected=result.get("entity_expected"),
        requires_input=result.get("requires_input", True),
        status=result.get("status")
    )


@router.delete(
    "/execution/{execution_id}",
    summary="Cancel workflow",
    description="Cancel a workflow execution"
)
async def cancel_workflow(execution_id: str):
    """
    Cancel an active or paused workflow.
    """
    engine = get_workflow_engine()
    result = await engine.cancel_workflow(execution_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to cancel workflow")
        )
    
    return result


@router.get(
    "/session/{session_id}",
    summary="Get session workflows",
    description="Get all workflow executions for a session"
)
async def get_session_workflows(session_id: str):
    """
    Get all workflow executions associated with a session.
    """
    engine = get_workflow_engine()
    executions = engine.get_session_executions(session_id)
    
    return {
        "success": True,
        "session_id": session_id,
        "executions": [ex.to_dict() for ex in executions],
        "total_count": len(executions)
    }
