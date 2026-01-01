"""
Dialogflow integration for conversation management.
"""

import uuid
from typing import Dict, Any, Optional, List

from config import get_settings, GOVERNMENT_SERVICES
from utils import get_logger

logger = get_logger(__name__)

# Try to import Dialogflow, gracefully handle if not available
try:
    from google.cloud import dialogflow_v2 as dialogflow
    DIALOGFLOW_AVAILABLE = True
except ImportError:
    DIALOGFLOW_AVAILABLE = False
    logger.warning("Dialogflow library not installed. Using fallback conversation management.")


class DialogflowService:
    """
    Service for Dialogflow conversation management.
    Provides intent matching and conversation flow control.
    """
    
    def __init__(self):
        """Initialize Dialogflow service."""
        self.settings = get_settings()
        self._session_client = None
        self._initialized = False
        self._fallback_intents = self._build_fallback_intents()
    
    def _build_fallback_intents(self) -> Dict[str, Dict[str, Any]]:
        """Build fallback intent patterns for when Dialogflow is unavailable."""
        return {
            "greeting": {
                "patterns": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings"],
                "responses": [
                    "Hello! I'm Wanjiku, your eCitizen booking assistant. How can I help you today?",
                    "Hi there! I'm here to help you access government services. What would you like to do?"
                ],
                "context": "welcome"
            },
            "book_appointment": {
                "patterns": ["book", "appointment", "schedule", "reserve", "booking"],
                "responses": [
                    "I can help you book an appointment. Which service do you need? "
                    "Options are: Passport, National ID, Driving License, or Certificate of Good Conduct."
                ],
                "context": "booking_service_selection",
                "requires_entity": "service_type"
            },
            "service_passport": {
                "patterns": ["passport"],
                "responses": [
                    "Great! You want to book a passport appointment. "
                    "May I have your full name please?"
                ],
                "context": "booking_name",
                "sets_entity": {"service_type": "passport"}
            },
            "service_national_id": {
                "patterns": ["national id", "id card", "identity card", "id"],
                "responses": [
                    "Great! You want to book an appointment for National ID. "
                    "May I have your full name please?"
                ],
                "context": "booking_name",
                "sets_entity": {"service_type": "national_id"}
            },
            "service_driving_license": {
                "patterns": ["driving license", "driver's license", "driving licence", "license"],
                "responses": [
                    "Great! You want to book a driving license appointment. "
                    "May I have your full name please?"
                ],
                "context": "booking_name",
                "sets_entity": {"service_type": "driving_license"}
            },
            "service_good_conduct": {
                "patterns": ["good conduct", "police clearance", "certificate of good conduct", "conduct"],
                "responses": [
                    "Great! You want to book an appointment for Certificate of Good Conduct. "
                    "May I have your full name please?"
                ],
                "context": "booking_name",
                "sets_entity": {"service_type": "good_conduct"}
            },
            "provide_name": {
                "patterns": ["my name is", "i am", "call me", "name is"],
                "context": "booking_phone",
                "extract_entity": "user_name"
            },
            "provide_phone": {
                "patterns": ["phone", "number", "07", "+254", "254"],
                "context": "booking_time",
                "extract_entity": "phone_number"
            },
            "time_morning": {
                "patterns": ["morning", "8 to 12", "8-12", "8am", "before noon"],
                "context": "booking_confirm",
                "sets_entity": {"time_slot": "08:00-12:00"}
            },
            "time_afternoon": {
                "patterns": ["afternoon", "2 to 5", "2-5", "2pm", "after noon"],
                "context": "booking_confirm",
                "sets_entity": {"time_slot": "14:00-17:00"}
            },
            "confirm_yes": {
                "patterns": ["yes", "confirm", "correct", "right", "okay", "sure", "proceed"],
                "responses": ["Your appointment has been confirmed. You will receive an SMS shortly."],
                "context": "booking_complete",
                "sets_entity": {"confirmation": True}
            },
            "confirm_no": {
                "patterns": ["no", "cancel", "wrong", "incorrect", "stop"],
                "responses": ["No problem. Would you like to start over?"],
                "context": "welcome",
                "sets_entity": {"confirmation": False}
            },
            "help": {
                "patterns": ["help", "assist", "support", "what can you do", "options"],
                "responses": [
                    "I can help you with: "
                    "1. Booking appointments for Passport, National ID, Driving License, or Good Conduct certificate. "
                    "2. Checking service requirements. "
                    "3. Navigating the eCitizen portal. "
                    "Just tell me what you need!"
                ],
                "context": "help"
            },
            "services_list": {
                "patterns": ["services", "what services", "available services", "list services"],
                "responses": [
                    "Available services are: "
                    "1. Passport Application, "
                    "2. National ID Card, "
                    "3. Driving License, "
                    "4. Certificate of Good Conduct. "
                    "Which one would you like?"
                ],
                "context": "service_selection"
            },
            "thank_you": {
                "patterns": ["thank", "thanks", "appreciate"],
                "responses": [
                    "You're welcome! Is there anything else I can help you with?",
                    "My pleasure! Feel free to ask if you need anything else."
                ],
                "context": "welcome"
            },
            "goodbye": {
                "patterns": ["bye", "goodbye", "see you", "exit", "quit"],
                "responses": [
                    "Goodbye! Thank you for using eCitizen services. Have a great day!",
                    "Take care! Come back anytime you need help with government services."
                ],
                "context": "end"
            },
            "fallback": {
                "patterns": [],
                "responses": [
                    "I'm sorry, I didn't quite understand that. Could you please rephrase?",
                    "I'm not sure what you mean. You can say 'help' to see what I can do."
                ],
                "context": "fallback"
            }
        }
    
    def initialize(self) -> bool:
        """
        Initialize the Dialogflow client.
        
        Returns:
            True if initialization successful
        """
        if not DIALOGFLOW_AVAILABLE:
            logger.info("Using fallback conversation management (Dialogflow not available)")
            self._initialized = True
            return True
        
        try:
            if not self.settings.DIALOGFLOW_PROJECT_ID:
                logger.warning("Dialogflow project ID not configured, using fallback")
                self._initialized = True
                return True
            
            self._session_client = dialogflow.SessionsClient()
            self._initialized = True
            logger.info("Dialogflow service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Dialogflow: {e}")
            logger.info("Falling back to pattern-based intent matching")
            self._initialized = True
            return True
    
    async def detect_intent(
        self,
        text: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect intent from user text.
        
        Args:
            text: User input text
            session_id: Session identifier for conversation tracking
            context: Current conversation context
        
        Returns:
            Dict with intent, entities, response, and context
        """
        if not self._initialized:
            self.initialize()
        
        # Try Dialogflow first if available and configured
        if DIALOGFLOW_AVAILABLE and self._session_client and self.settings.DIALOGFLOW_PROJECT_ID:
            try:
                return await self._detect_intent_dialogflow(text, session_id, context)
            except Exception as e:
                logger.error(f"Dialogflow detection failed, using fallback: {e}")
        
        # Fallback to pattern matching
        return self._detect_intent_fallback(text, context)
    
    async def _detect_intent_dialogflow(
        self,
        text: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect intent using Dialogflow."""
        session = self._session_client.session_path(
            self.settings.DIALOGFLOW_PROJECT_ID,
            session_id
        )
        
        text_input = dialogflow.TextInput(
            text=text,
            language_code=self.settings.DIALOGFLOW_LANGUAGE_CODE
        )
        
        query_input = dialogflow.QueryInput(text=text_input)
        
        # Add context if available
        query_params = None
        if context and context.get("dialogflow_contexts"):
            query_params = dialogflow.QueryParameters(
                contexts=context["dialogflow_contexts"]
            )
        
        response = self._session_client.detect_intent(
            request={
                "session": session,
                "query_input": query_input,
                "query_params": query_params
            }
        )
        
        result = response.query_result
        
        # Extract entities
        entities = {}
        for param_name, param_value in result.parameters.items():
            if param_value:
                entities[param_name] = param_value
        
        return {
            "intent": result.intent.display_name,
            "confidence": result.intent_detection_confidence,
            "response": result.fulfillment_text,
            "entities": entities,
            "context": result.output_contexts,
            "requires_input": not result.all_required_params_present
        }
    
    def _detect_intent_fallback(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fallback pattern-based intent detection."""
        text_lower = text.lower().strip()
        current_context = context.get("conversation_context", "welcome") if context else "welcome"
        
        # Track extracted entities
        entities = context.get("entities", {}) if context else {}
        
        # Context-aware matching
        if current_context == "booking_name":
            # Extract name from input
            name = self._extract_name(text)
            if name:
                entities["user_name"] = name
                return {
                    "intent": "provide_name",
                    "confidence": 0.8,
                    "response": f"Thank you, {name}. Now, please provide your phone number for SMS confirmation.",
                    "entities": entities,
                    "context": "booking_phone",
                    "requires_input": True
                }
        
        elif current_context == "booking_phone":
            # Extract phone number
            phone = self._extract_phone(text)
            if phone:
                entities["phone_number"] = phone
                return {
                    "intent": "provide_phone",
                    "confidence": 0.8,
                    "response": "Great! Which time works better for you? Morning (8 AM to 12 PM) or Afternoon (2 PM to 5 PM)?",
                    "entities": entities,
                    "context": "booking_time",
                    "requires_input": True
                }
        
        elif current_context == "booking_time":
            # Check for time slot
            for intent_name in ["time_morning", "time_afternoon"]:
                intent_data = self._fallback_intents[intent_name]
                if any(pattern in text_lower for pattern in intent_data["patterns"]):
                    entities.update(intent_data.get("sets_entity", {}))
                    service_name = GOVERNMENT_SERVICES.get(
                        entities.get("service_type", ""),
                        {"name": "the service"}
                    )["name"]
                    time_display = "morning (8 AM to 12 PM)" if "morning" in intent_name else "afternoon (2 PM to 5 PM)"
                    
                    return {
                        "intent": intent_name,
                        "confidence": 0.9,
                        "response": f"Let me confirm: You want to book a {service_name} appointment for {entities.get('user_name', 'you')} "
                                   f"in the {time_display}. Your confirmation SMS will be sent to {entities.get('phone_number', 'your phone')}. "
                                   f"Is this correct?",
                        "entities": entities,
                        "context": "booking_confirm",
                        "requires_input": True
                    }
        
        elif current_context == "booking_confirm":
            # Check for confirmation
            if any(pattern in text_lower for pattern in self._fallback_intents["confirm_yes"]["patterns"]):
                entities["confirmation"] = True
                return {
                    "intent": "confirm_booking",
                    "confidence": 0.95,
                    "response": "Your appointment has been confirmed! You will receive an SMS confirmation shortly. Is there anything else I can help you with?",
                    "entities": entities,
                    "context": "welcome",
                    "requires_input": True,
                    "action": "complete_booking"
                }
            elif any(pattern in text_lower for pattern in self._fallback_intents["confirm_no"]["patterns"]):
                return {
                    "intent": "cancel_booking",
                    "confidence": 0.9,
                    "response": "No problem, the booking has been cancelled. Would you like to start over or try a different service?",
                    "entities": {},
                    "context": "welcome",
                    "requires_input": True
                }
        
        # General intent matching
        best_match = None
        best_score = 0
        
        for intent_name, intent_data in self._fallback_intents.items():
            if intent_name == "fallback":
                continue
            
            for pattern in intent_data["patterns"]:
                if pattern in text_lower:
                    score = len(pattern) / len(text_lower) if text_lower else 0
                    if score > best_score:
                        best_score = score
                        best_match = intent_name
        
        if best_match:
            intent_data = self._fallback_intents[best_match]
            
            # Update entities if this intent sets any
            if "sets_entity" in intent_data:
                entities.update(intent_data["sets_entity"])
            
            responses = intent_data.get("responses", ["I understand. How can I help you?"])
            import random
            response = random.choice(responses)
            
            return {
                "intent": best_match,
                "confidence": min(0.9, best_score + 0.3),
                "response": response,
                "entities": entities,
                "context": intent_data.get("context", current_context),
                "requires_input": True
            }
        
        # Fallback response
        fallback = self._fallback_intents["fallback"]
        import random
        return {
            "intent": "fallback",
            "confidence": 0.0,
            "response": random.choice(fallback["responses"]),
            "entities": entities,
            "context": current_context,
            "requires_input": True
        }
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from text."""
        text = text.strip()
        
        # Remove common prefixes
        prefixes = ["my name is", "i am", "i'm", "call me", "this is", "it's", "name is"]
        text_lower = text.lower()
        
        for prefix in prefixes:
            if text_lower.startswith(prefix):
                name = text[len(prefix):].strip()
                # Capitalize properly
                return " ".join(word.capitalize() for word in name.split())
        
        # If no prefix, assume the whole input might be a name
        # Basic validation: 2-50 chars, mostly letters
        if 2 <= len(text) <= 50 and text.replace(" ", "").isalpha():
            return " ".join(word.capitalize() for word in text.split())
        
        return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        import re
        
        # Remove spaces and common words
        cleaned = text.lower()
        for word in ["my phone is", "phone number is", "number is", "call me on", "phone", "number"]:
            cleaned = cleaned.replace(word, "")
        
        cleaned = re.sub(r'[\s\-\(\)]', '', cleaned)
        
        # Match Kenyan phone patterns
        patterns = [
            r'(\+254\d{9})',
            r'(254\d{9})',
            r'(0[17]\d{8})',
            r'([17]\d{8})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned)
            if match:
                phone = match.group(1)
                # Normalize to +254 format
                if phone.startswith('0'):
                    return '+254' + phone[1:]
                elif phone.startswith('254'):
                    return '+' + phone
                elif not phone.startswith('+'):
                    return '+254' + phone
                return phone
        
        return None
    
    def get_conversation_state(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current conversation state information.
        
        Args:
            context: Current context
        
        Returns:
            State information for UI feedback
        """
        conv_context = context.get("conversation_context", "welcome")
        entities = context.get("entities", {})
        
        steps = {
            "welcome": {"step": 0, "label": "Start", "next": "Select a service"},
            "booking_service_selection": {"step": 1, "label": "Service Selection", "next": "Provide your name"},
            "booking_name": {"step": 2, "label": "Your Name", "next": "Provide phone number"},
            "booking_phone": {"step": 3, "label": "Phone Number", "next": "Select time slot"},
            "booking_time": {"step": 4, "label": "Time Slot", "next": "Confirm booking"},
            "booking_confirm": {"step": 5, "label": "Confirmation", "next": "Complete"},
            "booking_complete": {"step": 6, "label": "Complete", "next": None}
        }
        
        current_step = steps.get(conv_context, steps["welcome"])
        
        return {
            "current_context": conv_context,
            "step_number": current_step["step"],
            "step_label": current_step["label"],
            "next_action": current_step["next"],
            "total_steps": 6,
            "collected_info": {
                "service": entities.get("service_type"),
                "name": entities.get("user_name"),
                "phone": entities.get("phone_number"),
                "time_slot": entities.get("time_slot")
            }
        }


# Global service instance
dialogflow_service = DialogflowService()
