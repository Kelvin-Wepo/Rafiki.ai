"""
Intent detection and routing service for Rafiki platform.
Handles KRA nil returns, KRA PIN recovery, and other government workflows.
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


class IntentDetector:
    """
    Detects user intents and routes to appropriate workflows.
    Specialized for KRA and government service interactions.
    """
    
    # Intent categories - KRA
    INTENT_KRA_NIL_RETURNS = "kra_nil_returns"
    INTENT_KRA_PIN_RECOVERY = "kra_pin_recovery"
    INTENT_KRA_PIN_GENERATION = "kra_pin_generation"
    INTENT_KRA_PIN_VERIFICATION = "kra_pin_verification"
    INTENT_KRA_COMPLIANCE_CHECK = "kra_compliance_check"
    INTENT_ITAX_HELP = "itax_help"
    
    # Intent categories - IEBC (Voter Services)
    INTENT_VOTER_VERIFICATION = "voter_verification"
    INTENT_POLLING_STATION = "polling_station"
    
    # Intent categories - Location Services
    INTENT_HUDUMA_CENTRE = "huduma_centre"
    INTENT_DIRECTIONS = "directions"
    INTENT_TRAFFIC = "traffic"
    
    # Intent categories - Citizen Feedback/Reporting
    INTENT_FEEDBACK = "feedback"
    INTENT_EMERGENCY_REPORT = "emergency_report"
    INTENT_CORRUPTION_REPORT = "corruption_report"
    
    # General intents
    INTENT_SERVICE_INQUIRY = "service_inquiry"
    INTENT_BOOKING = "book_appointment"
    INTENT_MANAGE_APPOINTMENT = "manage_appointment"
    INTENT_CHECK_APPOINTMENT_STATUS = "check_appointment_status"
    INTENT_LIST_AGENCIES = "list_supported_agencies"
    INTENT_CONSTITUTIONAL_QA = "constitutional_qa_rag"
    INTENT_PASSPORT_APPOINTMENT = "passport_appointment"
    INTENT_CONFIRMATION = "confirm"
    INTENT_NAVIGATION = "navigate"
    INTENT_CLARIFICATION = "clarify"
    INTENT_GREETING = "greeting"
    INTENT_HELP = "help"
    INTENT_THANK_YOU = "thank_you"
    INTENT_GOODBYE = "goodbye"
    INTENT_UNKNOWN = "unknown"
    
    # Agency keywords mapping
    AGENCY_KEYWORDS = {
        'ntsa': ['ntsa', 'transport', 'driving', 'vehicle', 'logbook', 'license', 'leseni'],
        'kra': ['kra', 'tax', 'itax', 'pin', 'returns', 'revenue'],
        'nrb': ['nrb', 'national id', 'id card', 'kitambulisho', 'identity'],
        'dcrs': ['dcrs', 'birth certificate', 'death certificate', 'marriage certificate', 'civil registration'],
        'brs': ['brs', 'business registration', 'company', 'partnership'],
        'dci': ['dci', 'good conduct', 'police clearance', 'criminal investigation'],
        'cpb': ['counsellor', 'psychologist', 'therapist', 'mental health professional'],
        'moh': ['ministry of health', 'health', 'medical', 'hospital'],
        'county': ['county', 'local government', 'rates', 'permits']
    }
    
    # Keywords for listing agencies
    LIST_AGENCIES_KEYWORDS = [
        'what agencies', 'which agencies', 'supported agencies', 'list agencies',
        'available agencies', 'what services', 'which services', 'show agencies',
        'tell me agencies', 'what can you do', 'how can you help'
    ]
    
    # Keywords for appointment management
    MANAGE_APPOINTMENT_KEYWORDS = [
        'reschedule', 'cancel appointment', 'change appointment', 'modify booking',
        'update appointment', 'postpone', 'move appointment',
        # Kiswahili
        'panga tena', 'futa miadi', 'badilisha miadi', 'sogeza miadi'
    ]

    # Regex variants that tolerate filler words between the action verb and
    # 'appointment'/'booking' (e.g. "cancel my appointment", "change the appointment date")
    MANAGE_APPOINTMENT_PATTERNS = [
        r'\breschedule\b', r'\bpostpone\b',
        r'\bcancel\b.*\bappointment\b', r'\bcancel\b.*\bbooking\b',
        r'\bchange\b.*\bappointment\b', r'\bmodify\b.*\bbooking\b',
        r'\bupdate\b.*\bappointment\b', r'\bmove\b.*\bappointment\b',
    ]
    
    # Keywords for checking appointment status
    CHECK_STATUS_KEYWORDS = [
        'check status', 'appointment status', 'booking status', 'my appointment',
        'is my appointment', 'when is my', 'check my booking'
    ]
    
    # Constitutional/RAG query keywords
    CONSTITUTIONAL_KEYWORDS = [
        'constitution', 'katiba', 'bill of rights', 'article', 'chapter',
        'what does the constitution', 'constitutional', 'rights', 'haki',
        'law says', 'legal', 'amendment'
    ]
    
    # KRA-related keywords
    KRA_NIL_RETURNS_KEYWORDS = [
        'nil returns', 'nil return', 'zero returns', 'no income',
        'file returns', 'file nil', 'submit returns', 'annual returns',
        'kra returns', 'income returns', 'tax returns',
        # Kiswahili
        'kurudi sifuri', 'kurudi tupu', 'hakuna pendapatan', 'kurudi kila mwaka',
        'kufile kurudi', 'kufungua kurudi', 'kutuma kurudi'
    ]

    KRA_PIN_RECOVERY_KEYWORDS = [
        'recover pin', 'reset pin', 'forgotten pin', 'lost pin',
        'pin recovery', 'forgot pin', 'pin reset', 'forgot my',
        'pin help', 'pin issue', 'pin problem', 'lost my pin',
        'forgot my kra', 'lost my kra', 'cannot remember pin',
        # Kiswahili
        'komboa pin', 'badili pin', 'sahau pin', 'pin iliyopotea',
        'kukomboa pin', 'nimesahau pin', 'pin yangu imepotea'
    ]

    KRA_PIN_GENERATION_KEYWORDS = [
        'get pin', 'generate pin', 'create pin', 'need a pin',
        'pin application', 'apply for pin', 'register for pin',
        'pin number', 'new kra pin', 'first pin', 'need kra',
        'want a pin', 'want kra pin', 'need a kra', 'get a kra',
        'how do i get', 'obtain pin', 'obtain kra',
        # Kiswahili
        'pata pin', 'tengeneza pin', 'pin mpya', 'omba pin', 'ombi la pin',
        'nataka pin', 'ninataka pin ya kra'
    ]

    KRA_PIN_VERIFICATION_KEYWORDS = [
        'verify pin', 'check pin', 'validate pin', 'confirm pin',
        'pin valid', 'pin status', 'verify kra pin', 'check kra pin',
        'is my pin valid', 'pin verification', 'verify my pin',
        # Kiswahili
        'hakikisha pin', 'angalia pin', 'thibitisha pin'
    ]

    KRA_COMPLIANCE_KEYWORDS = [
        'tax compliance', 'compliance status', 'compliance certificate',
        'check compliance', 'am i compliant', 'tax compliant',
        'outstanding tax', 'outstanding returns', 'kra compliance',
        'compliance check', 'tax clearance',
        # Kiswahili
        'hali ya ushuru', 'cheti cha ushuru', 'angalia ushuru'
    ]

    ITAX_KEYWORDS = [
        'itax', 'i-tax', 'login', 'password', 'username',
        'dashboard', 'portal', 'account', 'access itax',
        # Kiswahili
        'ingia itax', 'neno siri', 'ingilia itax', 'mradi wa itax'
    ]
    
    GREETING_KEYWORDS = [
        'hello', 'hi', 'hey', 'good morning', 'good afternoon',
        'good evening', 'habari', 'jambo', 'asante', 'karibu',
        'how are you', 'how are you doing'
    ]
    
    CONFIRMATION_KEYWORDS = [
        'yes', 'yeah', 'yep', 'okay', 'ok', 'sure', 'confirmed',
        'proceed', 'go ahead', 'continue', 'ndiyo', 'sawa', 'kweli'
    ]
    
    NEGATION_KEYWORDS = [
        'no', 'nope', 'cancel', 'stop', 'don\'t', 'dont', 'back',
        'previous', 'hapana', 'simu', 'usisoma'
    ]
    
    HELP_KEYWORDS = [
        'help', 'assist', 'support', 'guide', 'explain', 'clarify',
        'how', 'what', 'confused', 'stuck', 'unclear', 'msaada'
    ]
    
    # IEBC/Voter keywords
    VOTER_KEYWORDS = [
        'voter', 'vote', 'voting', 'registered to vote', 'voter registration',
        'check registration', 'mpiga kura', 'usajili wa kura', 'kura'
    ]
    
    POLLING_STATION_KEYWORDS = [
        'polling station', 'where to vote', 'voting center', 'voting station',
        'kituo cha kura', 'kituo cha kupiga kura', 'where do i vote'
    ]
    
    # Location keywords
    HUDUMA_KEYWORDS = [
        'huduma', 'huduma centre', 'huduma center', 'nearest huduma',
        'government office', 'kituo cha huduma', 'find huduma'
    ]
    
    DIRECTIONS_KEYWORDS = [
        'directions', 'how to get', 'route to', 'way to', 'navigate to',
        'directions to', 'find', 'locate', 'njia', 'wapi'
    ]
    
    TRAFFIC_KEYWORDS = [
        'traffic', 'congestion', 'jam', 'msongamano', 'barabara',
        'road conditions', 'traffic update', 'traffic status'
    ]
    
    # Citizen feedback keywords
    FEEDBACK_KEYWORDS = [
        'feedback', 'suggestion', 'comment', 'complain', 'complaint',
        'maoni', 'pendekezo', 'malalamiko', 'review'
    ]
    
    EMERGENCY_KEYWORDS = [
        'emergency', 'urgent help', 'danger', 'police', 'fire',
        'ambulance', 'dharura', 'hatari', '999', '112', 'accident',
        'help me now', 'need help urgently', 'emergency help'
    ]
    
    CORRUPTION_KEYWORDS = [
        'corruption', 'bribe', 'corrupt', 'ufisadi', 'rushwa',
        'report corruption', 'whistleblower', 'report bribe'
    ]
    
    # Thank you and goodbye
    THANK_YOU_KEYWORDS = [
        'thank', 'thanks', 'asante', 'nashukuru', 'appreciate'
    ]
    
    GOODBYE_KEYWORDS = [
        'bye', 'goodbye', 'see you', 'exit', 'quit', 'kwaheri', 'end'
    ]
    
    def __init__(self):
        """Initialize intent detector."""
        self.language = 'en'
    
    def detect(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect user intent from message.
        
        Args:
            message: User message text
            conversation_history: Previous conversation turns
            session_context: Current session state (language, progress, etc.)
        
        Returns:
            Dict with intent, confidence, workflow, entities, and suggestions
        """
        try:
            # Detect language
            self.language = self._detect_language(message)
            
            # Normalize message
            normalized = self._normalize_message(message)
            
            # Detect primary intent
            intent, confidence = self._detect_primary_intent(normalized)
            
            # Extract entities
            entities = self._extract_entities(message, intent)
            
            # Determine workflow and next steps
            workflow = self._get_workflow(intent, entities, session_context)
            
            # Generate suggestions
            suggestions = self._get_suggestions(intent, workflow)
            
            return {
                "intent": intent,
                "confidence": confidence,
                "language": self.language,
                "normalized_message": normalized,
                "entities": entities,
                "workflow": workflow,
                "suggested_actions": suggestions,
                "requires_confirmation": self._needs_confirmation(intent),
                "is_conversational": self._is_conversational(intent)
            }
        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            return {
                "intent": self.INTENT_UNKNOWN,
                "confidence": 0.0,
                "language": self.language,
                "entities": {},
                "workflow": None,
                "suggested_actions": ["Could you clarify what you need?"],
                "requires_confirmation": False,
                "is_conversational": True
            }
    
    def _detect_language(self, message: str) -> str:
        """
        Detect if message is in English or Kiswahili.
        
        Returns: 'en', 'sw', or 'mixed'
        """
        # Kiswahili-specific patterns
        sw_patterns = [
            r'\b(na|kwa|ni|wa|ja|za|ta|ka)\b',  # Common Kiswahili prepositions/conjugations
            r'\b(rafiki|habari|asante|pole|sawa|ndiyo|hapana|tafadhali)\b',  # Common Kiswahili words
            r'\b(nataka|ninataka|ninajua|sijui|niko|leseni|huduma)\b',  # Common spoken words
            r'[aeiou]{2,}',  # Multiple consecutive vowels (more common in Sw)
        ]
        
        sw_score = sum(len(re.findall(pattern, message, re.IGNORECASE)) for pattern in sw_patterns)
        
        # FIXED: was > 3, too strict for short phrases. Now > 1 for better Kiswahili detection
        if sw_score > 1:
            return 'sw'
        elif sw_score == 1:
            return 'mixed'  # Single Kiswahili indicator suggests code-switching
        else:
            return 'en'
    
    def _normalize_message(self, message: str) -> str:
        """Normalize message for processing."""
        return message.lower().strip()
    
    def _detect_primary_intent(self, normalized: str) -> Tuple[str, float]:
        """
        Detect primary intent and confidence score.
        
        Returns: (intent, confidence_score)
        """
        # EMERGENCY - Highest priority
        if self._matches_keywords(normalized, self.EMERGENCY_KEYWORDS):
            return self.INTENT_EMERGENCY_REPORT, 0.98
        
        # Constitutional Q&A - high priority for specific queries
        if self._matches_keywords(normalized, self.CONSTITUTIONAL_KEYWORDS):
            return self.INTENT_CONSTITUTIONAL_QA, 0.95
        
        # List agencies intent
        if self._matches_keywords(normalized, self.LIST_AGENCIES_KEYWORDS):
            return self.INTENT_LIST_AGENCIES, 0.95
        
        # Appointment management intents (checked before status/booking so that
        # "cancel my appointment" etc. don't get misread as a status check)
        if self._matches_keywords(normalized, self.MANAGE_APPOINTMENT_KEYWORDS) or \
                any(re.search(p, normalized) for p in self.MANAGE_APPOINTMENT_PATTERNS):
            return self.INTENT_MANAGE_APPOINTMENT, 0.93

        if self._matches_keywords(normalized, self.CHECK_STATUS_KEYWORDS):
            return self.INTENT_CHECK_APPOINTMENT_STATUS, 0.93

        # Booking intent (checked before generic service-inquiry so "book a passport
        # appointment" isn't swallowed by the bare "passport" keyword match below)
        if self._matches_keywords(normalized, ['book', 'appointment', 'schedule', 'reserve', 'weka miadi', 'panga miadi', 'omba miadi']):
            return self.INTENT_BOOKING, 0.80
        
        # Check KRA-specific intents
        if self._matches_keywords(normalized, self.KRA_NIL_RETURNS_KEYWORDS):
            return self.INTENT_KRA_NIL_RETURNS, 0.95
        
        if self._matches_keywords(normalized, self.KRA_PIN_RECOVERY_KEYWORDS):
            return self.INTENT_KRA_PIN_RECOVERY, 0.95
        
        if self._matches_keywords(normalized, self.KRA_PIN_GENERATION_KEYWORDS):
            return self.INTENT_KRA_PIN_GENERATION, 0.90
        
        if self._matches_keywords(normalized, self.ITAX_KEYWORDS):
            return self.INTENT_ITAX_HELP, 0.85
        
        # IEBC/Voter intents
        if self._matches_keywords(normalized, self.VOTER_KEYWORDS):
            return self.INTENT_VOTER_VERIFICATION, 0.90
        
        if self._matches_keywords(normalized, self.POLLING_STATION_KEYWORDS):
            return self.INTENT_POLLING_STATION, 0.90
        
        # Location intents (check before help since "how" is in help)
        if self._matches_keywords(normalized, self.HUDUMA_KEYWORDS):
            return self.INTENT_HUDUMA_CENTRE, 0.90
        
        if self._matches_keywords(normalized, self.DIRECTIONS_KEYWORDS):
            return self.INTENT_DIRECTIONS, 0.85
        
        if self._matches_keywords(normalized, self.TRAFFIC_KEYWORDS):
            return self.INTENT_TRAFFIC, 0.85
        
        # Citizen feedback/reporting
        if self._matches_keywords(normalized, self.CORRUPTION_KEYWORDS):
            return self.INTENT_CORRUPTION_REPORT, 0.92
        
        if self._matches_keywords(normalized, self.FEEDBACK_KEYWORDS):
            return self.INTENT_FEEDBACK, 0.85
        
        # Thank you and goodbye (before help)
        if self._matches_keywords(normalized, self.THANK_YOU_KEYWORDS):
            return self.INTENT_THANK_YOU, 0.90
        
        if self._matches_keywords(normalized, self.GOODBYE_KEYWORDS):
            return self.INTENT_GOODBYE, 0.90
        
        # Service inquiry detection (booking already checked above)
        if any(service in normalized for service in ['passport', 'id', 'license', 'permit', 'conduct', 'birth']):
            return self.INTENT_SERVICE_INQUIRY, 0.85

        # General intents (lower priority)
        if self._matches_keywords(normalized, self.GREETING_KEYWORDS):
            return self.INTENT_GREETING, 0.90
        
        # Only check help if no other specific intent matched and user is clearly asking for help
        help_specific = ['help', 'assist', 'support', 'guide', 'msaada', 'confused', 'stuck', 'unclear']
        if self._matches_keywords(normalized, help_specific):
            return self.INTENT_HELP, 0.85
        
        if self._matches_keywords(normalized, self.CONFIRMATION_KEYWORDS):
            return self.INTENT_CONFIRMATION, 0.80
        
        if self._matches_keywords(normalized, self.NEGATION_KEYWORDS):
            return "negate", 0.80
        
        return self.INTENT_UNKNOWN, 0.5
    
    def _matches_keywords(self, normalized: str, keywords: List[str]) -> bool:
        """Check if message contains keywords."""
        return any(keyword in normalized for keyword in keywords)
    
    def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """Extract entities from message based on intent."""
        entities = {}
        
        # Extract phone number
        phone_match = re.search(r'(?:\+254|0)?[17]\d{8}', message)
        if phone_match:
            entities['phone_number'] = phone_match.group()
        
        # Extract KRA PIN (10 digits)
        kra_pin_match = re.search(r'\b\d{10}\b', message)
        if kra_pin_match and len(kra_pin_match.group()) == 10:
            entities['kra_pin'] = kra_pin_match.group()
        
        # Extract national ID (8 digits usually, sometimes with spaces)
        id_match = re.search(r'\b\d{8}\b|\d{2}\s*\d{2}\s*\d{2}\s*\d{2}', message)
        if id_match:
            entities['national_id'] = id_match.group().replace(' ', '')
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
        if email_match:
            entities['email'] = email_match.group()
        
        # Extract names (capitalize first letters)
        name_match = re.search(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', message)
        if name_match:
            entities['user_name'] = name_match.group()
        
        # Intent-specific entity extraction
        if intent == self.INTENT_KRA_NIL_RETURNS:
            entities['service_type'] = 'nil_returns'
            entities['requires_pin'] = 'kra_pin' not in entities
        
        elif intent == self.INTENT_KRA_PIN_RECOVERY:
            entities['service_type'] = 'pin_recovery'
            entities['requires_identification'] = 'national_id' not in entities
        
        elif intent == self.INTENT_KRA_PIN_GENERATION:
            entities['service_type'] = 'pin_generation'
            entities['requires_identification'] = 'national_id' not in entities
        
        elif intent == self.INTENT_BOOKING:
            # Extract date patterns
            date_match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', message)
            if date_match:
                entities['date'] = date_match.group()
            
            # Extract time slot
            if 'morning' in message.lower() or 'am' in message.lower():
                entities['time_slot'] = 'morning'
            elif 'afternoon' in message.lower() or 'pm' in message.lower():
                entities['time_slot'] = 'afternoon'
        
        return entities
    
    def _get_workflow(
        self,
        intent: str,
        entities: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the workflow steps for a detected intent.
        
        Returns: Workflow dict or None
        """
        if intent == self.INTENT_KRA_NIL_RETURNS:
            return {
                "name": "KRA Nil Returns Filing",
                "steps": [
                    "Confirm user has KRA PIN",
                    "Explain nil returns eligibility",
                    "Navigate to iTax portal",
                    "Guide through login",
                    "Guide through nil returns form",
                    "Confirm submission",
                    "Offer SMS confirmation"
                ],
                "urls": ["https://accounts.ecitizen.go.ke/en/services/itax"],
                "requires_authentication": True,
                "sms_confirmation": True
            }
        
        elif intent == self.INTENT_KRA_PIN_RECOVERY:
            return {
                "name": "KRA PIN Recovery",
                "steps": [
                    "Verify user identity (national ID)",
                    "Explain recovery process",
                    "Ask for registered email/phone",
                    "Guide through recovery link",
                    "Confirm new PIN delivery",
                    "Offer SMS confirmation"
                ],
                "urls": ["https://accounts.ecitizen.go.ke/en/services/pin-recovery"],
                "requires_authentication": False,
                "sms_confirmation": True
            }
        
        elif intent == self.INTENT_KRA_PIN_GENERATION:
            return {
                "name": "KRA PIN Generation",
                "steps": [
                    "Verify user identity (national ID)",
                    "Explain PIN requirements",
                    "Navigate to iTax registration",
                    "Guide through registration form",
                    "Confirm PIN assignment",
                    "Offer SMS PIN confirmation"
                ],
                "urls": ["https://accounts.ecitizen.go.ke/en/services/pin-registration"],
                "requires_authentication": False,
                "sms_confirmation": True
            }
        
        elif intent == self.INTENT_ITAX_HELP:
            return {
                "name": "iTax Portal Assistance",
                "steps": [
                    "Determine specific issue",
                    "Provide login guidance",
                    "Offer step-by-step help",
                    "Confirm issue resolved"
                ],
                "urls": ["https://itax.kra.go.ke"],
                "requires_authentication": True,
                "sms_confirmation": False
            }
        
        elif intent == self.INTENT_BOOKING:
            return {
                "name": "Appointment Booking",
                "steps": [
                    "Confirm service type",
                    "Verify user identity",
                    "Confirm preferred date/time",
                    "Take contact details",
                    "Send SMS confirmation"
                ],
                "urls": [],
                "requires_authentication": False,
                "sms_confirmation": True
            }
        
        # IEBC/Voter workflows
        elif intent == self.INTENT_VOTER_VERIFICATION:
            return {
                "name": "IEBC Voter Registration Check",
                "steps": [
                    "Collect National ID number",
                    "Query IEBC voter database",
                    "Return registration status",
                    "Provide polling station if registered",
                    "Offer voter registration guidance if not"
                ],
                "urls": ["https://orac.iebc.or.ke/verify"],
                "requires_authentication": False,
                "sms_confirmation": True
            }
        
        elif intent == self.INTENT_POLLING_STATION:
            return {
                "name": "Find Polling Station",
                "steps": [
                    "Verify voter registration",
                    "Look up assigned polling station",
                    "Provide station name and location",
                    "Offer directions if needed"
                ],
                "urls": ["https://orac.iebc.or.ke/verify"],
                "requires_authentication": False,
                "sms_confirmation": True
            }
        
        # Location workflows
        elif intent == self.INTENT_HUDUMA_CENTRE:
            return {
                "name": "Find Nearest Huduma Centre",
                "steps": [
                    "Get user location/city",
                    "Query Huduma Centre database",
                    "Return nearest centres",
                    "Provide services available",
                    "Offer directions"
                ],
                "urls": ["https://www.hudumakenya.go.ke"],
                "requires_authentication": False,
                "sms_confirmation": False
            }
        
        elif intent == self.INTENT_DIRECTIONS:
            return {
                "name": "Get Directions",
                "steps": [
                    "Confirm destination",
                    "Get user starting point",
                    "Calculate route",
                    "Provide step-by-step directions"
                ],
                "urls": [],
                "requires_authentication": False,
                "sms_confirmation": False
            }
        
        elif intent == self.INTENT_TRAFFIC:
            return {
                "name": "Traffic Information",
                "steps": [
                    "Get route/destination",
                    "Query traffic conditions",
                    "Provide current status",
                    "Suggest alternatives if congested"
                ],
                "urls": [],
                "requires_authentication": False,
                "sms_confirmation": False
            }
        
        # Citizen feedback/reporting workflows
        elif intent == self.INTENT_FEEDBACK:
            return {
                "name": "Submit Citizen Feedback",
                "steps": [
                    "Ask if anonymous submission",
                    "Collect feedback category",
                    "Collect feedback message",
                    "Confirm and submit",
                    "Provide reference number"
                ],
                "urls": [],
                "requires_authentication": False,
                "sms_confirmation": True
            }
        
        elif intent == self.INTENT_EMERGENCY_REPORT:
            return {
                "name": "Emergency Report",
                "steps": [
                    "Provide emergency numbers (999, 112)",
                    "Identify emergency type",
                    "Provide immediate guidance",
                    "Log report for follow-up"
                ],
                "urls": [],
                "requires_authentication": False,
                "sms_confirmation": False,
                "is_urgent": True
            }
        
        elif intent == self.INTENT_CORRUPTION_REPORT:
            return {
                "name": "Anonymous Corruption Report",
                "steps": [
                    "Explain whistleblower protections",
                    "Collect incident type",
                    "Collect incident details (encrypted)",
                    "Submit anonymously",
                    "Provide reference number"
                ],
                "urls": ["https://www.eacc.go.ke"],
                "requires_authentication": False,
                "sms_confirmation": False,
                "is_anonymous": True
            }
        
        return None
    
    def _get_suggestions(self, intent: str, workflow: Optional[Dict[str, Any]]) -> List[str]:
        """Get suggested next actions for user."""
        if intent == self.INTENT_KRA_NIL_RETURNS:
            return [
                "Guide me through filing nil returns",
                "Open iTax portal",
                "Do I qualify for nil returns?"
            ]
        
        elif intent == self.INTENT_KRA_PIN_RECOVERY:
            return [
                "Help me recover my PIN",
                "Send recovery link to my email",
                "Explain the recovery process"
            ]
        
        elif intent == self.INTENT_KRA_PIN_GENERATION:
            return [
                "Apply for a new KRA PIN",
                "What do I need to get a PIN?",
                "Start the registration process"
            ]
        
        # IEBC/Voter suggestions
        elif intent == self.INTENT_VOTER_VERIFICATION:
            return [
                "Check my voter status",
                "Find my polling station",
                "How do I register to vote?"
            ]
        
        elif intent == self.INTENT_POLLING_STATION:
            return [
                "Get directions to my station",
                "What do I need to vote?",
                "Check my registration"
            ]
        
        # Location suggestions
        elif intent == self.INTENT_HUDUMA_CENTRE:
            return [
                "Find nearest Huduma Centre",
                "What services are available?",
                "Get directions"
            ]
        
        elif intent == self.INTENT_DIRECTIONS:
            return [
                "Get directions",
                "Check traffic first",
                "Find government offices"
            ]
        
        elif intent == self.INTENT_TRAFFIC:
            return [
                "Show traffic updates",
                "Find alternate route",
                "Check specific road"
            ]
        
        # Citizen feedback suggestions
        elif intent == self.INTENT_FEEDBACK:
            return [
                "Submit anonymous feedback",
                "Submit with contact info",
                "Learn about feedback process"
            ]
        
        elif intent == self.INTENT_EMERGENCY_REPORT:
            return [
                "Call 999 (Police/Fire/Ambulance)",
                "Call 112 (National Emergency)",
                "Report non-urgent issue"
            ]
        
        elif intent == self.INTENT_CORRUPTION_REPORT:
            return [
                "Report anonymously",
                "Learn about whistleblower protection",
                "Contact EACC directly"
            ]
        
        elif intent == self.INTENT_GREETING:
            return [
                "File nil returns",
                "Recover my KRA PIN",
                "Check voter registration",
                "Book an appointment",
                "Find Huduma Centre"
            ]
        
        elif intent == self.INTENT_HELP:
            return [
                "KRA services",
                "Voter services",
                "Book appointments",
                "Find government offices",
                "Report an issue"
            ]
        
        elif intent == self.INTENT_THANK_YOU:
            return [
                "Need anything else?",
                "Start a new request",
                "Goodbye"
            ]
        
        elif intent == self.INTENT_GOODBYE:
            return []  # No suggestions needed for goodbye
        
        return [
            "Can you clarify that?",
            "Tell me more",
            "Start over"
        ]
    
    def _needs_confirmation(self, intent: str) -> bool:
        """Check if intent requires user confirmation."""
        confirmation_intents = [
            self.INTENT_BOOKING,
            self.INTENT_KRA_NIL_RETURNS,
            self.INTENT_KRA_PIN_RECOVERY,
            self.INTENT_KRA_PIN_GENERATION,
            self.INTENT_FEEDBACK,
            self.INTENT_CORRUPTION_REPORT,
        ]
        return intent in confirmation_intents
    
    def _is_conversational(self, intent: str) -> bool:
        """Check if intent requires conversational response."""
        return intent in [
            self.INTENT_GREETING,
            self.INTENT_HELP,
            self.INTENT_UNKNOWN,
            self.INTENT_SERVICE_INQUIRY,
            self.INTENT_CLARIFICATION,
            self.INTENT_THANK_YOU,
            self.INTENT_GOODBYE
        ]


# Global instance
intent_detector = IntentDetector()
