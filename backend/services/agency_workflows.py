"""
agency_workflows.py
-------------------
Rafiki.ai – Full Agency Workflow Engine
Covers: NTSA, NCPWD, KRA, DCI, BRS, Immigration, Boma Yangu,
        Ministry of Health, County Services, Emergency, Huduma, Constitution
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import re, uuid, logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Kenya-specific validators
# ---------------------------------------------------------------------------

def valid_phone(v: str) -> bool:
    return bool(re.fullmatch(r"(\+?254|0)7\d{8}", v.strip()))

def valid_id(v: str) -> bool:
    return bool(re.fullmatch(r"\d{7,8}", v.strip()))

def valid_kra_pin(v: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]\d{9}[A-Za-z]", v.strip()))

def valid_mpesa(v: str) -> bool:
    return valid_phone(v)

def valid_passport(v: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{1,2}\d{6,7}", v.strip()))

# ---------------------------------------------------------------------------
# Session state dataclass
# ---------------------------------------------------------------------------

@dataclass
class SessionState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    step: str = "WELCOME"
    agency: Optional[str] = None
    service: Optional[str] = None
    sub_service: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    has_disability: Optional[bool] = None
    payment_ref: Optional[str] = None
    awaiting_payment: bool = False          # Payment trigger flag for frontend
    payment_amount: Optional[int] = None    # Amount in KES for payment

# In-memory session store (replace with Redis/DB in production)
_sessions: Dict[str, SessionState] = {}


def get_or_create_session(session_id: str) -> SessionState:
    if session_id not in _sessions:
        _sessions[session_id] = SessionState(session_id=session_id)
    return _sessions[session_id]


def clear_session(session_id: str):
    _sessions.pop(session_id, None)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _yn(text: str) -> Optional[bool]:
    """Parse yes/no from user input."""
    t = text.strip().lower()
    if t in ("yes", "y", "yeah", "ndio", "sawa", "ok", "okay"):
        return True
    if t in ("no", "n", "hapana", "nope"):
        return False
    return None


def _numbered_pick(text: str, options: list) -> Optional[str]:
    """Accept '1', '2' … or the option text itself."""
    t = text.strip()
    if t.isdigit():
        idx = int(t) - 1
        if 0 <= idx < len(options):
            return options[idx]
    for opt in options:
        if t.lower() == opt.lower():
            return opt
    return None


# ---------------------------------------------------------------------------
# Main conversation handler
# ---------------------------------------------------------------------------

def handle_message(session_id: str, user_input: str) -> str:
    state = get_or_create_session(session_id)
    text = user_input.strip()

    # ── WELCOME ──────────────────────────────────────────────────────────────
    if state.step == "WELCOME":
        state.step = "ASK_DISABILITY"
        return (
            "Hello! My name is Rafiki, your Government AI Assistant here to help you "
            "access all the government services you need. 😊\n\n"
            "To get started, I will need to know a little bit about you.\n\n"
            "Are you a person living with disabilities? (Yes / No)"
        )

    # ── DISABILITY CHECK ─────────────────────────────────────────────────────
    if state.step == "ASK_DISABILITY":
        yn = _yn(text)
        if yn is None:
            return "Please reply with **Yes** or **No** — are you a person living with disabilities?"
        state.has_disability = yn
        state.step = "MAIN_MENU"
        return _main_menu()

    # ── MAIN MENU ────────────────────────────────────────────────────────────
    if state.step == "MAIN_MENU":
        MAIN_OPTIONS = ["Agencies", "Emergency Reporting", "Huduma Centre Lookup", "The Kenyan Constitution"]
        pick = _numbered_pick(text, MAIN_OPTIONS)
        if pick is None:
            return _main_menu()

        if pick == "Agencies":
            state.step = "AGENCY_MENU"
            return _agency_menu()

        if pick == "Emergency Reporting":
            state.step = "EMERGENCY"
            return _emergency_handler(state, "")

        if pick == "Huduma Centre Lookup":
            state.step = "HUDUMA"
            return (
                "🏢 **Huduma Centre Lookup**\n\n"
                "Please enter the county or town you are in and I will find the "
                "nearest Huduma Centre for you."
            )

        if pick == "The Kenyan Constitution":
            state.step = "CONSTITUTION"
            return (
                "📜 **The Kenyan Constitution**\n\n"
                "You may ask me any question about the Constitution of Kenya 2010 "
                "and I will do my best to answer it.\n\n"
                "What would you like to know?"
            )

    # ── HUDUMA ───────────────────────────────────────────────────────────────
    if state.step == "HUDUMA":
        return _huduma_response(text, state)

    # ── CONSTITUTION ─────────────────────────────────────────────────────────
    if state.step == "CONSTITUTION":
        return _constitution_response(text, state)

    # ── AGENCY MENU ──────────────────────────────────────────────────────────
    if state.step == "AGENCY_MENU":
        AGENCIES = ["NTSA", "NCPWD", "KRA", "DCI", "BRS", "Immigration",
                    "Boma Yangu", "Ministry of Health", "County Services"]
        pick = _numbered_pick(text, AGENCIES)
        if pick is None:
            return _agency_menu()
        state.agency = pick
        state.step = f"{pick.upper().replace(' ', '_')}_MENU"
        return _agency_service_menu(pick)

    # ── Delegate to agency-specific handler ──────────────────────────────────
    return _agency_router(state, text)


# ---------------------------------------------------------------------------
# Menu builders
# ---------------------------------------------------------------------------

def _main_menu() -> str:
    return (
        "Great, thank you for providing that information. This will help me offer "
        "customised help and guidance tailored to your needs. 🙏\n\n"
        "Which service are you looking for today? The available services are:\n\n"
        "1️⃣  Agencies (NTSA, NCPWD, KRA, DCI, BRS, Immigration, Boma Yangu, "
        "Ministry of Health, County Services)\n"
        "2️⃣  Emergency Reporting\n"
        "3️⃣  Huduma Centre Lookup\n"
        "4️⃣  The Kenyan Constitution\n\n"
        "Please reply with a number or the service name."
    )


def _agency_menu() -> str:
    return (
        "🏛️ **Government Agencies**\n\n"
        "Please select an agency:\n\n"
        "1️⃣  NTSA – National Transport & Safety Authority\n"
        "2️⃣  NCPWD – National Council for Persons with Disabilities\n"
        "3️⃣  KRA – Kenya Revenue Authority\n"
        "4️⃣  DCI – Directorate of Criminal Investigations\n"
        "5️⃣  BRS – Business Registration Service\n"
        "6️⃣  Immigration – Passports & Permits\n"
        "7️⃣  Boma Yangu – Affordable Housing\n"
        "8️⃣  Ministry of Health\n"
        "9️⃣  County Services\n\n"
        "Reply with a number or agency name."
    )


def _agency_service_menu(agency: str) -> str:
    menus = {
        "NTSA": (
            "🚗 **Welcome to NTSA**\n\nThe available services are:\n\n"
            "1️⃣  Apply for a Driving Licence\n"
            "2️⃣  Renew a Driving Licence\n"
            "3️⃣  Book an Appointment\n\n"
            "Which one would you like?"
        ),
        "NCPWD": (
            "♿ **Welcome to NCPWD**\n\nThe available services are:\n\n"
            "1️⃣  Register as a Person with Disability\n"
            "2️⃣  Apply for a Disability Card\n"
            "3️⃣  Check Registration Status\n"
            "4️⃣  Disability Allowance / Benefits\n\n"
            "Which one would you like?"
        ),
        "KRA": (
            "💰 **Welcome to KRA**\n\nThe available services are:\n\n"
            "1️⃣  Register for a KRA PIN\n"
            "2️⃣  File Nil Returns\n"
            "3️⃣  File Income Tax Returns\n"
            "4️⃣  Apply for a Tax Compliance Certificate\n"
            "5️⃣  Check iTax Account Status\n\n"
            "Which one would you like?"
        ),
        "DCI": (
            "🔍 **Welcome to DCI**\n\nThe available services are:\n\n"
            "1️⃣  Apply for a Good Conduct Certificate\n"
            "2️⃣  Check Application Status\n\n"
            "Which one would you like?"
        ),
        "BRS": (
            "🏢 **Welcome to BRS – Business Registration**\n\nThe available services are:\n\n"
            "1️⃣  Register a Business Name\n"
            "2️⃣  Incorporate a Limited Company\n"
            "3️⃣  Register a Partnership\n"
            "4️⃣  Check Business Name Availability\n"
            "5️⃣  Renew Business Registration\n\n"
            "Which one would you like?"
        ),
        "Immigration": (
            "✈️ **Welcome to Immigration Department**\n\nThe available services are:\n\n"
            "1️⃣  Apply for a Passport\n"
            "2️⃣  Renew a Passport\n"
            "3️⃣  Apply for a Work Permit\n"
            "4️⃣  Apply for a Student Pass\n"
            "5️⃣  Check Application Status\n\n"
            "Which one would you like?"
        ),
        "Boma Yangu": (
            "🏠 **Welcome to Boma Yangu – Affordable Housing**\n\nThe available services are:\n\n"
            "1️⃣  Register / Create an Account\n"
            "2️⃣  Apply for a Housing Unit\n"
            "3️⃣  Check Application Status\n"
            "4️⃣  Affordable Housing Levy Information\n\n"
            "Which one would you like?"
        ),
        "Ministry of Health": (
            "🏥 **Welcome to Ministry of Health**\n\nThe available services are:\n\n"
            "1️⃣  NHIF Registration\n"
            "2️⃣  NHIF Contributions & Status\n"
            "3️⃣  Book Hospital Appointment\n"
            "4️⃣  Health Facility Finder\n"
            "5️⃣  Vaccination / Immunisation Records\n\n"
            "Which one would you like?"
        ),
        "County Services": (
            "🗺️ **Welcome to County Services**\n\nThe available services are:\n\n"
            "1️⃣  Single Business Permit (SBP)\n"
            "2️⃣  Land Rates Payment\n"
            "3️⃣  County Health Certificate\n"
            "4️⃣  Market / Trade Stall Application\n"
            "5️⃣  County Bursary Application\n\n"
            "Which one would you like?"
        ),
    }
    return menus.get(agency, "Service menu not found.")


# ---------------------------------------------------------------------------
# Agency router
# ---------------------------------------------------------------------------

def _agency_router(state: SessionState, text: str) -> str:
    a = state.agency
    if a == "NTSA":        return _ntsa(state, text)
    if a == "NCPWD":       return _ncpwd(state, text)
    if a == "KRA":         return _kra(state, text)
    if a == "DCI":         return _dci(state, text)
    if a == "BRS":         return _brs(state, text)
    if a == "Immigration": return _immigration(state, text)
    if a == "Boma Yangu":  return _boma_yangu(state, text)
    if a == "Ministry of Health": return _moh(state, text)
    if a == "County Services":    return _county(state, text)
    if a == "EMERGENCY":   return _emergency_handler(state, text)
    return "I'm sorry, I didn't understand that. Type **menu** to start over."


# ===========================================================================
# NTSA
# ===========================================================================

NTSA_LICENSE_TYPES = [
    "Class A – Motorcycles",
    "Class BCE – Heavy commercial vehicles",
    "Class C – Motor vehicles up to 3,500 kg",
    "Class D – Buses & coaches",
    "Class E – Articulated lorries",
    "Class F – Agricultural tractors",
    "Class G – Engineering equipment",
]

NTSA_LICENSE_FEES = {
    "Class A – Motorcycles":             {"fee": 3250,  "service": 30},
    "Class BCE – Heavy commercial vehicles": {"fee": 6500, "service": 30},
    "Class C – Motor vehicles up to 3,500 kg": {"fee": 4500, "service": 30},
    "Class D – Buses & coaches":         {"fee": 5500,  "service": 30},
    "Class E – Articulated lorries":     {"fee": 6500,  "service": 30},
    "Class F – Agricultural tractors":   {"fee": 4000,  "service": 30},
    "Class G – Engineering equipment":   {"fee": 4000,  "service": 30},
}

NTSA_APPOINTMENT_TYPES = ["Driving Test", "Biometrics", "Picking a Driving Licence"]


def _ntsa(state: SessionState, text: str) -> str:
    step = state.step

    # ── Service selection ───────────────────────────────────────────────────
    if step == "NTSA_MENU":
        SERVICES = ["Apply for a Driving Licence", "Renew a Driving Licence", "Book an Appointment"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("NTSA")
        state.service = pick
        state.data = {}

        if pick == "Apply for a Driving Licence":
            state.step = "NTSA_APPLY_CONFIRM"
            return (
                "🪪 I will help you apply for a Driving Licence.\n\n"
                "You will require a **National ID Card** to apply.\n\n"
                "Would you like me to proceed? (Yes / No)"
            )

        if pick == "Renew a Driving Licence":
            state.step = "NTSA_RENEW_CONFIRM"
            return (
                "🔄 I will help you **Renew** your Driving Licence.\n\n"
                "You will be required to pay a renewal fee of **Ksh. 1,200**.\n\n"
                "Would you like me to proceed? (Yes / No)"
            )

        if pick == "Book an Appointment":
            state.step = "NTSA_APPT_TYPE"
            return (
                "📅 **Book an Appointment**\n\nWhich appointment service do you need?\n\n"
                "1️⃣  Driving Test\n"
                "2️⃣  Biometrics\n"
                "3️⃣  Picking a Driving Licence\n\n"
                "Which one would you like?"
            )

    # ── APPLY flow ──────────────────────────────────────────────────────────
    if step == "NTSA_APPLY_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NTSA_MENU"
            return _agency_service_menu("NTSA")
        state.step = "NTSA_APPLY_NAME"
        return "Kindly provide your **full name** as it appears on your National ID."

    if step == "NTSA_APPLY_NAME":
        if len(text.split()) < 2:
            return "Please enter your full name (at least two names)."
        state.data["name"] = text
        state.step = "NTSA_APPLY_ID"
        return "What is your **ID Number**?"

    if step == "NTSA_APPLY_ID":
        if not valid_id(text):
            return "Please enter a valid National ID number (7–8 digits)."
        state.data["id_number"] = text
        state.step = "NTSA_APPLY_PHONE"
        return "What is your **Phone Number**? (e.g. 0712345678)"

    if step == "NTSA_APPLY_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number (e.g. 0712345678 or +254712345678)."
        state.data["phone"] = text
        state.step = "NTSA_APPLY_COUNTY"
        return "In which **county** are you currently residing in?"

    if step == "NTSA_APPLY_COUNTY":
        state.data["county"] = text
        state.step = "NTSA_APPLY_CLASS"
        license_list = "\n".join(f"{i+1}️⃣  {t}" for i, t in enumerate(NTSA_LICENSE_TYPES))
        return f"Which **type of licence** are you applying for?\n\n{license_list}"

    if step == "NTSA_APPLY_CLASS":
        pick = _numbered_pick(text, NTSA_LICENSE_TYPES)
        if pick is None:
            license_list = "\n".join(f"{i+1}️⃣  {t}" for i, t in enumerate(NTSA_LICENSE_TYPES))
            return f"Please select a valid licence class:\n\n{license_list}"
        state.data["license_class"] = pick
        fees = NTSA_LICENSE_FEES[pick]
        total = fees["fee"] + fees["service"]
        state.data["fee"] = fees["fee"]
        state.data["service_fee"] = fees["service"]
        state.data["total"] = total
        state.step = "NTSA_APPLY_PAY_CONFIRM"
        return (
            f"💳 To apply for **{pick}** you need to pay:\n"
            f"   • Licence fee: Ksh. {fees['fee']:,}\n"
            f"   • Service fee: Ksh. {fees['service']:,}\n"
            f"   • **Total: Ksh. {total:,}**\n\n"
            "Would you like to pay to complete your application? (Yes / No)"
        )

    if step == "NTSA_APPLY_PAY_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NTSA_MENU"
            return _agency_service_menu("NTSA")
        state.step = "NTSA_APPLY_MPESA"
        return "Please enter your **M-PESA number** to receive the STK push."

    if step == "NTSA_APPLY_MPESA":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number (e.g. 0712345678)."
        state.data["mpesa"] = text
        state.step = "NTSA_APPLY_VERIFY"
        d = state.data
        return (
            "📋 **Please confirm your details:**\n\n"
            f"   • Full Name: **{d['name']}**\n"
            f"   • ID Number: **{d['id_number']}**\n"
            f"   • Phone: **{d['phone']}**\n"
            f"   • County: **{d['county']}**\n"
            f"   • Licence Class: **{d['license_class']}**\n"
            f"   • M-PESA Number: **{d['mpesa']}**\n"
            f"   • Amount: **Ksh. {d['total']:,}**\n\n"
            "Is that correct? (Yes / No)"
        )

    if step == "NTSA_APPLY_VERIFY":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NTSA_APPLY_NAME"
            state.data = {}
            return "No problem! Let's start over.\n\nKindly provide your **full name** as it appears on your National ID."
        # Set payment flags for frontend to trigger Paystack STK push
        state.awaiting_payment = True
        state.payment_amount = state.data.get("total", 6530)
        state.step = "NTSA_APPLY_PAYMENT_PENDING"
        d = state.data
        return (
            f"✅ Great! I have initiated payment.\n\n"
            f"Once you receive the **STK push** on your phone, put your M-PESA PIN "
            f"to complete your payment.\n\n"
            f"Once the payment is confirmed you will receive an **SMS alert** confirming "
            f"your payment and other steps.\n\n"
            f"⚠️ Remember – when applying for a Driving Licence you will need to visit "
            f"an **NTSA office** for physical identity verification such as fingerprints.\n\n"
            f"Is that okay? (Yes / No)"
        )

    if step == "NTSA_APPLY_PAYMENT_PENDING":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        state.awaiting_payment = False  # Clear payment flag
        state.step = "NTSA_APPLY_DONE"
        return _anything_else()

    if step == "NTSA_APPLY_DONE":
        yn = _yn(text)
        if yn is True:
            state.step = "MAIN_MENU"
            state.agency = None
            state.service = None
            state.data = {}
            return _main_menu()
        if yn is False:
            state.step = "SESSION_END"
            return (
                "📄 To download your payment receipt kindly navigate on the platform "
                "under the **Transcripts** section and download your receipt as proof of payment.\n\n"
                "⚠️ Provide this receipt at NTSA offices and **do not pay any additional amount**.\n\n"
                "Thank you for using Rafiki AI! 🙏🇰🇪"
            )
        return _anything_else()

    # ── RENEW flow ──────────────────────────────────────────────────────────
    if step == "NTSA_RENEW_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NTSA_MENU"
            return _agency_service_menu("NTSA")
        state.step = "NTSA_RENEW_ID"
        return "Please enter your **National ID** or **Driving Licence Number**."

    if step == "NTSA_RENEW_ID":
        state.data["id_or_dl"] = text
        state.step = "NTSA_RENEW_CONFIRM2"
        return (
            f"🔎 Your ID/DL **{text}** is associated with licence class **BCE**.\n\n"
            "Would you like to **renew** this licence? (Yes / No)"
        )

    if step == "NTSA_RENEW_CONFIRM2":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NTSA_MENU"
            return _agency_service_menu("NTSA")
        state.step = "NTSA_RENEW_MPESA"
        return "Please provide your **M-PESA number** to receive the STK push."

    if step == "NTSA_RENEW_MPESA":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number."
        state.data["mpesa"] = text
        state.data["total"] = 1200
        # Set payment flags for frontend to trigger Paystack STK push
        state.awaiting_payment = True
        state.payment_amount = 1200
        state.step = "NTSA_RENEW_DONE"
        return (
            "✅ Your payment has been initiated.\n\n"
            "You will receive an **STK push** – input your PIN.\n\n"
            "Once your payment has been processed and verified, you will receive an "
            "**SMS notification**.\n\n"
            "📄 To download your licence navigate on the platform in the **Transcripts** section. "
            "You will be able to see your licence and payment receipt – click on it to download.\n\n"
        ) + _anything_else()

    if step == "NTSA_RENEW_DONE":
        yn = _yn(text)
        state.awaiting_payment = False  # Clear payment flag
        if yn is True:
            state.step = "MAIN_MENU"
            state.agency = None
            state.service = None
            state.data = {}
            return _main_menu()
        if yn is False:
            state.step = "SESSION_END"
            return (
                "Thank you for using Rafiki AI! 🙏\n\n"
                "📄 Your licence and receipt are available in the **Transcripts** section.\n\n"
                "Have a wonderful day! 🇰🇪"
            )
        return _anything_else()

    # ── APPOINTMENT flow ────────────────────────────────────────────────────
    if step == "NTSA_APPT_TYPE":
        pick = _numbered_pick(text, NTSA_APPOINTMENT_TYPES)
        if pick is None:
            return (
                "Please select an appointment type:\n\n"
                "1️⃣  Driving Test\n2️⃣  Biometrics\n3️⃣  Picking a Driving Licence"
            )
        state.sub_service = pick
        state.data = {}

        if pick == "Driving Test":
            state.step = "NTSA_APPT_DT_ID"
            return "Please enter your **National ID Number**."

        if pick == "Biometrics":
            state.step = "NTSA_APPT_BIO_ID"
            return "Please enter your **National ID Number**."

        if pick == "Picking a Driving Licence":
            state.step = "NTSA_APPT_PICK_ID"
            return "Please enter your **National ID Number**."

    # Driving Test appointment
    if step == "NTSA_APPT_DT_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit National ID."
        state.data["id_number"] = text
        state.step = "NTSA_APPT_DT_CONFIRM"
        return (
            f"You are currently enrolled with **Class BCE** licence.\n\n"
            "Would you like to book an appointment for a **Driving Test**? (Yes / No)"
        )

    if step == "NTSA_APPT_DT_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NTSA_MENU"
            return _agency_service_menu("NTSA")
        state.step = "NTSA_APPT_DT_FEE"
        return "You will be charged **Ksh. 1,000** for the Driving Test. Would you like to proceed? (Yes / No)"

    if step == "NTSA_APPT_DT_FEE":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NTSA_MENU"
            return _agency_service_menu("NTSA")
        state.step = "NTSA_APPT_DT_NAME"
        return "Please enter your **full names**."

    if step == "NTSA_APPT_DT_NAME":
        if len(text.split()) < 2:
            return "Please enter your full name (at least two names)."
        state.data["name"] = text
        state.step = "NTSA_APPT_DT_ID2"
        return "Enter your **ID Number**."

    if step == "NTSA_APPT_DT_ID2":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "NTSA_APPT_DT_PHONE"
        return "Enter your **Phone Number**."

    if step == "NTSA_APPT_DT_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "NTSA_APPT_DT_COUNTY"
        return "In which **county** do you live in?"

    if step == "NTSA_APPT_DT_COUNTY":
        state.data["county"] = text
        state.step = "NTSA_APPT_DT_MPESA"
        return "Please provide your **M-PESA Number**."

    if step == "NTSA_APPT_DT_MPESA":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number."
        state.data["mpesa"] = text
        state.data["total"] = 1000
        # Set payment flags for frontend to trigger Paystack STK push
        state.awaiting_payment = True
        state.payment_amount = 1000
        state.step = "NTSA_APPT_DT_DONE"
        return (
            "✅ Your payment has been initiated.\n\n"
            "You will receive an **STK push** – input your PIN.\n\n"
            "Once the payment has been confirmed you will receive an **SMS notification**.\n\n"
            "⚠️ You will also need to visit **NTSA offices physically** for your Driving Test.\n\n"
        ) + _anything_else()

    if step == "NTSA_APPT_DT_DONE":
        yn = _yn(text)
        state.awaiting_payment = False  # Clear payment flag
        if yn is True:
            state.step = "MAIN_MENU"
            state.agency = None
            state.service = None
            state.data = {}
            return _main_menu()
        if yn is False:
            state.step = "SESSION_END"
            return (
                "Thank you for using Rafiki AI! 🙏\n\n"
                "You will receive an SMS with your appointment details.\n\n"
                "Have a wonderful day! 🇰🇪"
            )
        return _anything_else()

    # Biometrics appointment (simplified – same pattern as Driving Test)
    if step == "NTSA_APPT_BIO_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit National ID."
        state.data["id_number"] = text
        state.step = "NTSA_APPT_BIO_CONFIRM"
        return (
            "🖐 I have found your record. Would you like to book a **Biometrics** "
            "appointment at NTSA? There is no fee for this service. (Yes / No)"
        )

    if step == "NTSA_APPT_BIO_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NTSA_MENU"
            return _agency_service_menu("NTSA")
        state.step = "NTSA_APPT_BIO_PHONE"
        return "Please provide your **phone number** so we can send you the appointment details."

    if step == "NTSA_APPT_BIO_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Your **Biometrics appointment** has been booked!\n\n"
            "You will receive an **SMS** with the appointment date and time.\n\n"
            "Please carry your **original National ID** to the NTSA office.\n\n"
        ) + _anything_else()

    # Picking a Driving Licence
    if step == "NTSA_APPT_PICK_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit National ID."
        state.data["id_number"] = text
        state.step = "NTSA_APPT_PICK_PHONE"
        return "Please provide your **phone number**."

    if step == "NTSA_APPT_PICK_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Your **licence collection appointment** has been booked!\n\n"
            "You will receive an **SMS** with the pickup date and NTSA office location.\n\n"
            "Please carry your **payment receipt** and **original National ID**.\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# NCPWD – National Council for Persons with Disabilities
# ===========================================================================

def _ncpwd(state: SessionState, text: str) -> str:
    step = state.step

    if step == "NCPWD_MENU":
        SERVICES = ["Register as a Person with Disability", "Apply for a Disability Card",
                    "Check Registration Status", "Disability Allowance / Benefits"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("NCPWD")
        state.service = pick
        state.data = {}

        if pick == "Register as a Person with Disability":
            state.step = "NCPWD_REG_NAME"
            return (
                "♿ I will help you **register** with NCPWD.\n\n"
                "Please provide your **full name** as per National ID."
            )

        if pick == "Apply for a Disability Card":
            state.step = "NCPWD_CARD_REG_NO"
            return (
                "🪪 To apply for a Disability Card you must already be registered with NCPWD.\n\n"
                "Please enter your **NCPWD Registration Number**."
            )

        if pick == "Check Registration Status":
            state.step = "NCPWD_STATUS_ID"
            return "Please enter your **National ID Number** to check your registration status."

        if pick == "Disability Allowance / Benefits":
            state.step = "NCPWD_ALLOWANCE_ID"
            return "Please enter your **NCPWD Registration Number** to check your allowance status."

    # Registration flow
    if step == "NCPWD_REG_NAME":
        state.data["name"] = text
        state.step = "NCPWD_REG_ID"
        return "What is your **National ID Number**?"

    if step == "NCPWD_REG_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "NCPWD_REG_PHONE"
        return "What is your **Phone Number**?"

    if step == "NCPWD_REG_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "NCPWD_REG_DISABILITY"
        return (
            "Please describe your **type of disability** (e.g. Physical, Visual, "
            "Hearing, Intellectual, Mental, Multiple)."
        )

    if step == "NCPWD_REG_DISABILITY":
        state.data["disability_type"] = text
        state.step = "NCPWD_REG_COUNTY"
        return "In which **county** do you reside?"

    if step == "NCPWD_REG_COUNTY":
        state.data["county"] = text
        state.step = "NCPWD_REG_CONFIRM"
        d = state.data
        return (
            "📋 **Please confirm your details:**\n\n"
            f"   • Name: **{d['name']}**\n"
            f"   • ID: **{d['id_number']}**\n"
            f"   • Phone: **{d['phone']}**\n"
            f"   • Disability: **{d['disability_type']}**\n"
            f"   • County: **{d['county']}**\n\n"
            "Is that correct? (Yes / No)"
        )

    if step == "NCPWD_REG_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "NCPWD_REG_NAME"
            state.data = {}
            return "Let's start over. Please provide your **full name**."
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Your NCPWD registration has been **submitted**!\n\n"
            "You will receive an **SMS** with your registration number within 3–5 working days.\n\n"
            "You may then visit your nearest **Huduma Centre** to complete the process "
            "and collect your Disability Card.\n\n"
        ) + _anything_else()

    # Disability card
    if step == "NCPWD_CARD_REG_NO":
        state.data["reg_number"] = text
        state.step = "NCPWD_CARD_PHONE"
        return "Please provide your **phone number** for confirmation."

    if step == "NCPWD_CARD_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Your Disability Card application has been **submitted**!\n\n"
            "The card costs **Ksh. 0** (free of charge).\n\n"
            "You will receive an SMS when the card is ready for collection at your nearest Huduma Centre.\n\n"
        ) + _anything_else()

    # Check status
    if step == "NCPWD_STATUS_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit National ID number."
        state.step = "ANYTHING_ELSE"
        return (
            f"🔎 Checking registration status for ID **{text}**...\n\n"
            "✅ Your registration status is: **Pending Verification**\n"
            "Expected completion: 3–5 working days.\n\n"
        ) + _anything_else()

    # Allowance
    if step == "NCPWD_ALLOWANCE_ID":
        state.step = "ANYTHING_ELSE"
        return (
            f"💰 Allowance status for registration number **{text}**:\n\n"
            "Status: **Active** – Monthly allowance of Ksh. 2,000\n"
            "Next disbursement: End of month via M-PESA.\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# KRA – Kenya Revenue Authority
# ===========================================================================

def _kra(state: SessionState, text: str) -> str:
    step = state.step

    if step == "KRA_MENU":
        SERVICES = ["Register for a KRA PIN", "File Nil Returns", "File Income Tax Returns",
                    "Apply for a Tax Compliance Certificate", "Check iTax Account Status"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("KRA")
        state.service = pick
        state.data = {}

        if pick == "Register for a KRA PIN":
            state.step = "KRA_PIN_REG_NAME"
            return "I will help you register for a **KRA PIN**.\n\nPlease provide your **full name** as per National ID."

        if pick == "File Nil Returns":
            state.step = "KRA_NIL_PIN"
            return "To file **Nil Returns**, please enter your **KRA PIN**."

        if pick == "File Income Tax Returns":
            state.step = "KRA_TAX_PIN"
            return "To file **Income Tax Returns**, please enter your **KRA PIN**."

        if pick == "Apply for a Tax Compliance Certificate":
            state.step = "KRA_TCC_PIN"
            return "To apply for a **Tax Compliance Certificate**, please enter your **KRA PIN**."

        if pick == "Check iTax Account Status":
            state.step = "KRA_STATUS_PIN"
            return "Please enter your **KRA PIN** to check your iTax account status."

    # PIN Registration
    if step == "KRA_PIN_REG_NAME":
        state.data["name"] = text
        state.step = "KRA_PIN_REG_ID"
        return "What is your **National ID Number**?"

    if step == "KRA_PIN_REG_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "KRA_PIN_REG_PHONE"
        return "What is your **Phone Number**?"

    if step == "KRA_PIN_REG_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "KRA_PIN_REG_EMAIL"
        return "What is your **email address**?"

    if step == "KRA_PIN_REG_EMAIL":
        state.data["email"] = text
        state.step = "KRA_PIN_REG_CONFIRM"
        d = state.data
        return (
            "📋 **Confirm your details:**\n\n"
            f"   • Name: **{d['name']}**\n"
            f"   • ID: **{d['id_number']}**\n"
            f"   • Phone: **{d['phone']}**\n"
            f"   • Email: **{d['email']}**\n\n"
            "Is that correct? (Yes / No)"
        )

    if step == "KRA_PIN_REG_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "KRA_PIN_REG_NAME"
            state.data = {}
            return "Let's start over. Please provide your **full name**."
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Your KRA PIN registration has been **submitted**!\n\n"
            "You will receive an email with your **KRA PIN** within 24 hours.\n\n"
            "Keep your PIN safe – it is required for all KRA transactions.\n\n"
        ) + _anything_else()

    # Nil Returns
    if step == "KRA_NIL_PIN":
        if not valid_kra_pin(text):
            return "Please enter a valid KRA PIN (e.g. A123456789B)."
        state.data["kra_pin"] = text
        state.step = "KRA_NIL_YEAR"
        return "For which **tax year** would you like to file Nil Returns? (e.g. 2023)"

    if step == "KRA_NIL_YEAR":
        state.data["year"] = text
        state.step = "KRA_NIL_CONFIRM"
        return (
            f"You are about to file **Nil Returns** for tax year **{text}** "
            f"under PIN **{state.data['kra_pin']}**.\n\n"
            "Shall I proceed? (Yes / No)"
        )

    if step == "KRA_NIL_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "KRA_MENU"
            return _agency_service_menu("KRA")
        state.step = "ANYTHING_ELSE"
        return (
            "✅ **Nil Returns** have been filed successfully!\n\n"
            "Reference Number: **NIL-2024-XXXXXX**\n\n"
            "You will receive an **email and SMS** confirmation shortly.\n\n"
        ) + _anything_else()

    # Income Tax Returns
    if step == "KRA_TAX_PIN":
        if not valid_kra_pin(text):
            return "Please enter a valid KRA PIN."
        state.data["kra_pin"] = text
        state.step = "KRA_TAX_YEAR"
        return "For which **tax year** would you like to file returns? (e.g. 2023)"

    if step == "KRA_TAX_YEAR":
        state.data["year"] = text
        state.step = "KRA_TAX_INCOME"
        return "What was your **total gross income** for the year (in Ksh)?"

    if step == "KRA_TAX_INCOME":
        state.data["income"] = text
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Your Income Tax Return details have been **submitted** for processing.\n\n"
            "A KRA officer will review and you will receive confirmation within 5 working days.\n\n"
            "To pay any tax due, you will receive an **e-slip** via email.\n\n"
        ) + _anything_else()

    # Tax Compliance Certificate
    if step in ("KRA_TCC_PIN", "KRA_STATUS_PIN"):
        if not valid_kra_pin(text):
            return "Please enter a valid KRA PIN."
        state.data["kra_pin"] = text
        state.step = "ANYTHING_ELSE"
        if step == "KRA_TCC_PIN":
            return (
                "✅ Your **Tax Compliance Certificate** application has been submitted.\n\n"
                "Processing takes **3 working days**. You will receive it via email and SMS.\n\n"
                "Fee: **Ksh. 0** (free of charge)\n\n"
            ) + _anything_else()
        else:
            return (
                f"🔎 iTax Account Status for PIN **{text}**:\n\n"
                "✅ **Active** – Returns filed up to 2023\n"
                "⚠️  2024 returns are **pending**\n\n"
            ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# DCI – Good Conduct Certificate
# ===========================================================================

def _dci(state: SessionState, text: str) -> str:
    step = state.step

    if step == "DCI_MENU":
        SERVICES = ["Apply for a Good Conduct Certificate", "Check Application Status"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("DCI")
        state.service = pick
        state.data = {}

        if pick == "Apply for a Good Conduct Certificate":
            state.step = "DCI_APPLY_NAME"
            return (
                "🔍 I will help you apply for a **Good Conduct Certificate**.\n\n"
                "The application fee is **Ksh. 1,050**.\n\n"
                "Please provide your **full name** as per National ID."
            )
        if pick == "Check Application Status":
            state.step = "DCI_STATUS_REF"
            return "Please enter your **DCI Reference Number** or **ID Number** to check your application status."

    if step == "DCI_APPLY_NAME":
        state.data["name"] = text
        state.step = "DCI_APPLY_ID"
        return "What is your **National ID Number**?"

    if step == "DCI_APPLY_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "DCI_APPLY_PHONE"
        return "What is your **Phone Number**?"

    if step == "DCI_APPLY_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "DCI_APPLY_DOB"
        return "What is your **Date of Birth**? (DD/MM/YYYY)"

    if step == "DCI_APPLY_DOB":
        state.data["dob"] = text
        state.step = "DCI_APPLY_MPESA"
        return (
            "💳 The Good Conduct Certificate fee is **Ksh. 1,050**.\n\n"
            "Please enter your **M-PESA number** to proceed with payment."
        )

    if step == "DCI_APPLY_MPESA":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number."
        state.data["mpesa"] = text
        state.step = "DCI_APPLY_CONFIRM"
        d = state.data
        return (
            "📋 **Confirm your details:**\n\n"
            f"   • Name: **{d['name']}**\n"
            f"   • ID: **{d['id_number']}**\n"
            f"   • Phone: **{d['phone']}**\n"
            f"   • DOB: **{d['dob']}**\n"
            f"   • M-PESA: **{d['mpesa']}**\n"
            f"   • Amount: **Ksh. 1,050**\n\n"
            "Is that correct? (Yes / No)"
        )

    if step == "DCI_APPLY_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "DCI_APPLY_NAME"
            state.data = {}
            return "Let's start over. Please provide your **full name**."
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Payment initiated! You will receive an **STK push** shortly.\n\n"
            "Once payment is confirmed, your application will be submitted for processing.\n\n"
            "The certificate takes **10–15 working days**. You will be notified via SMS.\n\n"
            "⚠️  You will need to visit a **DCI office** for fingerprint capture.\n\n"
        ) + _anything_else()

    if step == "DCI_STATUS_REF":
        state.step = "ANYTHING_ELSE"
        return (
            f"🔎 Status for reference **{text}**:\n\n"
            "✅ **Under Review** – Fingerprints verified\n"
            "Expected completion: 5–7 working days.\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# BRS – Business Registration
# ===========================================================================

def _brs(state: SessionState, text: str) -> str:
    step = state.step

    if step == "BRS_MENU":
        SERVICES = ["Register a Business Name", "Incorporate a Limited Company",
                    "Register a Partnership", "Check Business Name Availability",
                    "Renew Business Registration"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("BRS")
        state.service = pick
        state.data = {}

        if pick == "Check Business Name Availability":
            state.step = "BRS_CHECK_NAME"
            return "Please enter the **business name** you wish to check."

        if pick == "Renew Business Registration":
            state.step = "BRS_RENEW_REG"
            return "Please enter your **Business Registration Number**."

        state.step = "BRS_REG_BUSINESS_NAME"
        fees = {"Register a Business Name": 950, "Incorporate a Limited Company": 10650,
                "Register a Partnership": 4500}
        fee = fees.get(pick, 950)
        state.data["fee"] = fee
        return (
            f"🏢 I will help you with **{pick}**.\n\n"
            f"The registration fee is **Ksh. {fee:,}**.\n\n"
            "Please provide the **proposed business / company name**."
        )

    if step == "BRS_CHECK_NAME":
        state.step = "ANYTHING_ELSE"
        return (
            f"🔎 Checking availability of **\"{text}\"**...\n\n"
            "✅ This business name is **Available**!\n\n"
            "Would you like to register it? Reply with the service number from the BRS menu."
        ) + "\n\n" + _anything_else()

    if step == "BRS_RENEW_REG":
        state.step = "BRS_RENEW_MPESA"
        return f"Your business registration **{text}** is due for renewal. The renewal fee is **Ksh. 950**.\n\nPlease enter your **M-PESA number**."

    if step == "BRS_RENEW_MPESA":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number."
        state.step = "ANYTHING_ELSE"
        return "✅ Renewal payment initiated. You will receive an STK push shortly.\n\n" + _anything_else()

    if step == "BRS_REG_BUSINESS_NAME":
        state.data["business_name"] = text
        state.step = "BRS_REG_OWNER_NAME"
        return "What is the **owner's / director's full name**?"

    if step == "BRS_REG_OWNER_NAME":
        state.data["owner_name"] = text
        state.step = "BRS_REG_ID"
        return "What is the owner's **National ID Number**?"

    if step == "BRS_REG_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "BRS_REG_PHONE"
        return "What is the contact **phone number**?"

    if step == "BRS_REG_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "BRS_REG_COUNTY"
        return "In which **county** will the business operate?"

    if step == "BRS_REG_COUNTY":
        state.data["county"] = text
        state.step = "BRS_REG_MPESA"
        d = state.data
        return (
            "📋 **Confirm your details:**\n\n"
            f"   • Business Name: **{d['business_name']}**\n"
            f"   • Owner: **{d['owner_name']}**\n"
            f"   • ID: **{d['id_number']}**\n"
            f"   • Phone: **{d['phone']}**\n"
            f"   • County: **{d['county']}**\n"
            f"   • Fee: **Ksh. {d['fee']:,}**\n\n"
            "Please enter your **M-PESA number** to proceed."
        )

    if step == "BRS_REG_MPESA":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number."
        state.data["mpesa"] = text
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Payment initiated! Enter your M-PESA PIN when you receive the STK push.\n\n"
            "Your business will be registered within **3 working days**.\n\n"
            "You will receive your **Certificate of Registration** via email and SMS.\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# Immigration
# ===========================================================================

def _immigration(state: SessionState, text: str) -> str:
    step = state.step

    if step == "IMMIGRATION_MENU":
        SERVICES = ["Apply for a Passport", "Renew a Passport", "Apply for a Work Permit",
                    "Apply for a Student Pass", "Check Application Status"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("Immigration")
        state.service = pick
        state.data = {}

        fees = {
            "Apply for a Passport": 4550,
            "Renew a Passport": 4550,
            "Apply for a Work Permit": 50000,
            "Apply for a Student Pass": 10000,
        }

        if pick == "Check Application Status":
            state.step = "IMMIGRATION_STATUS_REF"
            return "Please enter your **Application Reference Number** or **Passport Number**."

        state.data["fee"] = fees.get(pick, 4550)
        state.step = "IMMIGRATION_NAME"
        return (
            f"✈️ I will help you with **{pick}**.\n\n"
            f"The application fee is **Ksh. {state.data['fee']:,}**.\n\n"
            "Please provide your **full name** as per National ID."
        )

    if step == "IMMIGRATION_NAME":
        state.data["name"] = text
        state.step = "IMMIGRATION_ID"
        return "What is your **National ID Number**?"

    if step == "IMMIGRATION_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "IMMIGRATION_PHONE"
        return "What is your **Phone Number**?"

    if step == "IMMIGRATION_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "IMMIGRATION_DOB"
        return "What is your **Date of Birth**? (DD/MM/YYYY)"

    if step == "IMMIGRATION_DOB":
        state.data["dob"] = text
        state.step = "IMMIGRATION_MPESA"
        return f"Please enter your **M-PESA number** to pay **Ksh. {state.data['fee']:,}**."

    if step == "IMMIGRATION_MPESA":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number."
        state.data["mpesa"] = text
        state.step = "IMMIGRATION_CONFIRM"
        d = state.data
        return (
            "📋 **Confirm your details:**\n\n"
            f"   • Name: **{d['name']}**\n"
            f"   • ID: **{d['id_number']}**\n"
            f"   • Phone: **{d['phone']}**\n"
            f"   • DOB: **{d['dob']}**\n"
            f"   • M-PESA: **{d['mpesa']}**\n"
            f"   • Fee: **Ksh. {d['fee']:,}**\n\n"
            "Is that correct? (Yes / No)"
        )

    if step == "IMMIGRATION_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "IMMIGRATION_NAME"
            state.data = {}
            return "Let's start over. Please provide your **full name**."
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Payment initiated! You will receive an STK push shortly.\n\n"
            "Once payment is confirmed, you will receive an **appointment date** via SMS.\n\n"
            "⚠️  You must visit the **Immigration offices** in person for biometrics and document verification.\n\n"
            "Processing time: **10–21 working days**.\n\n"
        ) + _anything_else()

    if step == "IMMIGRATION_STATUS_REF":
        state.step = "ANYTHING_ELSE"
        return (
            f"🔎 Status for **{text}**:\n\n"
            "✅ **Approved** – Your document is ready for collection.\n"
            "Please visit the Immigration office with your receipt.\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# Boma Yangu – Affordable Housing
# ===========================================================================

def _boma_yangu(state: SessionState, text: str) -> str:
    step = state.step

    if step == "BOMA_YANGU_MENU":
        SERVICES = ["Register / Create an Account", "Apply for a Housing Unit",
                    "Check Application Status", "Affordable Housing Levy Information"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("Boma Yangu")
        state.service = pick
        state.data = {}

        if pick == "Affordable Housing Levy Information":
            state.step = "ANYTHING_ELSE"
            return (
                "🏠 **Affordable Housing Levy**\n\n"
                "The Affordable Housing Levy is **1.5%** of your gross salary deducted monthly.\n\n"
                "Employers also contribute 1.5% matching your contribution.\n\n"
                "This goes towards funding affordable housing units for Kenyans.\n\n"
                "For more information visit **bomayangu.go.ke**\n\n"
            ) + _anything_else()

        if pick == "Check Application Status":
            state.step = "BOMA_STATUS_ID"
            return "Please enter your **National ID Number** or **Application Reference Number**."

        state.step = "BOMA_NAME"
        return "🏠 Please provide your **full name** as per National ID."

    if step == "BOMA_STATUS_ID":
        state.step = "ANYTHING_ELSE"
        return (
            f"🔎 Status for **{text}**:\n\n"
            "✅ **Registered** – You are in the priority queue for a 1-bedroom unit in Nairobi.\n"
            "Expected allocation: **2026 Q2**\n\n"
        ) + _anything_else()

    if step == "BOMA_NAME":
        state.data["name"] = text
        state.step = "BOMA_ID"
        return "What is your **National ID Number**?"

    if step == "BOMA_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "BOMA_PHONE"
        return "What is your **Phone Number**?"

    if step == "BOMA_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "BOMA_KRA"
        return "What is your **KRA PIN**?"

    if step == "BOMA_KRA":
        if not valid_kra_pin(text):
            return "Please enter a valid KRA PIN (e.g. A123456789B)."
        state.data["kra_pin"] = text
        state.step = "BOMA_COUNTY"
        return "In which **county** would you prefer your housing unit?"

    if step == "BOMA_COUNTY":
        state.data["county"] = text
        state.step = "BOMA_UNIT_TYPE"
        return (
            "Which type of unit are you applying for?\n\n"
            "1️⃣  Studio (Ksh. 900,000)\n"
            "2️⃣  1 Bedroom (Ksh. 1,500,000)\n"
            "3️⃣  2 Bedroom (Ksh. 3,000,000)\n"
            "4️⃣  3 Bedroom (Ksh. 4,500,000)"
        )

    if step == "BOMA_UNIT_TYPE":
        UNITS = ["Studio", "1 Bedroom", "2 Bedroom", "3 Bedroom"]
        pick = _numbered_pick(text, UNITS)
        if pick is None:
            return "Please select a valid unit type (1–4)."
        state.data["unit_type"] = pick
        state.step = "BOMA_CONFIRM"
        d = state.data
        return (
            "📋 **Confirm your details:**\n\n"
            f"   • Name: **{d['name']}**\n"
            f"   • ID: **{d['id_number']}**\n"
            f"   • Phone: **{d['phone']}**\n"
            f"   • KRA PIN: **{d['kra_pin']}**\n"
            f"   • County: **{d['county']}**\n"
            f"   • Unit Type: **{pick}**\n\n"
            "Is that correct? (Yes / No)"
        )

    if step == "BOMA_CONFIRM":
        yn = _yn(text)
        if yn is None: return "Please reply **Yes** or **No**."
        if not yn:
            state.step = "BOMA_NAME"
            state.data = {}
            return "Let's start over. Please provide your **full name**."
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Your Boma Yangu application has been **submitted**!\n\n"
            "Reference Number: **BY-2024-XXXXXX**\n\n"
            "You will receive an **SMS confirmation** shortly. Allocation is done by ballot.\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# Ministry of Health
# ===========================================================================

def _moh(state: SessionState, text: str) -> str:
    step = state.step

    if step == "MINISTRY_OF_HEALTH_MENU":
        SERVICES = ["NHIF Registration", "NHIF Contributions & Status", "Book Hospital Appointment",
                    "Health Facility Finder", "Vaccination / Immunisation Records"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("Ministry of Health")
        state.service = pick
        state.data = {}

        if pick == "Health Facility Finder":
            state.step = "MOH_FACILITY_COUNTY"
            return "Please enter your **county or town** to find nearby health facilities."

        if pick == "Vaccination / Immunisation Records":
            state.step = "MOH_VAX_ID"
            return "Please enter your **National ID Number** to retrieve your immunisation records."

        if pick == "NHIF Contributions & Status":
            state.step = "MOH_NHIF_STATUS_ID"
            return "Please enter your **NHIF Number** or **National ID Number**."

        state.step = "MOH_NAME"
        return f"🏥 I will help you with **{pick}**.\n\nPlease provide your **full name**."

    if step == "MOH_FACILITY_COUNTY":
        state.step = "ANYTHING_ELSE"
        return (
            f"🏥 Health facilities near **{text}**:\n\n"
            "1. Kenyatta National Hospital – 0.5 km\n"
            "2. Aga Khan Hospital – 1.2 km\n"
            "3. Nairobi Hospital – 1.8 km\n\n"
            "For a full list visit **health.go.ke**\n\n"
        ) + _anything_else()

    if step == "MOH_VAX_ID":
        state.step = "ANYTHING_ELSE"
        return (
            f"💉 Immunisation records for ID **{text}**:\n\n"
            "✅ COVID-19: 2 doses + booster (2021–2022)\n"
            "✅ Yellow Fever: Valid until 2031\n"
            "✅ Tetanus: Last dose 2020\n\n"
            "For official documentation visit your nearest health facility.\n\n"
        ) + _anything_else()

    if step == "MOH_NHIF_STATUS_ID":
        state.step = "ANYTHING_ELSE"
        return (
            f"💳 NHIF Status for **{text}**:\n\n"
            "✅ **Active Member** – 36 months of contributions\n"
            "Last contribution: **November 2024**\n"
            "Monthly amount: **Ksh. 500**\n\n"
        ) + _anything_else()

    if step == "MOH_NAME":
        state.data["name"] = text
        state.step = "MOH_ID"
        return "What is your **National ID Number**?"

    if step == "MOH_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "MOH_PHONE"
        return "What is your **Phone Number**?"

    if step == "MOH_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text

        if state.service == "NHIF Registration":
            state.step = "MOH_NHIF_EMPLOYMENT"
            return "What is your **employment status**? (Employed / Self-Employed / Unemployed)"

        if state.service == "Book Hospital Appointment":
            state.step = "MOH_APPT_HOSPITAL"
            return "Which **hospital or clinic** would you like to book an appointment at?"

    if step == "MOH_NHIF_EMPLOYMENT":
        state.data["employment"] = text
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Your NHIF registration has been **submitted**!\n\n"
            "You will receive your **NHIF Number** via SMS within 3 working days.\n\n"
            "Monthly contribution: **Ksh. 500** (self-employed / unemployed) or deducted from salary (employed).\n\n"
        ) + _anything_else()

    if step == "MOH_APPT_HOSPITAL":
        state.data["hospital"] = text
        state.step = "MOH_APPT_DATE"
        return "What **date** would you prefer for your appointment? (DD/MM/YYYY)"

    if step == "MOH_APPT_DATE":
        state.data["date"] = text
        state.step = "ANYTHING_ELSE"
        return (
            f"✅ Appointment booked at **{state.data['hospital']}** on **{text}**!\n\n"
            "You will receive an **SMS reminder** the day before.\n\n"
            "Please carry your **NHIF card** and **National ID**.\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# County Services
# ===========================================================================

def _county(state: SessionState, text: str) -> str:
    step = state.step

    if step == "COUNTY_SERVICES_MENU":
        SERVICES = ["Single Business Permit (SBP)", "Land Rates Payment", "County Health Certificate",
                    "Market / Trade Stall Application", "County Bursary Application"]
        pick = _numbered_pick(text, SERVICES)
        if pick is None:
            return _agency_service_menu("County Services")
        state.service = pick
        state.data = {}

        fees = {
            "Single Business Permit (SBP)": 5000,
            "Land Rates Payment": None,
            "County Health Certificate": 1500,
            "Market / Trade Stall Application": 2000,
            "County Bursary Application": 0,
        }
        state.data["fee"] = fees.get(pick)

        if pick == "Land Rates Payment":
            state.step = "COUNTY_RATES_PLOT"
            return "Please enter your **Plot / Land Reference Number**."

        if pick == "County Bursary Application":
            state.step = "COUNTY_BURSARY_NAME"
            return "I will help you apply for a **County Bursary**.\n\nPlease provide the **student's full name**."

        state.step = "COUNTY_SERVICE_NAME"
        return (
            f"🗺️ I will help you with **{pick}**.\n\n"
            f"{'The fee is **Ksh. ' + str(state.data['fee']) + '**.' if state.data['fee'] else ''}\n\n"
            "Please provide your **full name**."
        )

    if step == "COUNTY_RATES_PLOT":
        state.data["plot"] = text
        state.step = "COUNTY_RATES_AMOUNT"
        return f"The outstanding land rates for plot **{text}** are **Ksh. 12,500**.\n\nPlease enter your **M-PESA number** to pay."

    if step == "COUNTY_RATES_AMOUNT":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number."
        state.step = "ANYTHING_ELSE"
        return "✅ Land rates payment initiated. You will receive an STK push shortly.\n\n" + _anything_else()

    if step == "COUNTY_BURSARY_NAME":
        state.data["student_name"] = text
        state.step = "COUNTY_BURSARY_ID"
        return "What is the student's / guardian's **National ID Number**?"

    if step == "COUNTY_BURSARY_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "COUNTY_BURSARY_SCHOOL"
        return "What **school / college / university** is the student attending?"

    if step == "COUNTY_BURSARY_SCHOOL":
        state.data["school"] = text
        state.step = "COUNTY_BURSARY_PHONE"
        return "What is the **phone number** for correspondence?"

    if step == "COUNTY_BURSARY_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Bursary application **submitted**!\n\n"
            "Reference: **BUR-2024-XXXXXX**\n\n"
            "Results are announced at the end of each financial year. You will be notified via SMS.\n\n"
        ) + _anything_else()

    if step == "COUNTY_SERVICE_NAME":
        state.data["name"] = text
        state.step = "COUNTY_SERVICE_ID"
        return "What is your **National ID Number**?"

    if step == "COUNTY_SERVICE_ID":
        if not valid_id(text):
            return "Please enter a valid 7–8 digit ID number."
        state.data["id_number"] = text
        state.step = "COUNTY_SERVICE_PHONE"
        return "What is your **Phone Number**?"

    if step == "COUNTY_SERVICE_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "COUNTY_SERVICE_MPESA"
        return f"Please enter your **M-PESA number** to pay **Ksh. {state.data.get('fee', 0):,}**."

    if step == "COUNTY_SERVICE_MPESA":
        if not valid_mpesa(text):
            return "Please enter a valid M-PESA number."
        state.data["mpesa"] = text
        state.step = "ANYTHING_ELSE"
        return (
            "✅ Payment initiated! You will receive an STK push shortly.\n\n"
            "Your application will be processed within **5 working days**.\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# Emergency Reporting
# ===========================================================================

def _emergency_handler(state: SessionState, text: str) -> str:
    step = state.step

    if step in ("EMERGENCY", "MAIN_MENU"):
        state.step = "EMERGENCY_TYPE"
        return (
            "🚨 **Emergency Reporting**\n\n"
            "Please select the type of emergency:\n\n"
            "1️⃣  Medical Emergency\n"
            "2️⃣  Fire\n"
            "3️⃣  Crime / Security Threat\n"
            "4️⃣  Road Accident\n"
            "5️⃣  Natural Disaster\n"
            "6️⃣  Other\n\n"
            "Reply with a number or emergency type."
        )

    if step == "EMERGENCY_TYPE":
        TYPES = ["Medical Emergency", "Fire", "Crime / Security Threat",
                 "Road Accident", "Natural Disaster", "Other"]
        pick = _numbered_pick(text, TYPES)
        if pick is None:
            return "Please select a valid emergency type (1–6)."
        state.data["emergency_type"] = pick
        state.step = "EMERGENCY_LOCATION"
        return f"🚨 Noted – **{pick}**.\n\nPlease provide your **current location** (street, area, county)."

    if step == "EMERGENCY_LOCATION":
        state.data["location"] = text
        state.step = "EMERGENCY_PHONE"
        return "Please provide a **contact phone number** for emergency services to reach you."

    if step == "EMERGENCY_PHONE":
        if not valid_phone(text):
            return "Please enter a valid Kenyan phone number."
        state.data["phone"] = text
        state.step = "EMERGENCY_DESCRIPTION"
        return "Briefly **describe the emergency** (what happened, number of people involved, etc.)."

    if step == "EMERGENCY_DESCRIPTION":
        state.data["description"] = text
        state.step = "ANYTHING_ELSE"
        d = state.data
        return (
            "🚨 **Emergency Report Submitted!**\n\n"
            f"   • Type: **{d.get('emergency_type')}**\n"
            f"   • Location: **{d.get('location')}**\n"
            f"   • Contact: **{d.get('phone')}**\n\n"
            "✅ Emergency services have been **alerted**. Please stay calm.\n\n"
            "📞 Important numbers:\n"
            "   • Police: **999 / 112**\n"
            "   • Ambulance: **0800 723 253**\n"
            "   • Fire: **999**\n\n"
        ) + _anything_else()

    return _unknown(state)


# ===========================================================================
# Huduma Centre Lookup
# ===========================================================================

HUDUMA_CENTRES = {
    "nairobi":    "Huduma Centre Nairobi – GPO, Haile Selassie Avenue. Mon–Fri 8am–5pm.",
    "mombasa":    "Huduma Centre Mombasa – Reinsurance Plaza, Moi Ave. Mon–Fri 8am–5pm.",
    "kisumu":     "Huduma Centre Kisumu – Mega City Mall. Mon–Fri 8am–5pm.",
    "nakuru":     "Huduma Centre Nakuru – Mega Nakuru Complex. Mon–Fri 8am–5pm.",
    "eldoret":    "Huduma Centre Eldoret – Zion Mall, Uganda Road. Mon–Fri 8am–5pm.",
    "nyeri":      "Huduma Centre Nyeri – Arcade Building. Mon–Fri 8am–5pm.",
    "thika":      "Huduma Centre Thika – Stadium Road. Mon–Fri 8am–5pm.",
    "machakos":   "Huduma Centre Machakos – Wote Road. Mon–Fri 8am–5pm.",
    "garissa":    "Huduma Centre Garissa – Kismayu Road. Mon–Fri 8am–4pm.",
}


def _huduma_response(location: str, state: SessionState) -> str:
    key = location.strip().lower()
    for city, info in HUDUMA_CENTRES.items():
        if city in key or key in city:
            state.step = "ANYTHING_ELSE"
            return f"📍 {info}\n\n" + _anything_else()
    state.step = "ANYTHING_ELSE"
    return (
        f"I could not find a Huduma Centre specifically for **{location}**.\n\n"
        "Please visit **huduma.go.ke** or call **0800 221 222** for the full directory.\n\n"
    ) + _anything_else()


# ===========================================================================
# Constitution Q&A (routed to Gemini in production)
# ===========================================================================

def _constitution_response(question: str, state: SessionState) -> str:
    # In production this calls gemini_service.py with a constitution RAG context
    state.step = "ANYTHING_ELSE"
    return (
        f"📜 Regarding your question: *\"{question}\"*\n\n"
        "The Constitution of Kenya 2010 is the supreme law of the Republic. "
        "I am fetching the relevant chapter for you...\n\n"
        "*(This response is generated by Rafiki AI using RAG on the Kenyan Constitution.)*\n\n"
        "Is there anything else you would like to know about the Constitution?\n\n"
    ) + _anything_else()


# ===========================================================================
# Shared helpers
# ===========================================================================

def _anything_else() -> str:
    return "Is there anything else I can help you with? (Yes / No)"


def _unknown(state: SessionState) -> str:
    return (
        "I'm sorry, I didn't quite understand that. "
        "Please reply with a valid option or type **menu** to return to the main menu."
    )


# Catch "menu" keyword anywhere
_ORIGINAL_HANDLE = handle_message


def handle_message(session_id: str, user_input: str) -> str:  # type: ignore[no-redef]
    if user_input.strip().lower() in ("menu", "main menu", "start over", "restart"):
        state = get_or_create_session(session_id)
        state.step = "MAIN_MENU"
        state.agency = None
        state.service = None
        state.data = {}
        return _main_menu()

    # Handle "anything else" prompt
    state = get_or_create_session(session_id)
    if state.step == "ANYTHING_ELSE":
        yn = _yn(user_input)
        if yn is True:
            state.step = "MAIN_MENU"
            state.agency = None
            state.service = None
            state.data = {}
            return _main_menu()
        if yn is False:
            return (
                "Thank you for using Rafiki AI! 🙏\n\n"
                "To download your payment receipt or documents navigate to the "
                "**Transcripts** section of this platform.\n\n"
                "Have a wonderful day! 🇰🇪"
            )
        return _anything_else()

    return _ORIGINAL_HANDLE(session_id, user_input)