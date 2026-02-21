"""
Google Gemini API integration for natural language understanding.
Integrated with Rafiki copilot platform for government service navigation.

Features:
- Natural language understanding via Gemini AI
- PII detection and sanitization
- Bilingual (English/Kiswahili) support
- Secure input handling
- RAG integration for government knowledge queries
"""

import json
from typing import Dict, Any, Optional, List

# Try new google-genai package first, fall back to old google-generativeai
try:
    from google import genai
    from google.genai import types
    GENAI_NEW_API = True
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_NEW_API = False
    except ImportError:
        genai = None
        GENAI_NEW_API = False

from rafiki_settings import get_settings, GOVERNMENT_SERVICES, ASSISTANT_RESPONSES
from utils.logger import get_logger
from services.intent_service import intent_detector
from utils.encryption import get_pii_detector, PIIDetector

# RAG service for knowledge queries
try:
    from services.rag_service import ConstitutionRAG
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    ConstitutionRAG = None

logger = get_logger(__name__)


class GeminiService:
    """
    Service for integrating with Google Gemini API for NLU.
    Handles intent detection, entity extraction, and response generation.
    
    Security Features:
    - PII detection and masking before logging
    - Input sanitization
    - Secure handling of sensitive data
    """
    
    def __init__(self):
        """Initialize Gemini service with API configuration."""
        self.settings = get_settings()
        self._model = None
        self._client = None  # For new google-genai API
        self._chat = None
        self._initialized = False
        self._pii_detector: Optional[PIIDetector] = None
        self._rag_service = None
        
        # System context for the assistant
        self._system_context = self._build_system_context()
        
        # Initialize RAG service for knowledge queries
        try:
            if RAG_AVAILABLE:
                self._rag_service = ConstitutionRAG()
                # Load documents on startup
                self._rag_service.load_all_documents()
                logger.info("RAG service initialized for Gemini")
        except Exception as e:
            logger.warning(f"RAG service not available: {e}")
            self._rag_service = None
        
        # Initialize PII detector
        try:
            self._pii_detector = get_pii_detector()
            logger.info("PII detector initialized for Gemini service")
        except Exception as e:
            logger.warning(f"PII detector not available: {e}")
    
    def _sanitize_input(self, text: str) -> tuple[str, Dict[str, Any]]:
        """
        Sanitize input text by detecting PII.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Tuple of (original text, PII detection results)
        """
        pii_found = {}
        
        if self._pii_detector:
            pii_found = self._pii_detector.detect(text)
            
            if pii_found:
                # Log PII detection (masked) for security auditing
                logger.warning(
                    f"PII detected in input: {list(pii_found.keys())} - "
                    f"counts: {self._pii_detector.get_pii_summary(text)}"
                )
        
        return text, pii_found
    
    def _get_safe_log_text(self, text: str) -> str:
        """
        Get a safe version of text for logging (PII masked).
        
        Args:
            text: Text to mask
            
        Returns:
            Text with PII masked
        """
        if self._pii_detector:
            return self._pii_detector.mask(text)
        return text
    
    def _is_knowledge_query(self, message: str) -> bool:
        """
        Check if a message is a knowledge/information query that should use RAG.
        
        Args:
            message: User's message
            
        Returns:
            True if this is a knowledge query
        """
        knowledge_patterns = [
            'constitution', 'katiba', 'law', 'sheria',
            'what does', 'what is', 'how do i', 'how can i',
            'tell me about', 'explain', 'niambie',
            'citizenship', 'uraia', 'rights', 'haki',
            'kra', 'itax', 'tax', 'nil returns', 'pin',
            'ecitizen', 'passport', 'id card', 'kitambulisho',
            'license', 'permit', 'registration', 'usajili',
            'documents', 'requirements', 'mahitaji',
            'article', 'chapter', 'section', 'sehemu',
            'government', 'serikali', 'service', 'huduma'
        ]
        
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in knowledge_patterns)
    
    def _get_rag_context(self, query: str, language: str = 'en') -> Dict[str, Any]:
        """
        Get relevant context from RAG service for knowledge queries.
        
        Args:
            query: User's question
            language: Language for citations
            
        Returns:
            Dictionary with context, citations, and spoken citations
        """
        if not self._rag_service:
            logger.warning("RAG service not available - returning empty context")
            return {'context': '', 'citations': [], 'spoken_citations': [], 'rag_available': False}
        
        try:
            logger.info(f"[RAG] Querying for: '{query[:100]}...' in language: {language}")
            
            # Query RAG with citations
            results = self._rag_service.query_with_citations(
                query_text=query,
                language=language,
                top_k=3
            )
            
            citation_count = len(results.get('citations', []))
            context_length = len(results.get('context', ''))
            
            logger.info(f"[RAG] Query successful - {citation_count} citations, {context_length} chars context")
            
            if citation_count == 0:
                logger.warning(f"[RAG] No citations found for query: '{query[:50]}...'")
            
            results['rag_available'] = True
            return results
            
        except Exception as e:
            logger.error(f"[RAG] Query FAILED for '{query[:50]}...': {type(e).__name__}: {e}", exc_info=True)
            return {
                'context': '', 
                'citations': [], 
                'spoken_citations': [], 
                'rag_available': True,
                'rag_error': str(e)
            }
    
    def _build_system_context(self, language: str = 'en') -> str:
        """Build the system context prompt for Gemini using Rafiki copilot guidelines."""
        services_info = "\n".join([
            f"- {key}: {info['name']} - {info['description']}"
            for key, info in GOVERNMENT_SERVICES.items()
        ])
        
        if language == 'sw':
            # Kiswahili system context - Rafiki copilot
            return f"""Jina lako ni Rafiki, msaidizi wa sauti-kwanza ambaye husaidia Wakenya—haswa wasioziona vizuri—kufikia huduma za serikali kupitia mazungumzo ya asili na yenye lugha mbili. Wewe ni rafiki mwenye subira, unasikitika, na unajifanya kuwa mwongozo wa inobly wa serikali kwa kila hatua.

# Tabia ya Rafiki
- **Jina:** Rafiki (Kiswahili kwa "rafiki")
- **Sauti:** Moto, subira, sauti ya Kiingereza ya Kenya
- **Lugha:** Kiingereza na Kiswahili, na code-switching bila matatizo
- **Haiba:** Rafiki msaidizi, mwongozo wa huduma za serikali, mchampioni wa ufikiaji

# Madhumuni na Uwezo
- **Urambazaji wa serikali:** Ongoza watumiaji kupitia KRA Nil Returns na mtiririko wa kawaida wa serikali.
- **Msaada wa lugha mbili:** Kumbuka lugha na ainishikie kile kinachohitajika kwa watumiaji - Kiingereza, Kiswahili, au mchanganyiko.
- **Ufikiaji kwanza:** Toa maelekezo wazi, fupi, yenye akili ya screen-reader na rudia au polepole kwa ombi.
- **Msaada wa hatua kwa hatua:** Gawanya michakato changamano katika hatua rahisi, zinazoezekan, na checkpoints na uthibitisho.
- **Urambazaji wa ushuhuda:** Tafsiri kusaidia kwa mazungumzo au kufungua tovuti rasmi, kisha baki kupatikana kusaidia.
- **Chaguo la uthibitisho:** Tafsiri ujumbe wa SMS kwa hatua muhimu kupitia Africa's Talking.

# Mtindo wa Mazungumzo na Sheria
- **Saluti:** "Habari! Mimi ni Rafiki, msaidizi wako wa huduma za serikali. Niaje nawe leo?"
- **Nia mapema:** Kumbuka lengo kama ni kufile nil returns, msaada wa iTax, au uponyaji wa KRA PIN.
- **Ridhaa kabla ya kuelekeza:** "Ungependa kunitaka hapa, au kufungua tovuti ya KRA moja kwa moja?"
- **Uwazi kwanza:** Fikiria mtumiaji anaweza kusikia; hifadhi maelekezo mafupi, yenye utaratibu, na bila neno lisilo na maelezo.
- **Kuangalia kuelewa:** "Je hilo lilieleza vizuri? Je nirudie kitu chochote?"
- **Nita za ufikiaji:** "Ninaweza kurudia hiyo polepole," "Ungependa ningie hiyo?" "Ijifanye hii katika hatua ndogo."
- **Kamwe:** Fikiria mtumiaji anaweza kuona skrini, haraka hatua, tumia neno lisilo na maelezo, au ruka kutafsiri chaguo mbadala.

# Mifano ya Mtiririko

## Mtiririko wa KRA nil returns
1. **Kumbuka nia:** "Nataka kufile nil returns" au "I need to file nil returns."
2. **Eleza mahitaji:** 
   - "Kufile nil returns, utakuwa na KRA PIN na ufikiaji wa iTax. Je una hii tayari?"
3. **Tafsiri chaguo la urambazaji:** 
   - "Ninaweza kukuongeza hatua kwa hatua hapa, au kufungua iTax. Unapendelea nini?"
4. **Ongoza mtiririko:**
   - **Kwa mazungumzo:** Toa hatua za namba, za msamiati, na checkpoints na ujumbe mfupi.
   - **Nje:** "Ninafungua iTax. Niko hapa kusaidia ukikamatwa."
5. **Thibitisha ukamilisho:** "Ungependa nikatume ujumbe wa SMS wa uthibitisho?"

## Maswali ya ujumbe
- **Mfano:** "Weka mabarizaji gani najisikilia kwa leseni ya biashara?"
- **Jibu:** Tumia RAG-lite kupata kumbukumbu uliyokiwa na kujibu wazi na kutafsiri hatua kwa kina.

# Kurudisha Mfalme
Tunajua kuwa kila mtumiaji ana uhitaji tofauti:
- **Tulio:** Tuatakuza sauti nzuri, Kiswahili asili (si rasmi kupita), Kiingereza kilichobanwa.
- **Kasi:** Tumia kasi ya kawaida, pause kwa asili, na msomeko wa akili.
- **Kutsanzia:** Kumbuka mtumiaji anaweza kusikia tu; kuamua kwa wazi na kuweka chaguo la urambazaji.

Huduma zinazopatikana:
{services_info}

Nyakati zinazopatikana: Asubuhi (8:00 AM - 12:00 PM) au Alasiri (2:00 PM - 5:00 PM)

Zungumza kwa subira na upendo. Rudia habari kama inahitajika. Tia moyo mtumiaji."""
        else:
            # English system context - Rafiki copilot platform prompt
            return f"""You are Rafiki, a voice-first AI assistant that helps Kenyan citizens—especially visually impaired users—access government services through natural, bilingual conversation. You guide people step by step, keep the experience human, and prioritize accessibility and dignity at every turn.

# Core Identity
- **Name:** Rafiki (Swahili for "friend")
- **Voice:** Warm, patient, human-like Kenyan accent
- **Languages:** English and Kiswahili, with natural code-switching
- **Personality:** Helpful friend, government service guide, accessibility champion

# Objectives and Capabilities
- **Government navigation:** Guide users through KRA Nil Returns and common government workflows.
- **Bilingual support:** Detect language and mirror the user's preference in English, Kiswahili, or mixed.
- **Accessibility first:** Give clear, concise, screen-reader-friendly instructions and repeat or slow down on request.
- **Step-by-step guidance:** Break complex processes into simple, actionable steps with checkpoints and confirmations.
- **Consentful navigation:** Offer to guide in-chat or open official sites, then stay available to help.
- **Confirmation options:** Offer SMS confirmations for critical steps via Africa's Talking.

# Conversation Style and Rules
- **Greeting:** "Habari! I'm Rafiki, your government services assistant. How can I help you today?"
- **Intent early:** Detect goals such as filing nil returns, iTax help, or KRA PIN recovery.
- **Consent before redirect:** "Would you like me to guide you here, or open the KRA website directly?"
- **Clarity first:** Assume the user may be listening; keep instructions short, ordered, and jargon-free.
- **Check understanding:** "Did that make sense? Should I repeat anything?"
- **Accessibility prompts:** "I can repeat that more slowly," "Would you like me to spell that out?" "Let me break this into smaller steps."
- **Never:** Assume the user can see the screen, rush steps, use unexplained jargon, or skip offering alternative formats.

# Example Workflows

## KRA Nil Returns Flow
1. **Detect intent:** "Nataka kufile nil returns" or "I need to file nil returns."
2. **Explain requirements:**
   - "To file nil returns, you'll need your KRA PIN and access to iTax. Do you have these ready?"
3. **Offer navigation options:**
   - "I can guide you step-by-step here, or open the iTax website. Which would you prefer?"
4. **Guide process:**
   - **In-chat:** Provide numbered, verbal steps with short sentences and checkpoints.
   - **External:** "I'm opening iTax. I'll stay here to help if you get stuck."
5. **Confirm completion:** "Would you like me to send you an SMS confirmation?"

## Knowledge Queries
- **Example:** "What documents do I need for a business permit?"
- **Response:** Use RAG-lite to fetch from the curated knowledge base, then answer clearly and offer detailed steps if desired.

# Technical Orchestration
- **Frontend (React):** Voice input capture, accessible UI with ARIA labels and keyboard nav, high contrast, avatar lip-sync.
- **Backend (Django/FastAPI):** Session management, intent routing, agent orchestration, API integrations, workflow logic.
- **AI (Gemini):** Natural language understanding, reasoning, intent and language detection, and RAG for knowledge retrieval.
- **Voice (ElevenLabs):** Text-to-speech with warm Kenyan-accent voices to avoid robotic tone; ensure clear pacing and pronunciation in EN/SW.
- **Messaging (Africa's Talking):** SMS confirmations and OTP when relevant.
- **Avatar:** Lip-sync to delivered audio for engagement; avoid distracting motions during critical instructions.
- **Deployment:** Containerized (Docker) on a managed host with HTTPS and environment-based secrets.

# Agents and Flow Control
- **Intent & language agent (Gemini):** Detect user goal and language; set conversation state and tone.
- **Knowledge agent (RAG-lite):** Retrieve structured answers from curated PDFs/text; cite source name verbally when helpful.
- **Navigation agent:** Ask for consent; choose in-chat guidance or open official sites; monitor for confusion and offer help.
- **Speech orchestration:** Convert final response text to natural audio via ElevenLabs; tune speed, pauses, and emphasis.

# Language Handling
- **Detection:** Auto-detect EN/SW and mirror the user's style; code-switch smoothly when they do.
- **Tone:** Natural Kiswahili (not overly formal); friendly, clear English.
- **Examples:** "Sawa, let me explain the PIN recovery process…" "Twende hatua kwa hatua."

# Error Handling and Resilience
- **User confusion:** "Let me try explaining that differently," "Would it help if I went back a step?" "Take your time."
- **Technical issues:** "I'm having a small technical issue. Let me try again," and prompt for a brief repeat if needed.
- **Safety and dignity:** Keep users oriented, never overwhelm; summarize progress and next steps.

# Tone Guide
- **Warm:** "Karibu! I'm so glad you reached out."
- **Patient:** "No worries—let's go through this step by step."
- **Encouraging:** "You're doing great—just one more step."
- **Clear:** "Here's what we'll do: First… Then… Finally…"

# Success Criteria
- **Accessible experience:** Users can complete one end-to-end government service via voice-only guidance.
- **Human-like audio:** ElevenLabs produces clear, Kenyan-accent speech with natural pacing and emphasis.
- **Accurate guidance:** Gemini-driven reasoning yields correct, context-aware steps and answers.
- **Trust and consent:** Users feel supported, not rushed; navigation choices are explicit and respected.
- **Scalable design:** New government workflows can be added with minimal changes to orchestration.

# Implementation Notes
- **Structure responses:** Prefer numbered steps and short sentences; insert brief pauses in speech (e.g., commas) to aid comprehension.
- **Confirm after each chunk:** Ask if the user wants repetition, slower delivery, or SMS summary.
- **Optimize audio:** Adjust speech rate, add emphasis to key terms (e.g., "KRA PIN"), and spell out tricky items on request.
- **Persist context:** Maintain session state (intent, language, progress) across turns; resume gracefully after interruptions.
- **Log outcomes:** Record completion markers and user confirmations to improve flows while respecting privacy norms.

Available services:
{services_info}

Available time slots: Morning (8:00 AM - 12:00 PM) or Afternoon (2:00 PM - 5:00 PM)

For booking requests, collect: service type, user name, phone number, preferred time slot, and date.

Always respond in a way that's easy to understand when spoken aloud. Sound like a caring friend, not a robot."""
    
    def initialize(self):
        """
        Initialize the Gemini API client.

        Returns an object that supports both truthy checks (synchronous usage) and awaiting (async usage) so tests can
        call `service.initialize()` or `await service.initialize()`.
        """
        def _sync_init():
            try:
                # Allow initialization even when GEMINI_API_KEY is not set (so tests can mock the model)
                if not self.settings.GEMINI_API_KEY:
                    logger.warning("Gemini API key not configured; attempting initialization (may be mocked)")

                if GENAI_NEW_API:
                    # New google-genai package (2024+)
                    client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
                    self._client = client
                    self._model = self.settings.GEMINI_MODEL
                    self._initialized = True
                    logger.info("Gemini service initialized with new API")
                else:
                    # Old google-generativeai package
                    genai.configure(api_key=self.settings.GEMINI_API_KEY)

                    # Configure the model
                    generation_config = genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.9,
                        top_k=40,
                        max_output_tokens=2048,
                    )

                    safety_settings = [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    ]

                    # Try with system_instruction first (newer API), fall back to without
                    try:
                        self._model = genai.GenerativeModel(
                            model_name=self.settings.GEMINI_MODEL,
                            generation_config=generation_config,
                            safety_settings=safety_settings,
                            system_instruction=self._system_context
                        )
                    except TypeError:
                        # Older API version doesn't support system_instruction
                        self._model = genai.GenerativeModel(
                            model_name=self.settings.GEMINI_MODEL,
                            generation_config=generation_config,
                            safety_settings=safety_settings
                        )
                        logger.info("Using Gemini without system_instruction (older API)")

                    self._initialized = True
                    logger.info("Gemini service initialized with legacy API")
                
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Gemini service: {e}")
                self._initialized = False
                return False

        async def _async_init():
            return _sync_init()

        class _InitResult:
            def __bool__(self):
                # allow synchronous truth checks to perform initialization
                return _sync_init()

            def __await__(self):
                return _async_init().__await__()

        return _InitResult()
    
    async def process_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response using Rafiki copilot guidelines.
        
        Args:
            user_message: The user's input message
            conversation_history: Previous conversation turns
            context: Additional context (booking state, user preferences, session_context)
            language: Response language ('en' for English, 'sw' for Kiswahili)
        
        Returns:
            Dictionary containing response text, intent, entities, workflow, and suggested actions
        """
        if not self._initialized:
            if not self.initialize():
                error_msg = "Samahani, kuna tatizo. Jaribu tena." if language == 'sw' else ASSISTANT_RESPONSES["error_generic"]
                return {
                    "text": error_msg,
                    "intent": "error",
                    "entities": {},
                    "suggested_actions": ["Try again", "Say 'help' for assistance"]
                }
        
        try:
            # Sanitize input and detect PII
            sanitized_message, pii_detected = self._sanitize_input(user_message)
            
            # Detect language from message if not explicitly provided
            detected_language = intent_detector._detect_language(user_message)
            language = detected_language if detected_language != 'en' or language == 'en' else language
            
            # Detect intent and extract entities
            intent_analysis = intent_detector.detect(
                user_message,
                conversation_history=conversation_history,
                session_context=context
            )
            
            # Check if this is a knowledge query and get RAG context
            rag_context = {}
            if self._is_knowledge_query(user_message):
                rag_context = self._get_rag_context(user_message, language)
                logger.info(f"Knowledge query detected, RAG context retrieved")
            
            # Update system context based on detected language
            self._system_context = self._build_system_context(language)
            
            # Build the prompt with enhanced context (including RAG)
            prompt = self._build_prompt(
                user_message,
                conversation_history,
                context,
                language,
                intent_analysis,
                rag_context=rag_context
            )
            
            # Generate response from Gemini
            response = await self._generate_response(prompt)
            
            # Parse the response
            parsed_response = self._parse_response(response, user_message)
            
            # Merge with intent analysis for richer context
            parsed_response['detected_intent'] = intent_analysis['intent']
            parsed_response['workflow'] = intent_analysis['workflow']
            parsed_response['language_detected'] = intent_analysis['language']
            parsed_response['entities'] = {**parsed_response.get('entities', {}), **intent_analysis['entities']}
            parsed_response['confidence'] = intent_analysis['confidence']
            parsed_response['pii_detected'] = list(pii_detected.keys()) if pii_detected else []
            
            # Add RAG citations if available
            if rag_context and rag_context.get('citations'):
                parsed_response['sources'] = [
                    c.get('citation', 'Unknown') for c in rag_context['citations']
                ]
                parsed_response['verified'] = rag_context.get('verified', False)
            
            # Log with PII masked
            safe_log_msg = self._get_safe_log_text(user_message)
            logger.info(
                f"Processed message - Intent: {intent_analysis['intent']}, "
                f"Confidence: {intent_analysis['confidence']:.2f}, Language: {language}, "
                f"RAG used: {bool(rag_context and rag_context.get('context'))}, "
                f"Message: {safe_log_msg[:50]}..."
            )
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "text": ASSISTANT_RESPONSES["error_generic"],
                "intent": "error",
                "entities": {},
                "suggested_actions": ["Try again", "Say 'help' for assistance"]
            }
    
    def _build_prompt(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
        language: str = 'en',
        intent_analysis: Optional[Dict[str, Any]] = None,
        rag_context: Optional[Dict[str, Any]] = None
    ):
        """Build the full prompt including history, context, RAG knowledge, and detected intent.

        This returns an object that is both string-coercible and awaitable so tests can `await service._build_prompt(...)`
        while internal code can pass it directly into the generator (which will cast to str).
        """
        prompt_parts = []
        
        # Add language instruction
        if language == 'sw':
            prompt_parts.append("IMPORTANT: Respond in Kiswahili (Swahili) language only. Use natural, friendly Kiswahili.")
        else:
            prompt_parts.append("IMPORTANT: Respond in English language only. Use clear, friendly English with a warm Kenyan tone.")
        
        # Add RAG context for knowledge queries (PRIORITY)
        if rag_context and rag_context.get('context'):
            prompt_parts.append("=" * 50)
            prompt_parts.append("IMPORTANT: Use the following VERIFIED KNOWLEDGE from official Kenya government documents to answer the user's question:")
            prompt_parts.append(rag_context['context'])
            
            # Add citations
            if rag_context.get('citations'):
                citations_text = "\n".join([
                    f"- {c.get('citation', 'Unknown source')}" 
                    for c in rag_context['citations'][:3]
                ])
                prompt_parts.append(f"\nSources:\n{citations_text}")
            
            # Add spoken citation instruction
            if rag_context.get('spoken_citations'):
                prompt_parts.append(f"\nWhen answering, mention the source by saying: \"{rag_context['spoken_citations'][0]}\"")
            
            prompt_parts.append("=" * 50)
            prompt_parts.append("Answer the question based on the above knowledge. Be accurate and cite the source.")
        
        # Add intent context if available
        if intent_analysis:
            intent = intent_analysis.get('intent', 'unknown')
            workflow = intent_analysis.get('workflow')
            entities = intent_analysis.get('entities', {})
            
            prompt_parts.append(f"Detected Intent: {intent}")
            
            if entities:
                entities_info = json.dumps(entities, indent=2)
                prompt_parts.append(f"Extracted Information:\n{entities_info}")
            
            if workflow:
                workflow_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(workflow.get('steps', []))])
                prompt_parts.append(f"Guidance Workflow ({workflow['name']}):\n{workflow_steps}")
        
        # Add context if available
        if context:
            if context.get("booking_state"):
                booking_info = json.dumps(context["booking_state"], indent=2)
                prompt_parts.append(f"Current booking state:\n{booking_info}")
            
            if context.get("last_intent"):
                prompt_parts.append(f"Previous intent: {context['last_intent']}")
            
            if context.get("user_progress"):
                prompt_parts.append(f"User progress: {context['user_progress']}")
        
        # Add conversation history
        if conversation_history:
            history_text = "\n".join([
                f"{'User' if turn['role'] == 'user' else 'Assistant'}: {turn['content']}"
                for turn in conversation_history[-6:]  # Last 6 turns
            ])
            prompt_parts.append(f"Recent conversation:\n{history_text}")
        
        # Add current message
        prompt_parts.append(f"User: {user_message}")
        
        # Add response format instruction
        response_lang = "Kiswahili" if language == 'sw' else "English"
        prompt_parts.append("""
Please respond with a JSON object containing:
{
    "response_text": "Your natural language response in """ + response_lang + """ to speak to the user. Be warm, patient, and accessible. Use short sentences and natural pauses.",
    "intent": "detected intent (kra_nil_returns/kra_pin_recovery/kra_pin_generation/itax_help/service_inquiry/book_appointment/greeting/help/unknown)",
    "entities": {
        "service_type": "nil_returns/pin_recovery/pin_generation/etc or null",
        "user_name": "extracted name or null",
        "phone_number": "extracted phone or null",
        "national_id": "extracted national ID or null",
        "kra_pin": "extracted KRA PIN or null",
        "email": "extracted email or null",
        "time_slot": "morning/afternoon or null",
        "date": "extracted date or null",
        "confirmation": "yes/no or null"
    },
    "workflow_step": "current step in workflow if applicable",
    "next_step": "next action to guide user through",
    "requires_input": true/false,
    "suggested_actions": ["action1", "action2"]
}

CRITICAL GUIDANCE:
- For KRA Nil Returns: Ask if they have KRA PIN, explain process, guide to iTax
- For KRA PIN Recovery: Verify identity, explain recovery options, guide through process
- For KRA PIN Generation: Explain eligibility, collect national ID, guide registration
- For iTax Help: Provide step-by-step guidance, never ask for passwords
- Always prioritize accessibility: clear language, numbered steps, confirmation checks
- Offer SMS confirmations for all important transactions
- Be conversational and warm - sound like a helpful Kenyan friend
- If user is confused, simplify, slow down, break into smaller steps
""")
        
        prompt_text = "\n\n".join(prompt_parts)

        class _Prompt:
            def __str__(self_non):
                return prompt_text

            def __await__(self_non):
                async def _a():
                    return prompt_text
                return _a().__await__()

        return _Prompt()
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Gemini."""
        try:
            # Ensure service is initialized (support lazy init when tests call this directly)
            if not self._initialized:
                init_res = self.initialize()
                # Force synchronous initialization attempt
                if not bool(init_res):
                    error_msg = "Gemini service not configured"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            prompt_text = str(prompt)
            
            if GENAI_NEW_API:
                # New google-genai API
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt_text,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        top_p=0.9,
                        top_k=40,
                        max_output_tokens=2048,
                    )
                )
                return response.text
            else:
                # Legacy google-generativeai API
                response = self._model.generate_content(prompt_text)
                return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise
    
    def _parse_response(self, response: str, original_message: str) -> Dict[str, Any]:
        """Parse Gemini response into structured format."""
        try:
            # Strip markdown code blocks if present
            clean_response = response
            if '```json' in clean_response:
                clean_response = clean_response.replace('```json', '').replace('```', '')
            elif '```' in clean_response:
                clean_response = clean_response.replace('```', '')
            
            clean_response = clean_response.strip()
            
            # Try to extract JSON from response
            json_start = clean_response.find('{')
            json_end = clean_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = clean_response[json_start:json_end]
                parsed = json.loads(json_str)
                
                return {
                    "text": parsed.get("response_text", clean_response),
                    "intent": parsed.get("intent", "unknown"),
                    "entities": parsed.get("entities", {}),
                    "automation": parsed.get("automation", {"action": "none"}),
                    "requires_input": parsed.get("requires_input", False),
                    "suggested_actions": parsed.get("suggested_actions", [])
                }
            
            # Fallback: return raw response with basic intent detection
            intent = self._detect_basic_intent(original_message)
            return {
                "text": clean_response,
                "intent": intent,
                "entities": {},
                "automation": {"action": "none"},
                "requires_input": True,
                "suggested_actions": []
            }
            
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from Gemini response")
            # Clean the response before returning
            clean_response = response
            if '```json' in clean_response:
                clean_response = clean_response.replace('```json', '').replace('```', '')
            elif '```' in clean_response:
                clean_response = clean_response.replace('```', '')
            clean_response = clean_response.strip()
            
            return {
                "text": clean_response,
                "intent": self._detect_basic_intent(original_message),
                "entities": {},
                "automation": {"action": "none"},
                "requires_input": True,
                "suggested_actions": []
            }
    
    def _detect_basic_intent(self, message: str) -> str:
        """Fallback basic intent detection."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return 'greeting'
        elif any(word in message_lower for word in ['book', 'appointment', 'schedule']):
            return 'book_appointment'
        elif any(word in message_lower for word in ['passport', 'id', 'license', 'conduct']):
            return 'service_info'
        elif any(word in message_lower for word in ['help', 'assist', 'support']):
            return 'help'
        elif any(word in message_lower for word in ['yes', 'confirm', 'okay', 'sure']):
            return 'confirm'
        elif any(word in message_lower for word in ['no', 'cancel', 'stop']):
            return 'cancel'
        else:
            return 'unknown'
    
    def get_service_info(self, service_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a government service (synchronous for tests).
        """
        if service_type in GOVERNMENT_SERVICES:
            service = GOVERNMENT_SERVICES[service_type]
            
            # Generate a natural language description
            requirements_text = ", ".join(service["requirements"])
            
            response_text = (
                f"For {service['name']}, you will need to visit the {service['department']}. "
                f"The required documents are: {requirements_text}. "
                f"Available time slots are morning from 8 AM to 12 PM, or afternoon from 2 PM to 5 PM. "
                f"Would you like me to book an appointment for this service?"
            )
            
            return {
                "text": response_text,
                "service_info": service,
                "intent": "service_info",
                "requires_input": True,
                "suggested_actions": ["Book appointment", "Learn about another service", "Go back"]
            }
        else:
            return {
                "error": "Service not found",
                "text": f"I don't have information about that service. Available services are: "
                       f"Passport, National ID, Driving License, and Certificate of Good Conduct.",
                "intent": "error",
                "requires_input": True,
                "suggested_actions": list(GOVERNMENT_SERVICES.keys())
            }


# Global service instance
gemini_service = GeminiService()
