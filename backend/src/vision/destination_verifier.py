"""
Destination Verification Module

This module verifies if detected text matches expected destination.
Phase 2: Mock implementation returning simulated verification results.
"""

import asyncio
import re
from typing import Optional
from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    """Result of destination verification."""
    success: bool = Field(..., description="Verification process success")
    verified: bool = Field(..., description="Whether destination matches expected")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    detected_text: Optional[str] = Field(None, description="Text detected from image")
    expected_text: Optional[str] = Field(None, description="Expected destination text")
    message: str = Field(..., description="Verification result message")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class DestinationVerifier:
    """
    Verifies if detected text matches expected destination.

    Phase 2: Mock implementation that simulates verification logic.
    Returns simulated results for development and testing.
    """

    def __init__(self, mock_mode: bool = True):
        """
        Initialize destination verifier.

        Args:
            mock_mode: If True, use mock verification (always True for Phase 2)
        """
        self.mock_mode = mock_mode
        print("[DestinationVerifier] Initialized in mock mode")

    async def verify(
        self,
        detected_text: str,
        expected_destination: str,
        image_data: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify if detected text matches expected destination.

        Args:
            detected_text: Text detected from OCR
            expected_destination: Expected destination identifier or text
            image_data: Optional base64 encoded image data (not used in mock mode)

        Returns:
            VerificationResult with match status and confidence
        """
        import time
        start_time = time.time()

        # Simulate processing delay
        await asyncio.sleep(0.1)

        # Mock verification logic
        # In real implementation, this would compare text similarity,
        # handle variations, use NLP, etc.

        # Clean and normalize text for comparison
        detected_clean = self._normalize_text(detected_text)
        expected_clean = self._normalize_text(expected_destination)

        # Simple mock matching logic
        verified = False
        confidence = 0.0
        message = ""

        # Check for exact or partial matches
        if detected_clean == expected_clean:
            verified = True
            confidence = 0.95
            message = f"Destination match confirmed: '{detected_text}'"
        elif expected_clean in detected_clean:
            verified = True
            confidence = 0.85
            message = f"Destination partially matched: '{expected_destination}' found in '{detected_text}'"
        elif detected_clean in expected_clean:
            verified = True
            confidence = 0.80
            message = f"Detected text '{detected_text}' is part of expected destination '{expected_destination}'"
        else:
            # Check for common hospital location keywords
            common_keywords = ['诊室', 'clinic', 'room', '室', '科', 'department', '急诊', '手术']
            detected_has_keyword = any(keyword in detected_clean for keyword in common_keywords)
            expected_has_keyword = any(keyword in expected_clean for keyword in common_keywords)

            if detected_has_keyword and expected_has_keyword:
                # Both have hospital-related keywords, might be a match
                verified = True
                confidence = 0.70
                message = f"Both texts contain hospital location keywords"
            else:
                verified = False
                confidence = 0.30
                message = f"Destination mismatch: '{detected_text}' doesn't match '{expected_destination}'"

        # Add some randomness to simulate real-world variations
        import random
        confidence = max(0.1, min(0.99, confidence + random.uniform(-0.1, 0.1)))

        processing_time = (time.time() - start_time) * 1000

        return VerificationResult(
            success=True,
            verified=verified,
            confidence=confidence,
            detected_text=detected_text,
            expected_text=expected_destination,
            message=message,
            processing_time_ms=processing_time
        )

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Input text

        Returns:
            Normalized text (lowercase, whitespace removed, punctuation removed)
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and special characters
        import re
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)  # Keep Chinese characters

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    async def verify_with_image(
        self,
        image_data: str,
        expected_destination: str
    ) -> VerificationResult:
        """
        Verify destination directly from image data.

        Note: In mock mode, this simulates the full pipeline.
        In real implementation, this would call:
        1. Black box segmentation
        2. OCR recognition
        3. Text comparison

        Args:
            image_data: Base64 encoded image data
            expected_destination: Expected destination identifier

        Returns:
            VerificationResult
        """
        import time
        start_time = time.time()

        # Simulate full pipeline delay
        await asyncio.sleep(0.3)

        # Mock detected text based on expected destination
        # In real implementation, this would come from OCR module
        mock_detected_text = f"模拟文本: {expected_destination}"

        # Add some variation
        import random
        variations = [
            f"{expected_destination}诊室",
            f"{expected_destination}科室",
            f"{expected_destination} Clinic",
            f"Room {expected_destination}",
            f"Department of {expected_destination}"
        ]

        if random.random() > 0.3:  # 70% chance of matching text
            mock_detected_text = random.choice(variations)

        # Verify using the text verification method
        result = await self.verify(mock_detected_text, expected_destination)

        # Update processing time
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result


# Global verifier instance for easy access
_verifier_instance: Optional[DestinationVerifier] = None


async def get_destination_verifier(mock_mode: bool = True) -> DestinationVerifier:
    """
    Get or create global destination verifier instance.

    Args:
        mock_mode: Whether to use mock mode

    Returns:
        DestinationVerifier instance
    """
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = DestinationVerifier(mock_mode=mock_mode)
    return _verifier_instance


async def verify_destination(
    detected_text: str,
    expected_destination: str,
    mock_mode: bool = True
) -> VerificationResult:
    """
    Convenience function to verify destination match.

    Args:
        detected_text: Text detected from OCR
        expected_destination: Expected destination
        mock_mode: Whether to use mock mode

    Returns:
        VerificationResult
    """
    verifier = await get_destination_verifier(mock_mode)
    return await verifier.verify(detected_text, expected_destination)


async def verify_destination_from_image(
    image_data: str,
    expected_destination: str,
    mock_mode: bool = True
) -> VerificationResult:
    """
    Convenience function to verify destination directly from image.

    Args:
        image_data: Base64 encoded image
        expected_destination: Expected destination
        mock_mode: Whether to use mock mode

    Returns:
        VerificationResult
    """
    verifier = await get_destination_verifier(mock_mode)
    return await verifier.verify_with_image(image_data, expected_destination)