"""
Language detection and code-switching support for Rafiki platform.
Handles automatic language detection and bilingual response generation.
"""

import re
from typing import Dict, Tuple, Optional, List
from utils.logger import get_logger

logger = get_logger(__name__)


class LanguageDetector:
    """
    Detects user language and supports code-switching between English and Kiswahili.
    """
    
    # Kiswahili vocabulary for reliable detection
    KISWAHILI_VOCABULARY = {
        'habari', 'asante', 'karibu', 'pole', 'sawa', 'ndiyo', 'hapana',
        'tafadhali', 'rafiki', 'msaada', 'tupo', 'sana', 'kwa', 'na', 'ni',
        'kupata', 'kusaidia', 'kufanya', 'kufikia', 'kuenda', 'kujibu',
        'kufungua', 'kuandika', 'kuanguka', 'kufa', 'kutegemea',
        'mtu', 'watu', 'kitu', 'vitu', 'sehemu', 'mahali',
        'asubuhi', 'alasiri', 'jioni', 'usiku', 'siku', 'wiki', 'mwezi',
        'mwaka', 'muda', 'wakati', 'saa', 'dakika', 'sekunde',
        'namba', 'idadi', 'kila', 'moja', 'mbili', 'tatu', 'nne',
        'kra', 'pin', 'itax', 'serikali', 'huduma', 'fomu', 'karatasi',
        'hata', 'kama', 'lakini', 'ingawa', 'wakati', 'baada', 'kabla',
        'kutoka', 'kwenda', 'huko', 'hapa', 'hapo', 'sini', 'juu',
        'chini', 'karibu', 'mbali', 'jibu', 'swali', 'ujumbe', 'ujumuika'
    }
    
    # English words (for comparison)
    ENGLISH_VOCABULARY = {
        'hello', 'thank', 'please', 'help', 'friend', 'nil', 'returns',
        'file', 'password', 'login', 'submit', 'form', 'booking',
        'appointment', 'service', 'government', 'portal', 'access',
        'recovery', 'registration', 'confirmation', 'sms'
    }
    
    # Kiswahili-specific characters/patterns
    KISWAHILI_PATTERNS = [
        r'\b[a-z]{2,}[iaeou][aeiou]+',  # Multiple vowels (common in Sw)
        r'\bk[ua]\w+',  # Verb prefixes
        r'\bm[ao]\w+',  # Noun prefixes
        r'\b(ni|na|ja|li|tu|wa)\w+',  # Tense markers
    ]
    
    def __init__(self):
        """Initialize language detector."""
        self.session_language = None
        self.detected_languages = []
    
    def detect(self, text: str, session_context: Optional[Dict] = None) -> Tuple[str, float]:
        """
        Detect language of text.
        
        Args:
            text: Input text to analyze
            session_context: Optional session context with previous language preference
        
        Returns:
            Tuple of (language_code, confidence_score)
            language_code: 'en' or 'sw'
            confidence_score: 0.0 to 1.0
        """
        try:
            # Check session language preference first
            if session_context and session_context.get('preferred_language'):
                return session_context['preferred_language'], 1.0
            
            normalized_text = text.lower().strip()
            
            # Score Kiswahili indicators
            sw_score = self._score_kiswahili(normalized_text)
            
            # Score English indicators
            en_score = self._score_english(normalized_text)
            
            # Determine dominant language
            if sw_score > en_score + 0.2:  # Kiswahili needs higher margin
                confidence = min(sw_score / (sw_score + en_score) if (sw_score + en_score) > 0 else 0.6, 1.0)
                return 'sw', confidence
            else:
                confidence = min(en_score / (sw_score + en_score) if (sw_score + en_score) > 0 else 0.6, 1.0)
                return 'en', confidence
        
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return 'en', 0.5
    
    def _score_kiswahili(self, text: str) -> float:
        """Score how likely text is Kiswahili."""
        score = 0.0
        words = text.split()
        
        # Check for Kiswahili vocabulary
        sw_word_count = sum(1 for word in words if self._normalize_word(word) in self.KISWAHILI_VOCABULARY)
        if len(words) > 0:
            score += (sw_word_count / len(words)) * 0.5
        
        # Check for Kiswahili patterns
        pattern_matches = sum(1 for pattern in self.KISWAHILI_PATTERNS if re.search(pattern, text))
        score += (pattern_matches / len(self.KISWAHILI_PATTERNS)) * 0.3
        
        # Check for common Kiswahili phrases
        sw_phrases = [
            'nataka', 'karibu', 'asante', 'tafadhali', 'je', 'nini',
            'wakati gani', 'siku gani', 'wapi', 'nani', 'lini'
        ]
        phrase_count = sum(1 for phrase in sw_phrases if phrase in text)
        score += min(phrase_count * 0.1, 0.2)
        
        return min(score, 1.0)
    
    def _score_english(self, text: str) -> float:
        """Score how likely text is English."""
        score = 0.0
        words = text.split()
        
        # Check for English vocabulary
        en_word_count = sum(1 for word in words if self._normalize_word(word) in self.ENGLISH_VOCABULARY)
        if len(words) > 0:
            score += (en_word_count / len(words)) * 0.4
        
        # Check for English contractions
        if re.search(r"[a-z]+'[a-z]+", text):
            score += 0.2
        
        # Check for common English patterns
        if re.search(r'\b(the|a|an|is|are|be|been|have|has|do|does|did)\b', text):
            score += 0.3
        
        # Check for English phrases
        en_phrases = [
            'file nil', 'kra pin', 'recover pin', 'itax', 'help me',
            'how to', 'what is', 'where is', 'when can', 'do i'
        ]
        phrase_count = sum(1 for phrase in en_phrases if phrase in text)
        score += min(phrase_count * 0.1, 0.2)
        
        return min(score, 1.0)
    
    def _normalize_word(self, word: str) -> str:
        """Normalize word for matching."""
        return re.sub(r'[^\w]', '', word.lower())
    
    def set_session_language(self, language: str, context: Optional[Dict] = None):
        """Set the preferred language for this session."""
        if language in ['en', 'sw']:
            self.session_language = language
            if context is not None:
                context['preferred_language'] = language
            logger.info(f"Session language set to: {language}")
    
    def supports_code_switching(self) -> bool:
        """Check if code-switching is enabled."""
        return True
    
    def detect_code_switches(self, text: str) -> List[Dict[str, any]]:
        """
        Detect code-switches in text (switches between English and Kiswahili).
        
        Returns:
            List of detected code-switch segments
        """
        segments = []
        current_language = None
        current_segment = ""
        current_start = 0
        
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            detected_lang, confidence = self.detect(sentence)
            
            if detected_lang != current_language:
                if current_segment:
                    segments.append({
                        'text': current_segment.strip(),
                        'language': current_language,
                        'start': current_start,
                        'end': current_start + len(current_segment)
                    })
                
                current_language = detected_lang
                current_segment = sentence + '. '
                current_start = len(text) - len(current_segment)
            else:
                current_segment += sentence + '. '
        
        # Add final segment
        if current_segment:
            segments.append({
                'text': current_segment.strip(),
                'language': current_language,
                'start': len(text) - len(current_segment),
                'end': len(text)
            })
        
        return segments
    
    def translate_intent_keywords(self, intent: str, target_language: str) -> Dict[str, List[str]]:
        """
        Provide keywords in target language for intent matching.
        
        Args:
            intent: Intent type (e.g., 'kra_nil_returns')
            target_language: Target language ('en' or 'sw')
        
        Returns:
            Dict with keywords in target language
        """
        intent_translations = {
            'kra_nil_returns': {
                'en': ['nil returns', 'zero returns', 'file nil', 'no income', 'annual returns'],
                'sw': ['nil returns', 'kurudi sifuri', 'kurudi tupu', 'hakuna pendapatan', 'kurudi kila mwaka']
            },
            'kra_pin_recovery': {
                'en': ['recover pin', 'reset pin', 'forgot pin', 'lost pin', 'pin recovery'],
                'sw': ['komboa pin', 'badili pin', 'sahau pin', 'pin iliyopotozwa', 'kukomboa pin']
            },
            'kra_pin_generation': {
                'en': ['get pin', 'generate pin', 'new pin', 'apply for pin', 'pin application'],
                'sw': ['pata pin', 'tengeneza pin', 'pin mpya', 'omba pin', 'ombi la pin']
            },
            'itax_help': {
                'en': ['itax', 'login', 'password', 'access itax', 'itax portal'],
                'sw': ['itax', 'ingia', 'neno siri', 'ingilia itax', 'mradi wa itax']
            }
        }
        
        return intent_translations.get(intent, {}).get(target_language, [])


# Global instance
language_detector = LanguageDetector()
