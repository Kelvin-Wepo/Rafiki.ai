"""
Workflow Action Handlers

Custom action handlers for government service workflows.
These are registered with the workflow engine and called
when a workflow reaches an ACTION step.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, TYPE_CHECKING

from utils.logger import get_logger
from utils.audit import get_audit_service, AuditEventType

if TYPE_CHECKING:
    from workflows.engine import WorkflowState, WorkflowContext

logger = get_logger(__name__)


async def handle_create_ntsa_booking(
    state: "WorkflowState",
    context: Optional["WorkflowContext"]
) -> Dict[str, Any]:
    """
    Create an NTSA driving license appointment.
    
    Stores the booking in the booking service and prepares
    for SMS confirmation.
    """
    from services.booking_service import booking_service
    from models.schemas import ServiceType, TimeSlot
    
    try:
        # Normalize time slot
        time_slot_raw = state.entities.get("time_slot", "morning").lower()
        if "morning" in time_slot_raw or "asubuhi" in time_slot_raw:
            time_slot = TimeSlot.MORNING
        else:
            time_slot = TimeSlot.AFTERNOON
        
        # Calculate appointment date (next business day)
        appointment_date = date.today() + timedelta(days=1)
        while appointment_date.weekday() >= 5:  # Skip weekends
            appointment_date += timedelta(days=1)
        
        # Create booking
        result = await booking_service.create_booking(
            service_type=ServiceType.DRIVING_LICENSE,
            user_name=state.entities.get("full_name", "Unknown"),
            phone_number=state.entities.get("phone_number", ""),
            time_slot=time_slot,
            appointment_date=appointment_date,
            additional_notes=f"License type: {state.entities.get('license_type', 'renewal')}",
            send_sms=False  # We'll send SMS separately
        )
        
        if result.get("success"):
            state.entities["booking_id"] = result.get("booking_id")
            state.entities["appointment_date"] = appointment_date.isoformat()
            state.entities["time_slot_formatted"] = time_slot.value
            state.entities["service_type"] = "driving_license"
            
            # Log to audit
            audit = get_audit_service()
            await audit.log(
                event_type=AuditEventType.BOOKING_CREATED,
                action="NTSA driving license appointment created",
                session_id=state.session_id,
                details={
                    "booking_id": result.get("booking_id"),
                    "workflow_id": state.workflow_id,
                    "service": "driving_license"
                }
            )
            
            logger.info(f"Created NTSA booking: {result.get('booking_id')}")
            return {"success": True, "booking_id": result.get("booking_id")}
        else:
            return {"success": False, "error": result.get("error", "Booking failed")}
            
    except Exception as e:
        logger.error(f"NTSA booking creation failed: {e}")
        return {"success": False, "error": str(e)}


async def handle_send_sms_confirmation(
    state: "WorkflowState",
    context: Optional["WorkflowContext"]
) -> Dict[str, Any]:
    """
    Send SMS confirmation for a booking or workflow completion.
    """
    from services.sms_service import sms_service
    
    try:
        phone = state.entities.get("phone_number")
        if not phone:
            logger.warning("No phone number for SMS confirmation")
            return {"success": True}  # Don't fail workflow
        
        # Build message based on workflow
        workflow_id = state.workflow_id
        
        if workflow_id == "ntsa_driving_license":
            booking_id = state.entities.get("booking_id", "N/A")
            appointment_date = state.entities.get("appointment_date", "TBD")
            time_slot = state.entities.get("time_slot_formatted", "TBD")
            
            message = (
                f"Rafiki eCitizen: Your NTSA driving license appointment is confirmed!\n"
                f"Booking ID: {booking_id}\n"
                f"Date: {appointment_date}\n"
                f"Time: {time_slot}\n"
                f"Please arrive 15 minutes early with your ID, medical cert, and photos."
            )
        elif workflow_id == "dci_good_conduct":
            reference = state.entities.get("reference_id", f"GC-{uuid.uuid4().hex[:8].upper()}")
            state.entities["reference_id"] = reference
            
            message = (
                f"Rafiki eCitizen: Your Good Conduct application details have been saved.\n"
                f"Reference: {reference}\n"
                f"Next: Visit DCI or Huduma Centre with ID, 2 photos, and Ksh 1,050."
            )
        elif workflow_id == "emergency_report":
            reference = state.entities.get("reference_id", f"EM-{uuid.uuid4().hex[:8].upper()}")
            state.entities["reference_id"] = reference
            
            message = (
                f"Rafiki Emergency Report received.\n"
                f"Reference: {reference}\n"
                f"For immediate help call: 999 (Police/Fire/Ambulance) or 112."
            )
        else:
            # Generic confirmation
            message = (
                f"Rafiki eCitizen: Your request has been processed.\n"
                f"Workflow: {workflow_id.replace('_', ' ').title()}\n"
                f"Thank you for using Rafiki."
            )
        
        result = await sms_service.send_sms(phone, message)
        
        # Log to audit
        audit = get_audit_service()
        await audit.log_sms_event(
            success=result.get("success", False),
            phone_masked=f"{phone[:4]}****{phone[-2:]}",
            message_type=workflow_id,
            session_id=state.session_id,
            error=result.get("error")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")
        return {"success": False, "error": str(e)}


async def handle_lookup_huduma_centres(
    state: "WorkflowState",
    context: Optional["WorkflowContext"]
) -> Dict[str, Any]:
    """
    Find nearest Huduma Centres based on user location.
    """
    from services.maps_service import get_maps_service
    
    try:
        maps = get_maps_service()
        location = state.entities.get("location", "Nairobi")
        service_needed = state.entities.get("service_needed")
        
        result = await maps.find_nearest_huduma_centres(
            location=location,
            limit=3,
            service_filter=service_needed
        )
        
        if result.get("success") and result.get("centres"):
            nearest = result["centres"][0]
            state.entities["nearest_centre"] = nearest["name"]
            state.entities["distance"] = f"{nearest['distance_km']} km"
            state.entities["hours"] = nearest["hours"]
            state.entities["huduma_phone"] = nearest["phone"]
            state.entities["huduma_address"] = nearest["address"]
            
            # Store all centres for reference
            state.entities["all_centres"] = [
                {
                    "name": c["name"],
                    "distance_km": c["distance_km"],
                    "address": c["address"]
                }
                for c in result["centres"]
            ]
        
        return result
        
    except Exception as e:
        logger.error(f"Huduma Centre lookup failed: {e}")
        return {"success": False, "error": str(e)}


async def handle_search_rag(
    state: "WorkflowState",
    context: Optional["WorkflowContext"]
) -> Dict[str, Any]:
    """
    Search the Constitution/government documents via RAG.
    """
    from services.rag_service import get_rag_service
    
    try:
        rag = get_rag_service()
        query = state.entities.get("query", "")
        
        if not query:
            return {"success": False, "error": "No query provided"}
        
        # Get language from context
        language = context.language if context else state.language
        
        # Perform RAG query with citations
        result = rag.query_with_citations(
            query_text=query,
            language=language,
            top_k=3
        )
        
        # Store results in entities for response
        if result.get("context"):
            state.entities["rag_answer"] = result["context"]
            state.entities["rag_citations"] = result.get("citations", [])
            state.entities["rag_spoken_citations"] = result.get("spoken_citations", [])
            
            # Log to audit
            audit = get_audit_service()
            await audit.log(
                event_type=AuditEventType.RAG_QUERY,
                action=f"Constitutional query: {query[:50]}...",
                session_id=state.session_id,
                details={
                    "query": query[:100],
                    "results_count": result.get("total_sources", 0),
                    "verified_count": result.get("verified_sources", 0)
                }
            )
            
            return {"success": True, "answer": result["context"]}
        else:
            return {
                "success": False, 
                "error": "No relevant information found in the Constitution"
            }
        
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return {"success": False, "error": str(e)}


async def handle_submit_feedback(
    state: "WorkflowState",
    context: Optional["WorkflowContext"]
) -> Dict[str, Any]:
    """
    Submit citizen feedback.
    """
    try:
        # Generate reference ID
        reference_id = f"FB-{uuid.uuid4().hex[:8].upper()}"
        state.entities["reference_id"] = reference_id
        
        # Log to audit
        audit = get_audit_service()
        await audit.log_citizen_report(
            report_type="feedback",
            reference_id=reference_id,
            is_anonymous=state.entities.get("is_anonymous", "yes").lower() == "yes",
            session_id=state.session_id
        )
        
        logger.info(f"Feedback submitted: {reference_id}")
        
        return {"success": True, "reference_id": reference_id}
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        return {"success": False, "error": str(e)}


async def handle_log_emergency(
    state: "WorkflowState",
    context: Optional["WorkflowContext"]
) -> Dict[str, Any]:
    """
    Log an emergency report.
    """
    try:
        # Generate reference ID
        reference_id = f"EM-{uuid.uuid4().hex[:8].upper()}"
        state.entities["reference_id"] = reference_id
        
        # Log to audit with HIGH risk level
        from utils.audit import RiskLevel
        audit = get_audit_service()
        await audit.log(
            event_type=AuditEventType.EMERGENCY_REPORTED,
            action=f"Emergency report: {state.entities.get('emergency_type', 'unknown')}",
            session_id=state.session_id,
            risk_level=RiskLevel.HIGH,
            details={
                "reference_id": reference_id,
                "emergency_type": state.entities.get("emergency_type"),
                "location": state.entities.get("location"),
                # Don't log full description for privacy
            }
        )
        
        logger.warning(f"Emergency report logged: {reference_id}")
        
        return {"success": True, "reference_id": reference_id}
        
    except Exception as e:
        logger.error(f"Emergency logging failed: {e}")
        return {"success": False, "error": str(e)}


def register_action_handlers(engine):
    """
    Register all custom action handlers with the workflow engine.
    
    Call this during engine initialization.
    """
    engine.register_action_handler("create_ntsa_booking", handle_create_ntsa_booking)
    engine.register_action_handler("send_sms_confirmation", handle_send_sms_confirmation)
    engine.register_action_handler("lookup_huduma_centres", handle_lookup_huduma_centres)
    engine.register_action_handler("search_rag", handle_search_rag)
    engine.register_action_handler("submit_feedback", handle_submit_feedback)
    engine.register_action_handler("log_emergency", handle_log_emergency)
    
    logger.info("Registered 6 custom workflow action handlers")
