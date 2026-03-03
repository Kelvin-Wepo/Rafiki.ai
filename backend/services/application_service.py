"""
application_service.py
----------------------
Rafiki.ai - Application persistence service.
Stores application records in JSON (dev) or database (production).
"""

import json
import os
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Storage path for applications (JSON file for dev)
DATA_DIR = Path(__file__).parent.parent / "data"
APPLICATIONS_FILE = DATA_DIR / "applications.json"


def _ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not APPLICATIONS_FILE.exists():
        with open(APPLICATIONS_FILE, "w") as f:
            json.dump({}, f)


def _load_applications() -> Dict[str, Any]:
    """Load all applications from storage."""
    _ensure_data_dir()
    try:
        with open(APPLICATIONS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_applications(data: Dict[str, Any]):
    """Save applications to storage."""
    _ensure_data_dir()
    with open(APPLICATIONS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def generate_application_ref(agency: str, service: str) -> str:
    """Generate a unique application reference."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_id = str(uuid.uuid4())[:8].upper()
    agency_code = agency[:3].upper() if agency else "RAF"
    return f"{agency_code}-{timestamp}-{short_id}"


def save_application(
    session_id: str,
    agency: str,
    service: str,
    applicant_data: Dict[str, Any],
    payment_ref: Optional[str] = None,
    amount: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Save a new application record.
    
    Args:
        session_id: The chat session ID
        agency: Agency name (e.g., "NTSA", "KRA")
        service: Service name (e.g., "Apply for Driving Licence")
        applicant_data: User-provided data (name, ID, phone, etc.)
        payment_ref: Payment reference if payment was made
        amount: Payment amount in KES
    
    Returns:
        The saved application record
    """
    applications = _load_applications()
    
    app_ref = generate_application_ref(agency, service)
    
    application = {
        "application_ref": app_ref,
        "session_id": session_id,
        "agency": agency,
        "service": service,
        "status": "pending_payment" if payment_ref else "draft",
        "applicant": {
            "name": applicant_data.get("name", ""),
            "id_number": applicant_data.get("id", ""),
            "phone": applicant_data.get("phone", "") or applicant_data.get("mpesa", ""),
            "email": applicant_data.get("email", ""),
            "county": applicant_data.get("county", ""),
            "kra_pin": applicant_data.get("kra_pin", ""),
        },
        "payment": {
            "reference": payment_ref,
            "amount": amount,
            "status": "pending" if payment_ref else None,
            "paid_at": None,
        },
        "metadata": applicant_data,  # Store all raw data
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    applications[app_ref] = application
    _save_applications(applications)
    
    logger.info(f"Application saved: ref={app_ref}, agency={agency}, service={service}")
    return application


def update_application_status(
    app_ref: str,
    status: str,
    payment_status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update an application's status.
    
    Args:
        app_ref: Application reference
        status: New status (e.g., "submitted", "paid", "completed", "rejected")
        payment_status: New payment status (e.g., "paid", "failed")
    
    Returns:
        Updated application or None if not found
    """
    applications = _load_applications()
    
    if app_ref not in applications:
        logger.warning(f"Application not found: {app_ref}")
        return None
    
    application = applications[app_ref]
    application["status"] = status
    application["updated_at"] = datetime.now().isoformat()
    
    if payment_status:
        application["payment"]["status"] = payment_status
        if payment_status == "paid":
            application["payment"]["paid_at"] = datetime.now().isoformat()
    
    _save_applications(applications)
    
    logger.info(f"Application updated: ref={app_ref}, status={status}")
    return application


def get_application(app_ref: str) -> Optional[Dict[str, Any]]:
    """Get an application by reference."""
    applications = _load_applications()
    return applications.get(app_ref)


def get_application_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent application for a session."""
    applications = _load_applications()
    
    # Find applications for this session, sorted by created_at
    session_apps = [
        app for app in applications.values()
        if app.get("session_id") == session_id
    ]
    
    if not session_apps:
        return None
    
    # Return most recent
    return max(session_apps, key=lambda x: x.get("created_at", ""))


def get_application_by_payment_ref(payment_ref: str) -> Optional[Dict[str, Any]]:
    """Get an application by payment reference."""
    applications = _load_applications()
    
    for app in applications.values():
        if app.get("payment", {}).get("reference") == payment_ref:
            return app
    
    return None


def list_applications(
    agency: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    List applications with optional filters.
    
    Args:
        agency: Filter by agency
        status: Filter by status
        limit: Max number of results
    
    Returns:
        List of applications
    """
    applications = _load_applications()
    
    results = list(applications.values())
    
    if agency:
        results = [a for a in results if a.get("agency") == agency]
    
    if status:
        results = [a for a in results if a.get("status") == status]
    
    # Sort by created_at descending
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return results[:limit]


def mark_application_paid(
    payment_ref: str,
    transaction_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Mark an application as paid when payment is confirmed.
    
    Args:
        payment_ref: Payment reference from Paystack
        transaction_id: Transaction ID from payment provider
    
    Returns:
        Updated application or None if not found
    """
    app = get_application_by_payment_ref(payment_ref)
    
    if not app:
        logger.warning(f"No application found for payment ref: {payment_ref}")
        return None
    
    applications = _load_applications()
    app_ref = app["application_ref"]
    
    applications[app_ref]["status"] = "submitted"
    applications[app_ref]["payment"]["status"] = "paid"
    applications[app_ref]["payment"]["paid_at"] = datetime.now().isoformat()
    
    if transaction_id:
        applications[app_ref]["payment"]["transaction_id"] = transaction_id
    
    applications[app_ref]["updated_at"] = datetime.now().isoformat()
    
    _save_applications(applications)
    
    logger.info(f"Application marked paid: ref={app_ref}, payment_ref={payment_ref}")
    return applications[app_ref]
