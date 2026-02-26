"""
Tests for the Workflow Engine

Tests cover:
- Workflow registration and listing
- Starting workflows
- Processing input
- Entity validation
- State transitions
- Pause/resume
- Action handlers
"""

import pytest
import asyncio
from datetime import datetime

from workflows.engine import (
    WorkflowEngine,
    WorkflowState,
    WorkflowContext,
    WorkflowStatus,
    StepType,
    StepDefinition,
    WorkflowDefinition,
    ValidationResult
)
from workflows.definitions import (
    list_workflows,
    get_workflow,
    get_ntsa_driving_license_workflow,
    get_kra_nil_returns_workflow
)


@pytest.fixture
def engine():
    """Create a fresh workflow engine for each test."""
    return WorkflowEngine()


@pytest.fixture
def sample_workflow():
    """Create a simple test workflow."""
    return WorkflowDefinition(
        workflow_id="test_workflow",
        name_en="Test Workflow",
        name_sw="Mkakati wa Majaribio",
        description_en="A test workflow",
        description_sw="Mkakati wa majaribio",
        agency="Test Agency",
        initial_step="step1",
        completion_message_en="Test complete! Name: {name}",
        completion_message_sw="Majaribio yamekamilika! Jina: {name}",
        steps=[
            StepDefinition(
                step_id="step1",
                step_type=StepType.PROMPT,
                prompt_en="What is your name?",
                prompt_sw="Jina lako ni nani?",
                entity_name="name",
                validator="name",
                next_step="step2"
            ),
            StepDefinition(
                step_id="step2",
                step_type=StepType.PROMPT,
                prompt_en="Hello {name}! What is your phone?",
                prompt_sw="Habari {name}! Nambari yako ya simu?",
                entity_name="phone",
                validator="phone_ke",
                next_step="step3"
            ),
            StepDefinition(
                step_id="step3",
                step_type=StepType.CONFIRM,
                prompt_en="Confirm: Name={name}, Phone={phone}? (Yes/No)",
                prompt_sw="Thibitisha: Jina={name}, Simu={phone}? (Ndio/Hapana)",
                next_step=None,
                branches={"no": "step1"}
            )
        ]
    )


@pytest.fixture
def context():
    """Create a test context."""
    return WorkflowContext(
        session_id="test-session-123",
        language="en",
        voice_mode=False
    )


class TestWorkflowDefinitions:
    """Tests for workflow definitions."""
    
    def test_list_workflows_returns_all(self):
        """Test that list_workflows returns all defined workflows."""
        workflows = list_workflows()
        
        assert len(workflows) >= 7
        assert "ntsa_driving_license" in workflows
        assert "kra_nil_returns" in workflows
        assert "dci_good_conduct" in workflows
        assert "huduma_centre_lookup" in workflows
        assert "constitution_query" in workflows
    
    def test_get_workflow_returns_definition(self):
        """Test that get_workflow returns a valid definition."""
        workflow = get_workflow("ntsa_driving_license")
        
        assert workflow is not None
        assert workflow.workflow_id == "ntsa_driving_license"
        assert workflow.agency == "NTSA"
        assert len(workflow.steps) > 0
    
    def test_get_workflow_returns_none_for_unknown(self):
        """Test that get_workflow returns None for unknown workflows."""
        workflow = get_workflow("nonexistent_workflow")
        assert workflow is None
    
    def test_ntsa_workflow_has_required_steps(self):
        """Test NTSA workflow has all required steps."""
        workflow = get_ntsa_driving_license_workflow()
        
        step_ids = [s.step_id for s in workflow.steps]
        assert "welcome" in step_ids
        assert "full_name" in step_ids
        assert "national_id" in step_ids
        assert "phone_number" in step_ids
        assert "confirm_details" in step_ids
    
    def test_kra_workflow_has_required_steps(self):
        """Test KRA nil returns workflow has all required steps."""
        workflow = get_kra_nil_returns_workflow()
        
        step_ids = [s.step_id for s in workflow.steps]
        assert "welcome" in step_ids
        assert "check_pin" in step_ids
        assert "itax_login_guide" in step_ids


class TestWorkflowEngine:
    """Tests for the workflow engine."""
    
    def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine._executions == {}
        assert engine._workflows == {}
        assert len(engine._action_handlers) > 0  # Built-in handlers
    
    def test_register_workflow(self, engine, sample_workflow):
        """Test workflow registration."""
        engine.register_workflow(sample_workflow)
        
        assert "test_workflow" in engine._workflows
        assert engine._workflows["test_workflow"] == sample_workflow
    
    @pytest.mark.asyncio
    async def test_start_workflow(self, engine, sample_workflow, context):
        """Test starting a workflow."""
        engine.register_workflow(sample_workflow)
        
        result = await engine.start_workflow("test_workflow", context)
        
        assert result["success"] is True
        assert "execution_id" in result
        assert result["workflow_id"] == "test_workflow"
        assert result["current_step"] == "step1"
        assert "What is your name?" in result["prompt"]
        assert result["requires_input"] is True
    
    @pytest.mark.asyncio
    async def test_start_unknown_workflow(self, engine, context):
        """Test starting an unknown workflow."""
        result = await engine.start_workflow("unknown", context)
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_process_input_valid(self, engine, sample_workflow, context):
        """Test processing valid input."""
        engine.register_workflow(sample_workflow)
        
        # Start workflow
        start_result = await engine.start_workflow("test_workflow", context)
        execution_id = start_result["execution_id"]
        
        # Provide valid name
        result = await engine.process_input(execution_id, "John Doe", context)
        
        assert result["success"] is True
        assert result["current_step"] == "step2"
        assert "John Doe" in result["prompt"]  # Name substituted
    
    @pytest.mark.asyncio
    async def test_process_input_invalid(self, engine, sample_workflow, context):
        """Test processing invalid input."""
        engine.register_workflow(sample_workflow)
        
        # Start workflow
        start_result = await engine.start_workflow("test_workflow", context)
        execution_id = start_result["execution_id"]
        
        # Provide invalid name (numbers)
        result = await engine.process_input(execution_id, "12345", context)
        
        assert result["success"] is True
        assert result["validation_error"] is True
        assert result["retry_count"] == 1
        assert result["current_step"] == "step1"  # Still on same step
    
    @pytest.mark.asyncio
    async def test_workflow_completion(self, engine, sample_workflow, context):
        """Test completing a workflow."""
        engine.register_workflow(sample_workflow)
        
        # Start workflow
        start_result = await engine.start_workflow("test_workflow", context)
        execution_id = start_result["execution_id"]
        
        # Step 1: Name
        await engine.process_input(execution_id, "Jane Doe", context)
        
        # Step 2: Phone
        await engine.process_input(execution_id, "0712345678", context)
        
        # Step 3: Confirm
        result = await engine.process_input(execution_id, "yes", context)
        
        assert result["success"] is True
        assert result["workflow_complete"] is True
        assert result["status"] == "completed"
        assert "Jane Doe" in result["prompt"]  # Entity substituted


class TestValidation:
    """Tests for input validation."""
    
    def test_validate_phone_valid(self, engine):
        """Test valid Kenyan phone numbers."""
        valid_phones = [
            "0712345678",
            "+254712345678",
            "254712345678",
        ]
        
        for phone in valid_phones:
            result = engine._validate_input(phone, "phone_ke")
            assert result.valid, f"Should accept: {phone}"
    
    def test_validate_phone_invalid(self, engine):
        """Test invalid phone numbers."""
        invalid_phones = [
            "123",
            "0812345678",  # Invalid prefix
            "07123456789",  # Too long
        ]
        
        for phone in invalid_phones:
            result = engine._validate_input(phone, "phone_ke")
            assert not result.valid, f"Should reject: {phone}"
    
    def test_validate_national_id(self, engine):
        """Test National ID validation."""
        assert engine._validate_input("12345678", "national_id").valid
        assert engine._validate_input("1234567", "national_id").valid
        assert not engine._validate_input("123", "national_id").valid
        assert not engine._validate_input("123456789", "national_id").valid
    
    def test_validate_kra_pin(self, engine):
        """Test KRA PIN validation."""
        assert engine._validate_input("A123456789B", "kra_pin").valid
        assert engine._validate_input("P051234567Q", "kra_pin").valid
        assert not engine._validate_input("123456789", "kra_pin").valid
        assert not engine._validate_input("AB12345678C", "kra_pin").valid
    
    def test_validate_yes_no(self, engine):
        """Test yes/no validation."""
        yes_values = ["yes", "Yes", "YES", "y", "Y", "ndio", "Ndio"]
        no_values = ["no", "No", "NO", "n", "N", "hapana", "Hapana"]
        
        for val in yes_values:
            result = engine._validate_input(val, "yes_no")
            assert result.valid
            assert result.value == "yes"
        
        for val in no_values:
            result = engine._validate_input(val, "yes_no")
            assert result.valid
            assert result.value == "no"


class TestWorkflowState:
    """Tests for workflow state management."""
    
    @pytest.mark.asyncio
    async def test_pause_workflow(self, engine, sample_workflow, context):
        """Test pausing a workflow."""
        engine.register_workflow(sample_workflow)
        
        start_result = await engine.start_workflow("test_workflow", context)
        execution_id = start_result["execution_id"]
        
        # Pause
        pause_result = await engine.pause_workflow(execution_id)
        
        assert pause_result["success"] is True
        
        state = engine.get_execution(execution_id)
        assert state.status == WorkflowStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_resume_workflow(self, engine, sample_workflow, context):
        """Test resuming a paused workflow."""
        engine.register_workflow(sample_workflow)
        
        start_result = await engine.start_workflow("test_workflow", context)
        execution_id = start_result["execution_id"]
        
        # Pause then resume
        await engine.pause_workflow(execution_id)
        resume_result = await engine.resume_workflow(execution_id, context)
        
        assert resume_result["success"] is True
        assert "Welcome back" in resume_result["prompt"]
        
        state = engine.get_execution(execution_id)
        assert state.status == WorkflowStatus.AWAITING_INPUT
    
    @pytest.mark.asyncio
    async def test_cancel_workflow(self, engine, sample_workflow, context):
        """Test cancelling a workflow."""
        engine.register_workflow(sample_workflow)
        
        start_result = await engine.start_workflow("test_workflow", context)
        execution_id = start_result["execution_id"]
        
        cancel_result = await engine.cancel_workflow(execution_id)
        
        assert cancel_result["success"] is True
        
        state = engine.get_execution(execution_id)
        assert state.status == WorkflowStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_get_session_executions(self, engine, sample_workflow, context):
        """Test getting all executions for a session."""
        engine.register_workflow(sample_workflow)
        
        # Start multiple workflows
        await engine.start_workflow("test_workflow", context)
        await engine.start_workflow("test_workflow", context)
        
        executions = engine.get_session_executions(context.session_id)
        
        assert len(executions) == 2


class TestKiswahiliSupport:
    """Tests for Kiswahili language support."""
    
    @pytest.mark.asyncio
    async def test_kiswahili_prompts(self, engine, sample_workflow):
        """Test that Kiswahili prompts are returned when language is sw."""
        engine.register_workflow(sample_workflow)
        
        context = WorkflowContext(
            session_id="test-sw",
            language="sw"
        )
        
        result = await engine.start_workflow("test_workflow", context)
        
        assert "Jina lako ni nani?" in result["prompt"]
    
    def test_workflow_has_bilingual_messages(self):
        """Test that all workflows have both English and Kiswahili messages."""
        workflows = list_workflows()
        
        for wf_id in workflows:
            workflow = get_workflow(wf_id)
            assert workflow.name_sw, f"{wf_id} missing name_sw"
            assert workflow.description_sw, f"{wf_id} missing description_sw"
            assert workflow.completion_message_sw, f"{wf_id} missing completion_message_sw"
            
            for step in workflow.steps:
                assert step.prompt_sw, f"{wf_id}.{step.step_id} missing prompt_sw"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
