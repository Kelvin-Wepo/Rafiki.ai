"""
agencies.py
-----------
Rafiki.ai – FastAPI route for the Agency Workflow Engine
Mount this in your backend/main.py with:

    from routes.agencies import router as agencies_router
    app.include_router(agencies_router, prefix="/api/agencies", tags=["agencies"])
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import logging

from services.agency_workflows import handle_message, get_or_create_session, clear_session
from services.paystack_service import (
    initiate_stk_push,
    verify_payment,
    generate_reference,
)
from services.sms_service import sms_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    step: str
    agency: Optional[str] = None
    service: Optional[str] = None
    awaiting_payment: bool = False          # Signals frontend to initiate payment
    payment_amount: Optional[int] = None    # Amount in KES


class PaymentInitRequest(BaseModel):
    session_id: str
    phone: str
    amount_ksh: int
    service: str
    email: Optional[str] = "customer@rafiki.ai"


class PaymentVerifyRequest(BaseModel):
    reference: str


# ---------------------------------------------------------------------------
# SMS Notification Helpers
# ---------------------------------------------------------------------------

async def send_payment_initiated_sms(phone: str, service: str, amount: int, reference: str):
    """Send SMS when STK push is initiated."""
    try:
        message = (
            f"Rafiki.ai Payment Request\n\n"
            f"Service: {service}\n"
            f"Amount: KES {amount:,}\n"
            f"Ref: {reference}\n\n"
            f"Please enter your M-PESA PIN when prompted to complete payment."
        )
        result = await sms_service.send_sms(phone, message)
        if result.get("success"):
            logger.info(f"Payment initiated SMS sent to {phone[:4]}****")
        else:
            logger.warning(f"Failed to send payment initiated SMS: {result.get('error')}")
    except Exception as e:
        logger.error(f"SMS send error: {e}")


async def send_payment_confirmed_sms(phone: str, service: str, amount: int, reference: str):
    """Send SMS when payment is confirmed."""
    try:
        message = (
            f"Rafiki.ai Payment Confirmed! ✅\n\n"
            f"Service: {service}\n"
            f"Amount: KES {amount:,}\n"
            f"Ref: {reference}\n\n"
            f"Your payment has been received. You can download your receipt "
            f"from the Transcripts section on Rafiki.ai.\n\n"
            f"Thank you for using Rafiki!"
        )
        result = await sms_service.send_sms(phone, message)
        if result.get("success"):
            logger.info(f"Payment confirmed SMS sent to {phone[:4]}****")
        else:
            logger.warning(f"Failed to send payment confirmed SMS: {result.get('error')}")
    except Exception as e:
        logger.error(f"SMS send error: {e}")


async def send_booking_sms(phone: str, service: str, details: dict):
    """Send SMS for service booking confirmation."""
    try:
        name = details.get("name", "Customer")
        agency = details.get("agency", "Government Agency")
        
        message = (
            f"Rafiki.ai Booking Confirmed! ✅\n\n"
            f"Dear {name},\n"
            f"Agency: {agency}\n"
            f"Service: {service}\n\n"
            f"Please visit the relevant office with your National ID "
            f"and payment receipt for verification.\n\n"
            f"Thank you for using Rafiki!"
        )
        result = await sms_service.send_sms(phone, message)
        if result.get("success"):
            logger.info(f"Booking SMS sent to {phone[:4]}****")
        else:
            logger.warning(f"Failed to send booking SMS: {result.get('error')}")
    except Exception as e:
        logger.error(f"SMS send error: {e}")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main conversational endpoint.
    Send a message and receive Rafiki's next response.
    
    - If session_id is not provided, a new session is created (WELCOME flow).
    - Send 'menu' at any point to return to the main menu.
    - When awaiting_payment=True, automatically initiates STK push via Paystack.
    """
    session_id = req.session_id or str(uuid.uuid4())

    try:
        # On first contact (no session yet), trigger welcome
        if not req.session_id:
            response_text = handle_message(session_id, "__new_session__")
        else:
            response_text = handle_message(session_id, req.message)
    except Exception as e:
        logger.error(f"Workflow error for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")

    state = get_or_create_session(session_id)

    # Auto-trigger Paystack STK push when payment is awaited
    if state.awaiting_payment and state.payment_amount:
        mpesa_number = state.data.get("mpesa", "")
        service_name = state.service or state.agency or "Government Service"
        
        if mpesa_number:
            try:
                reference = generate_reference(session_id, service_name)
                state.payment_ref = reference
                
                # Initiate the STK push via Paystack
                payment_result = await initiate_stk_push(
                    phone=mpesa_number,
                    amount_ksh=state.payment_amount,
                    email=f"user_{session_id[:8]}@rafiki.ai",
                    reference=reference,
                    description=f"Rafiki.ai - {service_name}",
                )
                
                if payment_result.get("success"):
                    logger.info(f"STK push sent: session={session_id}, ref={reference}, amount={state.payment_amount}")
                    # Send SMS notification for payment initiation
                    await send_payment_initiated_sms(
                        phone=mpesa_number,
                        service=service_name,
                        amount=state.payment_amount,
                        reference=reference
                    )
                else:
                    logger.warning(f"STK push failed: {payment_result.get('message')}")
                    
            except Exception as e:
                logger.error(f"Payment initiation error: {e}", exc_info=True)

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        step=state.step,
        agency=state.agency,
        service=state.service,
        awaiting_payment=state.awaiting_payment,
        payment_amount=state.payment_amount,
    )


@router.post("/chat/start", response_model=ChatResponse)
async def start_chat():
    """
    Create a brand new session and return the welcome message.
    Call this when a user first logs in.
    """
    session_id = str(uuid.uuid4())
    response_text = handle_message(session_id, "__new_session__")
    state = get_or_create_session(session_id)

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        step=state.step,
        agency=state.agency,
        service=state.service,
        awaiting_payment=state.awaiting_payment,
        payment_amount=state.payment_amount,
    )


@router.delete("/chat/{session_id}")
async def end_session(session_id: str):
    """Clear a session (e.g. on logout)."""
    clear_session(session_id)
    return {"message": "Session cleared."}


@router.post("/payment/initiate")
async def initiate_payment(req: PaymentInitRequest):
    """
    Initiate an M-PESA STK push via Paystack.
    Call this after the user confirms their details in the chat flow.
    """
    state = get_or_create_session(req.session_id)
    reference = generate_reference(req.session_id, req.service)
    state.payment_ref = reference

    result = await initiate_stk_push(
        phone=req.phone,
        amount_ksh=req.amount_ksh,
        email=req.email or "customer@rafiki.ai",
        reference=reference,
        description=f"Rafiki.ai – {req.service}",
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "reference": reference,
        "message": result["message"],
        "display_text": result.get("display_text", "Check your phone for the M-PESA prompt."),
    }


@router.post("/payment/verify")
async def verify_payment_endpoint(req: PaymentVerifyRequest):
    """
    Verify an M-PESA payment by reference.
    Poll this after initiating the STK push (every 5 seconds, up to 60 seconds).
    Sends SMS notification when payment is confirmed.
    """
    result = await verify_payment(req.reference)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    # Send SMS when payment is confirmed
    if result.get("paid"):
        # Find the session with this reference to get phone and service details
        from services.agency_workflows import _sessions
        for session_id, state in _sessions.items():
            if state.payment_ref == req.reference:
                phone = state.data.get("mpesa") or state.data.get("phone", "")
                service = state.service or state.agency or "Government Service"
                amount = result.get("amount_ksh", state.payment_amount or 0)
                
                if phone:
                    await send_payment_confirmed_sms(
                        phone=phone,
                        service=service,
                        amount=amount,
                        reference=req.reference
                    )
                    # Also send booking confirmation SMS
                    await send_booking_sms(
                        phone=phone,
                        service=service,
                        details={
                            "name": state.data.get("name", "Customer"),
                            "agency": state.agency or "Government Agency",
                        }
                    )
                break

    return result


@router.get("/payment/status/{session_id}")
async def payment_status(session_id: str):
    """Check payment status for an active session. Sends SMS on first confirmation."""
    state = get_or_create_session(session_id)
    if not state.payment_ref:
        return {"paid": False, "message": "No payment initiated for this session."}

    result = await verify_payment(state.payment_ref)
    
    # Send SMS when payment is confirmed (only if not already sent)
    if result.get("paid") and not state.data.get("sms_sent"):
        phone = state.data.get("mpesa") or state.data.get("phone", "")
        service = state.service or state.agency or "Government Service"
        amount = result.get("amount_ksh", state.payment_amount or 0)
        
        if phone:
            await send_payment_confirmed_sms(
                phone=phone,
                service=service,
                amount=amount,
                reference=state.payment_ref
            )
            await send_booking_sms(
                phone=phone,
                service=service,
                details={
                    "name": state.data.get("name", "Customer"),
                    "agency": state.agency or "Government Agency",
                }
            )
            # Mark SMS as sent to avoid duplicates
            state.data["sms_sent"] = True
    
    return result


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Debug endpoint – returns current session state (disable in production)."""
    state = get_or_create_session(session_id)
    return {
        "session_id": state.session_id,
        "step": state.step,
        "agency": state.agency,
        "service": state.service,
        "has_disability": state.has_disability,
        "payment_ref": state.payment_ref,
        "data_keys": list(state.data.keys()),
    }