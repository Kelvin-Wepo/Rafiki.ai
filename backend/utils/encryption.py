"""
Encryption utilities for secure data handling.

Provides AES-256-GCM encryption for sensitive session data,
conversation context, and PII protection.
"""

import os
import base64
import json
import hashlib
import secrets
from typing import Any, Dict, Optional, Union
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EncryptionService:
    """
    AES-256-GCM encryption service for sensitive data.
    
    Features:
    - AES-256-GCM authenticated encryption
    - Key derivation from secret key
    - Automatic nonce generation
    - JSON serialization for complex data
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            secret_key: Base secret key for encryption (uses settings if not provided)
        """
        self._secret_key = secret_key or settings.SESSION_SECRET_KEY
        self._derived_key = self._derive_key(self._secret_key)
        self._aesgcm = AESGCM(self._derived_key)
        
        logger.info("Encryption service initialized")
    
    def _derive_key(self, secret: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive a 256-bit key from the secret using PBKDF2.
        
        Args:
            secret: Base secret string
            salt: Optional salt (uses fixed salt if not provided for consistency)
        
        Returns:
            32-byte derived key
        """
        if salt is None:
            # Use a fixed salt derived from the secret for key consistency
            salt = hashlib.sha256(b"rafiki_session_salt").digest()[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        return kdf.derive(secret.encode('utf-8'))
    
    def encrypt(self, data: Union[str, Dict, Any]) -> str:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            data: Data to encrypt (string, dict, or JSON-serializable object)
        
        Returns:
            Base64-encoded encrypted data with nonce prepended
        """
        try:
            # Serialize if not a string
            if not isinstance(data, str):
                data = json.dumps(data, default=str)
            
            # Generate random nonce (96 bits for GCM)
            nonce = secrets.token_bytes(12)
            
            # Encrypt
            ciphertext = self._aesgcm.encrypt(
                nonce,
                data.encode('utf-8'),
                None  # No additional authenticated data
            )
            
            # Prepend nonce to ciphertext
            encrypted = nonce + ciphertext
            
            # Base64 encode for storage
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt AES-256-GCM encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
        
        Returns:
            Decrypted string
        """
        try:
            # Base64 decode
            encrypted = base64.b64decode(encrypted_data)
            
            # Extract nonce (first 12 bytes)
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]
            
            # Decrypt
            plaintext = self._aesgcm.decrypt(
                nonce,
                ciphertext,
                None
            )
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Decryption failed: {e}")
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt and parse JSON data.
        
        Args:
            encrypted_data: Base64-encoded encrypted JSON
        
        Returns:
            Parsed dictionary
        """
        plaintext = self.decrypt(encrypted_data)
        return json.loads(plaintext)
    
    def hash_identifier(self, identifier: str) -> str:
        """
        Create a secure hash of an identifier for lookup without exposing the value.
        
        Args:
            identifier: Value to hash (e.g., phone number, ID number)
        
        Returns:
            Hex-encoded SHA-256 hash
        """
        salted = f"{self._secret_key}:{identifier}"
        return hashlib.sha256(salted.encode('utf-8')).hexdigest()
    
    def generate_session_token(self) -> str:
        """
        Generate a cryptographically secure session token.
        
        Returns:
            URL-safe base64-encoded token
        """
        return secrets.token_urlsafe(32)
    
    def create_digital_signature(self, data: str) -> str:
        """
        Create a simple HMAC signature for data integrity verification.
        
        Args:
            data: Data to sign
        
        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        import hmac
        signature = hmac.new(
            self._derived_key,
            data.encode('utf-8'),
            hashlib.sha256
        )
        return signature.hexdigest()
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """
        Verify a digital signature.
        
        Args:
            data: Original data
            signature: Signature to verify
        
        Returns:
            True if signature is valid
        """
        import hmac
        expected = self.create_digital_signature(data)
        return hmac.compare_digest(expected, signature)


class PIIDetector:
    """
    Detects and masks Personally Identifiable Information (PII).
    
    Detects:
    - Kenyan National ID numbers
    - KRA PIN numbers
    - Phone numbers
    - Email addresses
    - Passport numbers
    - Bank account numbers
    """
    
    # Regex patterns for PII detection
    PATTERNS = {
        'national_id': r'\b\d{7,8}\b',  # 7-8 digit ID numbers
        'kra_pin': r'\b[A-Z]\d{9}[A-Z]\b',  # KRA PIN format: A123456789B
        'phone': r'\b(?:\+254|254|0)?[17]\d{8}\b',  # Kenyan phone numbers
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'passport': r'\b[A-Z]{1,2}\d{6,7}\b',  # Kenyan passport format
        'bank_account': r'\b\d{10,16}\b',  # Bank account numbers
        'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',  # Credit card numbers
    }
    
    # Mask patterns for each PII type
    MASKS = {
        'national_id': '***ID***',
        'kra_pin': '***PIN***',
        'phone': '***PHONE***',
        'email': '***EMAIL***',
        'passport': '***PASSPORT***',
        'bank_account': '***ACCOUNT***',
        'credit_card': '***CARD***',
    }
    
    def __init__(self):
        """Initialize PII detector with compiled patterns."""
        import re
        self._compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.PATTERNS.items()
        }
        logger.info("PII detector initialized")
    
    def detect(self, text: str) -> Dict[str, list]:
        """
        Detect PII in text.
        
        Args:
            text: Text to scan for PII
        
        Returns:
            Dictionary mapping PII type to list of found values
        """
        found = {}
        
        for pii_type, pattern in self._compiled_patterns.items():
            matches = pattern.findall(text)
            if matches:
                found[pii_type] = matches
        
        if found:
            logger.warning(f"PII detected: {list(found.keys())}")
        
        return found
    
    def mask(self, text: str, pii_types: Optional[list] = None) -> str:
        """
        Mask PII in text.
        
        Args:
            text: Text to mask
            pii_types: Optional list of PII types to mask (masks all if None)
        
        Returns:
            Text with PII masked
        """
        masked_text = text
        
        types_to_mask = pii_types or list(self.PATTERNS.keys())
        
        for pii_type in types_to_mask:
            if pii_type in self._compiled_patterns:
                pattern = self._compiled_patterns[pii_type]
                mask = self.MASKS.get(pii_type, '***REDACTED***')
                masked_text = pattern.sub(mask, masked_text)
        
        return masked_text
    
    def contains_pii(self, text: str) -> bool:
        """
        Check if text contains any PII.
        
        Args:
            text: Text to check
        
        Returns:
            True if PII is found
        """
        return bool(self.detect(text))
    
    def get_pii_summary(self, text: str) -> Dict[str, int]:
        """
        Get a summary count of PII types found.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary mapping PII type to count
        """
        found = self.detect(text)
        return {k: len(v) for k, v in found.items()}


# Global instances
_encryption_service: Optional[EncryptionService] = None
_pii_detector: Optional[PIIDetector] = None


def get_encryption_service() -> EncryptionService:
    """Get the global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def get_pii_detector() -> PIIDetector:
    """Get the global PII detector instance."""
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    return _pii_detector
