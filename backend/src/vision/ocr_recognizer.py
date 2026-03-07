"""
OCR Recognition Module

This module provides text recognition functionality for visual verification.
Phase 2: Mock implementation returning simulated OCR results.
"""

import asyncio
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    """Result of OCR recognition."""
    success: bool = Field(..., description="OCR process success")
    detected_text: Optional[str] = Field(None, description="Text detected from image")
    confidence: Optional[float] = Field(None, description="Confidence score (0.0-1.0)")
    bounding_boxes: List[Tuple[int, int, int, int]] = Field(default_factory=list,
                                                           description="List of [x1, y1, x2, y2] bounding boxes")
    languages: List[str] = Field(default_factory=list, description="Detected languages")
    error_message: Optional[str] = Field(None, description="Error message if OCR failed")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class OCRRecognizer:
    """
    OCR text recognizer for reading text from images.

    Phase 2: Mock implementation that simulates OCR recognition.
    Returns simulated text detection for development and testing.
    """

    def __init__(self, mock_mode: bool = True):
        """
        Initialize OCR recognizer.

        Args:
            mock_mode: If True, use mock recognition (always True for Phase 2)
        """
        self.mock_mode = mock_mode
        print("[OCRRecognizer] Initialized in mock mode")

        # Mock hospital location texts (simulating real hospital signage)
        self.mock_texts = [
            "急诊室 Emergency Room",
            "外科手术室 Surgery Room",
            "内科诊室 Internal Medicine",
            "儿科诊室 Pediatric Clinic",
            "放射科 Radiology Department",
            "药房 Pharmacy",
            "护士站 Nurse Station",
            "接待处 Reception",
            "电梯 Elevator",
            "楼梯 Stairs",
            "卫生间 Restroom",
            "候诊区 Waiting Area",
            "医生办公室 Doctor's Office",
            "检验科 Laboratory",
            "住院部 Inpatient Department"
        ]

    async def recognize(self, image_data: "np.ndarray") -> OCRResult:
        """
        Recognize text in an image.

        Args:
            image_data: Input image as numpy array (H, W, C) in RGB format

        Returns:
            OCRResult with recognized text
        """
        import time
        start_time = time.time()

        # Simulate processing delay
        await asyncio.sleep(0.2)

        try:
            # Mock recognition logic
            # In real implementation, this would use OCR engines like EasyOCR or Tesseract

            import random

            # Select mock text based on some characteristic (e.g., image hash)
            # This ensures some consistency for the same image
            try:
                # Try to create a hash from image data if available
                import numpy as np
                if hasattr(image_data, 'shape'):
                    image_hash = hash(str(image_data.shape)) % len(self.mock_texts)
                else:
                    image_hash = random.randint(0, len(self.mock_texts) - 1)
            except:
                image_hash = random.randint(0, len(self.mock_texts) - 1)

            detected_text = self.mock_texts[image_hash]

            # Sometimes add variation (simulating OCR errors or variations)
            if random.random() > 0.7:  # 30% chance
                variations = [
                    f"{detected_text}",
                    detected_text.split()[0],  # Just Chinese part
                    detected_text.split()[-1],  # Just English part
                    detected_text.upper(),
                    detected_text.lower()
                ]
                detected_text = random.choice(variations)

            # Mock bounding box (center of image)
            try:
                height, width = image_data.shape[:2]
            except:
                # Default dimensions if image_data not available
                height, width = 480, 640

            box_width = width // 4
            box_height = height // 8
            center_x = width // 2 - box_width // 2
            center_y = height // 2 - box_height // 2

            # Confidence based on text length and randomness
            base_confidence = 0.85 + (len(detected_text) * 0.005)  # Longer text = slightly higher confidence
            confidence = min(0.98, max(0.6, base_confidence + random.uniform(-0.1, 0.1)))

            processing_time = (time.time() - start_time) * 1000

            return OCRResult(
                success=True,
                detected_text=detected_text,
                confidence=confidence,
                bounding_boxes=[(center_x, center_y, center_x + box_width, center_y + box_height)],
                languages=['zh', 'en'],
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return OCRResult(
                success=False,
                error_message=f"OCR recognition error: {e}",
                processing_time_ms=processing_time
            )

    async def recognize_base64(self, image_base64: str) -> OCRResult:
        """
        Recognize text from base64 encoded image.

        Args:
            image_base64: Base64 encoded image string

        Returns:
            OCRResult with recognized text
        """
        import time
        start_time = time.time()

        # Simulate processing delay
        await asyncio.sleep(0.25)

        try:
            # In mock mode, we don't actually decode the image
            # Just simulate recognition based on expected content

            import random

            # Select mock text
            detected_text = random.choice(self.mock_texts)

            # Sometimes simulate partial or noisy recognition
            if random.random() > 0.8:  # 20% chance
                # Simulate OCR errors
                error_types = [
                    f"{detected_text[:len(detected_text)//2]}...",  # Truncated
                    detected_text.replace("室", "").replace("Room", ""),  # Missing characters
                    detected_text.upper()[:10] + "...",  # Uppercase truncated
                ]
                detected_text = random.choice(error_types)

            # Mock image dimensions
            mock_width = 640
            mock_height = 480

            # Mock bounding box
            box_width = mock_width // 4
            box_height = mock_height // 8
            center_x = mock_width // 2 - box_width // 2
            center_y = mock_height // 2 - box_height // 2

            # Confidence with some randomness
            confidence = 0.88 + random.uniform(-0.15, 0.1)

            processing_time = (time.time() - start_time) * 1000

            return OCRResult(
                success=True,
                detected_text=detected_text,
                confidence=max(0.5, min(0.99, confidence)),  # Clamp to reasonable range
                bounding_boxes=[(center_x, center_y, center_x + box_width, center_y + box_height)],
                languages=['zh', 'en'],
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return OCRResult(
                success=False,
                error_message=f"Base64 OCR error: {e}",
                processing_time_ms=processing_time
            )


# Global OCR instance for easy access
_ocr_instance: Optional[OCRRecognizer] = None


async def get_ocr_recognizer(mock_mode: bool = True) -> OCRRecognizer:
    """
    Get or create global OCR recognizer instance.

    Args:
        mock_mode: Whether to use mock mode

    Returns:
        OCRRecognizer instance
    """
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = OCRRecognizer(mock_mode=mock_mode)
    return _ocr_instance


async def recognize_text(image_data: "np.ndarray", mock_mode: bool = True) -> OCRResult:
    """
    Convenience function to recognize text.

    Args:
        image_data: Input image as numpy array
        mock_mode: Whether to use mock mode

    Returns:
        OCRResult
    """
    recognizer = await get_ocr_recognizer(mock_mode)
    return await recognizer.recognize(image_data)


async def recognize_text_base64(image_base64: str, mock_mode: bool = True) -> OCRResult:
    """
    Convenience function to recognize text from base64 image.

    Args:
        image_base64: Base64 encoded image string
        mock_mode: Whether to use mock mode

    Returns:
        OCRResult
    """
    recognizer = await get_ocr_recognizer(mock_mode)
    return await recognizer.recognize_base64(image_base64)