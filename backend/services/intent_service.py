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
    
    # Intent categories
    INTENT_KRA_NIL_RETURNS = "kra_nil_returns"
    INTENT_KRA_PIN_RECOVERY = "kra_pin_recovery"
    INTENT_KRA_PIN_GENERATION = "kra_pin_generation"
    INTENT_ITAX_HELP = "itax_help"
    INTENT_SERVICE_INQUIRY = "service_inquiry"
    INTENT_BOOKING = "book_appointment"
    INTENT_CONFIRMATION = "confirm"
    INTENT_NAVIGATION = "navigate"
    INTENT_CLARIFICATION = "clarify"
    INTENT_GREETING = "greeting"
    INTENT_HELP = "help"
    INTENT_UNKNOWN = "unknown"
    
    # KRA-related keywords
    KRA_NIL_RETURNS_KEYWORDS = [
        'nil returns', 'nil return', 'zero returns', 'no income',
        'file returns', 'file nil', 'submit returns', 'annual returns',
        'kra returns', 'income returns', 'tax returns'
    ]
    
    KRA_PIN_RECOVERY_KEYWORDS = [
        'recover pin', 'reset pin', 'forgotten pin', 'lost pin',
        'pin recovery', 'forgot pin', 'pin reset', 'new pin',
        'pin help', 'pin issue', 'pin problem'
    ]
    
    KRA_PIN_GENERATION_KEYWORDS = [
        'get pin', 'generate pin', 'create pin', 'new pin',
        'pin application', 'apply for pin', 'register for pin',
        'kra pin', 'pin number'
    ]
    
    ITAX_KEYWORDS = [
        'itax', 'i-tax', 'login', 'password', 'username',
        'dashboard', 'portal', 'account', 'access itax'
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
        
        Returns: 'en' or 'sw'
        """
        # Kiswahili-specific patterns
        sw_patterns = [
            r'\b(na|kwa|ni|wa|ja|za|ta|ka)\b',  # Common Kiswahili prepositions/conjugations
            r'\b(rafiki|habari|asante|pole|sawa|ndiyo|hapana|tafadhali)\b',  # Common Kiswahili words
            r'[aeiou]{2,}',  # Multiple consecutive vowels (more common in Sw)
        ]
        
        sw_score = sum(len(re.findall(pattern, message, re.IGNORECASE)) for pattern in sw_patterns)
        
        # If more Kiswahili patterns detected, default to Kiswahili
        return 'sw' if sw_score > 3 else 'en'
    
    def _normalize_message(self, message: str) -> str:
        """Normalize message for processing."""
        return message.lower().strip()
    
    def _detect_primary_intent(self, normalized: str) -> Tuple[str, float]:
        """
        Detect primary intent and confidence score.
        
        Returns: (intent, confidence_score)
        """
        # Check KRA-specific intents first
        if self._matches_keywords(normalized, self.KRA_NIL_RETURNS_KEYWORDS):
            return self.INTENT_KRA_NIL_RETURNS, 0.95
        
        if self._matches_keywords(normalized, self.KRA_PIN_RECOVERY_KEYWORDS):
            return self.INTENT_KRA_PIN_RECOVERY, 0.95
        
        if self._matches_keywords(normalized, self.KRA_PIN_GENERATION_KEYWORDS):
            return self.INTENT_KRA_PIN_GENERATION, 0.90
        
        if self._matches_keywords(normalized, self.ITAX_KEYWORDS):
            return self.INTENT_ITAX_HELP, 0.85
        
        # General intents
        if self._matches_keywords(normalized, self.GREETING_KEYWORDS):
            return self.INTENT_GREETING, 0.90
        
        if self._matches_keywords(normalized, self.HELP_KEYWORDS):
            return self.INTENT_HELP, 0.85
        
        if self._matches_keywords(normalized, self.CONFIRMATION_KEYWORDS):
            return self.INTENT_CONFIRMATION, 0.80
        
        if self._matches_keywords(normalized, self.NEGATION_KEYWORDS):
            return "negate", 0.80
        
        # Service inquiry detection
        if any(service in normalized for service in ['passport', 'id', 'license', 'permit', 'conduct', 'birth']):
            return self.INTENT_SERVICE_INQUIRY, 0.85
        
        # Booking detection
        if self._matches_keywords(normalized, ['book', 'appointment', 'schedule', 'reserve']):
            return self.INTENT_BOOKING, 0.80
        
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
        
        elif intent == self.INTENT_GREETING:
            return [
                "File nil returns",
                "Recover my KRA PIN",
                "Get a KRA PIN",
                "Book an appointment"
            ]
        
        elif intent == self.INTENT_HELP:
            return [
                "Can you help me navigate?",
                "What services are available?",
                "Go back to main menu"
            ]
        
        return [
            "Can you clarify that?",
            "Tell me more",
            "Try again"
        ]
    
    def _needs_confirmation(self, intent: str) -> bool:
        """Check if intent requires user confirmation."""
        confirmation_intents = [
            self.INTENT_BOOKING,
            self.INTENT_KRA_NIL_RETURNS,
            self.INTENT_KRA_PIN_RECOVERY,
            self.INTENT_KRA_PIN_GENERATION,
        ]
        return intent in confirmation_intents
    
    def _is_conversational(self, intent: str) -> bool:
        """Check if intent requires conversational response."""
        return intent in [
            self.INTENT_GREETING,
            self.INTENT_HELP,
            self.INTENT_UNKNOWN,
            self.INTENT_SERVICE_INQUIRY,
            self.INTENT_CLARIFICATION
        ]


# Global instance
intent_detector = IntentDetector()
