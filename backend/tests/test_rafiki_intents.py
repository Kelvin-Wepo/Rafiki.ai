"""
Tests for Rafiki voice assistant intent detection and routing.

Tests cover:
1. list_supported_agencies - User asks for available agencies
2. book_appointment - User wants to book an appointment
3. manage_appointment - User wants to reschedule/cancel
4. check_appointment_status - User checks booking status
5. get_huduma_directions - User asks for Huduma Centre directions
6. constitutional_qa_rag - User asks constitutional question
7. FAILURE: unsupported_agency - User asks for non-existent agency
8. FAILURE: rag_retrieval_failure - RAG fails to retrieve
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.intent_service import IntentDetector
from services.dialogflow_service import DialogflowService
from rafiki_settings import SUPPORTED_AGENCIES, ASSISTANT_RESPONSES


class TestIntentDetection:
    """Test suite for intent detection."""
    
    def setup_method(self):
        """Setup for each test."""
        self.intent_detector = IntentDetector()
        self.dialogflow_service = DialogflowService()
    
    # === TEST 1: list_supported_agencies ===
    def test_list_supported_agencies_intent(self):
        """Test that asking for agencies returns list_supported_agencies intent."""
        test_messages = [
            "What agencies do you support?",
            "Which agencies are available?",
            "List the supported agencies",
            "What services can you help with?",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_LIST_AGENCIES, \
                f"Expected list_supported_agencies intent for: '{message}', got: {result['intent']}"
            assert result["confidence"] >= 0.9, f"Low confidence for: '{message}'"
    
    # === TEST 2: book_appointment ===
    def test_book_appointment_intent(self):
        """Test that booking requests trigger book_appointment intent."""
        test_messages = [
            "I want to book an appointment",
            "Schedule an appointment for me",
            "Can I book a passport appointment?",
            "Reserve a slot for driving license",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_BOOKING, \
                f"Expected book_appointment intent for: '{message}', got: {result['intent']}"
    
    # === TEST 3: manage_appointment ===
    def test_manage_appointment_intent(self):
        """Test that management requests trigger manage_appointment intent."""
        test_messages = [
            "I want to reschedule my appointment",
            "Cancel my appointment",
            "Change my appointment date",
            "Postpone my booking",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_MANAGE_APPOINTMENT, \
                f"Expected manage_appointment intent for: '{message}', got: {result['intent']}"
    
    # === TEST 4: check_appointment_status ===
    def test_check_appointment_status_intent(self):
        """Test that status queries trigger check_appointment_status intent."""
        test_messages = [
            "Check my appointment status",
            "What is my booking status?",
            "Is my appointment confirmed?",
            "When is my appointment?",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_CHECK_APPOINTMENT_STATUS, \
                f"Expected check_appointment_status intent for: '{message}', got: {result['intent']}"
    
    # === TEST 5: get_huduma_directions ===
    def test_huduma_directions_intent(self):
        """Test that Huduma Centre queries trigger huduma_centre intent."""
        test_messages = [
            "Where is the nearest Huduma Centre?",
            "Directions to Huduma Centre",
            "Find Huduma Centre near me",
            "Kituo cha huduma",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_HUDUMA_CENTRE, \
                f"Expected huduma_centre intent for: '{message}', got: {result['intent']}"
    
    # === TEST 6: constitutional_qa_rag ===
    def test_constitutional_qa_intent(self):
        """Test that constitutional questions trigger constitutional_qa_rag intent."""
        test_messages = [
            "What is the bill of rights?",
            "Tell me about the constitution",
            "What does Article 27 say?",
            "Katiba ya Kenya",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_CONSTITUTIONAL_QA, \
                f"Expected constitutional_qa_rag intent for: '{message}', got: {result['intent']}"
    
    # === TEST 7: FAILURE - unsupported_agency ===
    def test_unsupported_agency_response(self):
        """Test that unsupported agency gets appropriate response."""
        # Verify our supported agencies constant exists and has 9 agencies
        assert len(SUPPORTED_AGENCIES) == 9, \
            f"Expected 9 supported agencies, got: {len(SUPPORTED_AGENCIES)}"
        
        # Required agencies
        required_agencies = ['ntsa', 'kra', 'nrb', 'dcrs', 'brs', 'dci', 'cpb', 'moh', 'county']
        for agency in required_agencies:
            assert agency in SUPPORTED_AGENCIES, f"Missing required agency: {agency}"
        
        # Check unsupported agency message exists
        assert "unsupported_agency" in ASSISTANT_RESPONSES, \
            "Missing 'unsupported_agency' in ASSISTANT_RESPONSES"
        
        # Verify the message lists all agencies
        unsupported_msg = ASSISTANT_RESPONSES["unsupported_agency"]
        for agency in ['NTSA', 'KRA', 'NRB', 'DCRS', 'BRS', 'DCI']:
            assert agency in unsupported_msg, f"Agency {agency} not in unsupported message"
    
    # === TEST 8: FAILURE - RAG retrieval failure ===
    def test_rag_fallback_response_exists(self):
        """Test that RAG fallback response exists for retrieval failures."""
        assert "rag_fallback" in ASSISTANT_RESPONSES, \
            "Missing 'rag_fallback' in ASSISTANT_RESPONSES"
        
        fallback_msg = ASSISTANT_RESPONSES["rag_fallback"]
        assert "unable to retrieve" in fallback_msg.lower() or "can't retrieve" in fallback_msg.lower(), \
            f"RAG fallback message doesn't indicate retrieval failure: {fallback_msg}"


class TestAgencyValidation:
    """Test agency definitions and validation."""
    
    def test_all_required_agencies_exist(self):
        """Verify all 9 required agencies are defined."""
        required = {
            'ntsa': 'National Transport and Safety Authority',
            'kra': 'Kenya Revenue Authority', 
            'nrb': 'National Registration Bureau',
            'dcrs': 'Department of Civil Registration Services',
            'brs': 'Business Registration Service',
            'dci': 'Directorate of Criminal Investigations',
            'cpb': 'Counsellors and Psychologists Board',
            'moh': 'Ministry of Health',
            'county': 'County'
        }
        
        for key, name_part in required.items():
            assert key in SUPPORTED_AGENCIES, f"Missing agency: {key}"
            agency = SUPPORTED_AGENCIES[key]
            assert 'name' in agency, f"Agency {key} missing 'name' field"
            assert 'full_name' in agency, f"Agency {key} missing 'full_name' field"
            assert 'services' in agency, f"Agency {key} missing 'services' field"
    
    def test_greeting_includes_all_agencies(self):
        """Verify greeting message lists all agencies."""
        greeting = ASSISTANT_RESPONSES["greeting"]["default"]
        
        # Check agency mentions
        assert "NTSA" in greeting, "NTSA not in greeting"
        assert "KRA" in greeting, "KRA not in greeting"
        assert "NRB" in greeting or "National Registration Bureau" in greeting, "NRB not in greeting"
        assert "DCRS" in greeting or "Civil Registration" in greeting, "DCRS not in greeting"
        assert "BRS" in greeting or "Business Registration" in greeting, "BRS not in greeting"
        assert "DCI" in greeting or "Criminal Investigations" in greeting, "DCI not in greeting"
        assert "Counsellors" in greeting or "Psychologists" in greeting, "CPB not in greeting"
        assert "Ministry of Health" in greeting or "Health" in greeting, "MOH not in greeting"
        assert "County" in greeting, "County services not in greeting"


class TestDialogflowFallback:
    """Test Dialogflow fallback intent matching."""
    
    def setup_method(self):
        """Setup for each test."""
        self.dialogflow = DialogflowService()
    
    def test_fallback_intents_include_required_intents(self):
        """Verify fallback intents include all required intents."""
        fallback_intents = self.dialogflow._fallback_intents
        
        required_intents = [
            'greeting',
            'book_appointment',
            'manage_appointment',
            'check_appointment_status',
            'list_agencies',
            'constitutional_qa',
            'feedback',
            'emergency',
            'corruption_report',
            'huduma_centre',
            'help'
        ]
        
        for intent in required_intents:
            assert intent in fallback_intents, f"Missing fallback intent: {intent}"


class TestEmergencyAndReporting:
    """Test emergency and reporting intents."""
    
    def setup_method(self):
        """Setup for each test."""
        self.intent_detector = IntentDetector()
    
    def test_emergency_intent(self):
        """Test emergency detection has highest priority."""
        test_messages = [
            "Emergency! I need help",
            "Call the police",
            "There's a fire",
            "I need an ambulance",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_EMERGENCY_REPORT, \
                f"Expected emergency_report intent for: '{message}', got: {result['intent']}"
            # Emergency should have highest confidence
            assert result["confidence"] >= 0.95
    
    def test_corruption_report_intent(self):
        """Test corruption reporting detection."""
        test_messages = [
            "I want to report corruption",
            "Someone asked for a bribe",
            "Report ufisadi",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_CORRUPTION_REPORT, \
                f"Expected corruption_report intent for: '{message}', got: {result['intent']}"
    
    def test_feedback_intent(self):
        """Test anonymous feedback detection."""
        test_messages = [
            "I want to give feedback",
            "I have a suggestion",
            "I want to complain about service",
        ]
        
        for message in test_messages:
            result = self.intent_detector.detect(message)
            assert result["intent"] == IntentDetector.INTENT_FEEDBACK, \
                f"Expected feedback intent for: '{message}', got: {result['intent']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
