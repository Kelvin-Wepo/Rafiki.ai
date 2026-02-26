"""
Workflow Engine for Kenya Government Voice Assistant

This module provides a state machine-based workflow engine for guiding users
through government service processes step by step.

Features:
- Declarative workflow definitions (DSL)
- State persistence and resumption
- Voice and text input support
- Entity extraction and validation
- Interrupt handling (pause/resume)
- Audit trail integration
"""

from .engine import WorkflowEngine, WorkflowState, WorkflowContext
from .definitions import get_workflow, list_workflows, WorkflowDefinition

__all__ = [
    'WorkflowEngine',
    'WorkflowState', 
    'WorkflowContext',
    'get_workflow',
    'list_workflows',
    'WorkflowDefinition'
]
