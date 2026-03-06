"""
OCR Recognition Module

This module provides text recognition functionality using OCR.
Supports both Chinese and English text recognition.
"""

import numpy as np
from typing import Optional, List, Tuple
from pydantic import BaseModel
import base64
from io import BytesIO
from PIL import Image


class OCRResult(BaseModel):
    """Result of OCR recognition."""
    success: bool
    detected_text: Optional[str] = None
    confidence: Optional[float] = None
    bounding_boxes: List[Tuple[int, int, int, int]] = []  # List of [x1, y1, x2, y2]
    languages: List[str] = []  # Detected languages
    error_message: Optional[str] = None
    processing_time_ms: Optional[float] = None


class OCRRecognizer:
    """OCR text recognizer using EasyOCR or fallback to Tesseract."""

    def __init__(self, mock_mode: bool = False):
        """
        Initialize OCR recognizer.

        Args:
            mock_mode: If True, use mock recognition instead of real OCR.
        """
        self.mock_mode = mock_mode
        self.ocr_engine = None
        self._initialized = False

        if not self.mock_mode:
            self._initialize_ocr()

    def _initialize_ocr(self):
        """Initialize OCR engine."""
        try:
            # Try to import EasyOCR first
            import easyocr
            print("[OCRRecognizer] Using EasyOCR engine")

            # Initialize reader for Chinese and English
            self.ocr_engine = easyocr.Reader(['ch_sim', 'en'], gpu=False)
            self._initialized = True
            print("[OCRRecognizer] EasyOCR initialized successfully")

        except ImportError:
            print("[OCRRecognizer] EasyOCR not available, trying Tesseract")
            try:
                import pytesseract
                from PIL import Image
                self.ocr_engine = 'tesseract'
                self._initialized = True
                print("[OCRRecognizer] Using Tesseract OCR")

                # Test Tesseract availability
                try:
                    pytesseract.get_tesseract_version()
                except Exception:
                    print("[OCRRecognizer] Tesseract not found in PATH")
                    self._initialized = False
                    self.mock_mode = True

            except ImportError:
                print("[OCRRecognizer] Neither EasyOCR nor Tesseract available, using mock mode")
                self.mock_mode = True
                self._initialized = False

    def preprocess_for_ocr(self, image_data: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR recognition.

        Args:
            image_data: Input image as numpy array (H, W, C) in RGB format

        Returns:
            Preprocessed image
        """
        try:
            import cv2

            # Convert to grayscale if needed
            if len(image_data.shape) == 3:
                gray = cv2.cvtColor(image_data, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_data

            # Apply adaptive thresholding for better text contrast
            # This helps with black boxes on potentially varying backgrounds
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,  # Invert for black text on white
                11, 2
            )

            # Optional: denoise
            denoised = cv2.medianBlur(binary, 3)

            # Convert back to 3 channels if needed by OCR engine
            if self.ocr_engine == 'tesseract':
                # Tesseract works better with inverted black-on-white
                result = cv2.bitwise_not(denoised)
                result = cv2.cvtColor(result, cv2.COLOR_GRAY2RGB)
            else:
                # EasyOCR can handle the binary image
                result = denoised

            return result

        except ImportError:
            # If OpenCV not available, return original
            return image_data
        except Exception as e:
            print(f"[OCRRecognizer] Preprocessing error: {e}")
            return image_data

    def recognize_with_easyocr(self, image_data: np.ndarray) -> OCRResult:
        """
        Recognize text using EasyOCR.

        Args:
            image_data: Input image as numpy array

        Returns:
            OCRResult
        """
        import time
        start_time = time.time()

        try:
            # EasyOCR expects BGR format
            import cv2
            if len(image_data.shape) == 3:
                if image_data.shape[2] == 3:  # RGB
                    image_bgr = cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR)
                elif image_data.shape[2] == 4:  # RGBA
                    image_rgb = cv2.cvtColor(image_data, cv2.COLOR_RGBA2RGB)
                    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                else:
                    image_bgr = image_data
            else:
                # Grayscale to BGR
                image_bgr = cv2.cvtColor(image_data, cv2.COLOR_GRAY2BGR)

            # Run OCR
            results = self.ocr_engine.readtext(image_bgr)

            # Process results
            all_text = []
            bounding_boxes = []
            confidences = []

            for (bbox, text, confidence) in results:
                all_text.append(text)
                bounding_boxes.append(bbox)
                confidences.append(confidence)

            # Combine text
            combined_text = ' '.join(all_text)

            # Calculate average confidence
            avg_confidence = np.mean(confidences) if confidences else 0.0

            processing_time = (time.time() - start_time) * 1000

            return OCRResult(
                success=True,
                detected_text=combined_text,
                confidence=avg_confidence,
                bounding_boxes=[tuple(map(int, box)) for box in bounding_boxes],
                languages=['ch_sim', 'en'],
                processing_time_ms=processing_time
            )

        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"EasyOCR error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000
            )

    def recognize_with_tesseract(self, image_data: np.ndarray) -> OCRResult:
        """
        Recognize text using Tesseract.

        Args:
            image_data: Input image as numpy array

        Returns:
            OCRResult
        """
        import time
        start_time = time.time()

        try:
            import pytesseract
            from PIL import Image

            # Convert numpy array to PIL Image
            if len(image_data.shape) == 3:
                pil_image = Image.fromarray(image_data)
            else:
                pil_image = Image.fromarray(image_data)

            # Preprocess for Tesseract
            processed_image = self.preprocess_for_ocr(image_data)

            # Convert processed image to PIL
            if len(processed_image.shape) == 3:
                processed_pil = Image.fromarray(processed_image)
            else:
                processed_pil = Image.fromarray(processed_image)

            # Run OCR with Chinese and English
            custom_config = r'--oem 3 --psm 6 -l chi_sim+eng'
            text = pytesseract.image_to_string(processed_pil, config=custom_config)

            # Try to get confidence (Tesseract doesn't provide easy confidence per word)
            # We'll use a placeholder confidence
            confidence = 0.85 if text.strip() else 0.0

            # Get bounding boxes
            data = pytesseract.image_to_data(processed_pil, config=custom_config, output_type=pytesseract.Output.DICT)

            bounding_boxes = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    bounding_boxes.append((x, y, x + w, y + h))

            processing_time = (time.time() - start_time) * 1000

            return OCRResult(
                success=True,
                detected_text=text.strip(),
                confidence=confidence,
                bounding_boxes=bounding_boxes,
                languages=['chi_sim', 'eng'],
                processing_time_ms=processing_time
            )

        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"Tesseract error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000
            )

    def recognize(self, image_data: np.ndarray) -> OCRResult:
        """
        Recognize text in an image.

        Args:
            image_data: Input image as numpy array (H, W, C) in RGB format

        Returns:
            OCRResult with recognized text
        """
        import time
        start_time = time.time()

        if self.mock_mode:
            return self._mock_recognize(image_data)

        if not self._initialized:
            return OCRResult(
                success=False,
                error_message="OCR engine not initialized"
            )

        try:
            if isinstance(self.ocr_engine, str) and self.ocr_engine == 'tesseract':
                result = self.recognize_with_tesseract(image_data)
            else:
                # Assume EasyOCR
                result = self.recognize_with_easyocr(image_data)

            # Ensure processing time is set
            if result.processing_time_ms is None:
                result.processing_time_ms = (time.time() - start_time) * 1000

            return result

        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"Recognition error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000
            )

    def _mock_recognize(self, image_data: np.ndarray) -> OCRResult:
        """Mock OCR recognition for development."""
        import time
        start_time = time.time()

        # Simulate processing delay
        import random
        time.sleep(0.2 + random.random() * 0.2)

        # Mock text based on image characteristics
        height, width = image_data.shape[:2]

        # Some mock text samples (simulating hospital navigation labels)
        mock_texts = [
            "急诊室 Emergency Room",
            "外科手术室 Surgery Room",
            "内科诊室 Internal Medicine",
            "儿科诊室 Pediatric Clinic",
            "放射科 Radiology",
            "药房 Pharmacy",
            "护士站 Nurse Station",
            "接待处 Reception",
            "电梯 Elevator",
            "楼梯 Stairs"
        ]

        # Choose a mock text based on image size or other characteristics
        text_index = hash(str(image_data.shape)) % len(mock_texts)
        mock_text = mock_texts[text_index]

        # Mock bounding box (center of image)
        box_width = width // 4
        box_height = height // 8
        center_x = width // 2 - box_width // 2
        center_y = height // 2 - box_height // 2

        processing_time = (time.time() - start_time) * 1000

        return OCRResult(
            success=True,
            detected_text=mock_text,
            confidence=0.92 + random.random() * 0.06,  # 0.92-0.98
            bounding_boxes=[(center_x, center_y, center_x + box_width, center_y + box_height)],
            languages=['ch_sim', 'en'],
            processing_time_ms=processing_time
        )

    def recognize_base64(self, image_base64: str) -> OCRResult:
        """
        Recognize text from base64 encoded image.

        Args:
            image_base64: Base64 encoded image string

        Returns:
            OCRResult with recognized text
        """
        try:
            # Decode base64
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_bytes))

            # Convert to numpy array (RGB)
            image_np = np.array(image)

            return self.recognize(image_np)

        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"Base64 decoding error: {e}"
            )

    def recognize_in_region(self, image_data: np.ndarray,
                           region: Tuple[int, int, int, int]) -> OCRResult:
        """
        Recognize text in a specific region of the image.

        Args:
            image_data: Input image
            region: (x1, y1, x2, y2) bounding box

        Returns:
            OCRResult for the specified region
        """
        x1, y1, x2, y2 = region
        region_image = image_data[y1:y2, x1:x2]
        return self.recognize(region_image)


# Global OCR instance for easy access
_ocr_instance: Optional[OCRRecognizer] = None


def get_ocr_recognizer(mock_mode: bool = False) -> OCRRecognizer:
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


async def recognize_text(image_data: np.ndarray, mock_mode: bool = False) -> OCRResult:
    """
    Convenience function to recognize text.

    Args:
        image_data: Input image as numpy array
        mock_mode: Whether to use mock mode

    Returns:
        OCRResult
    """
    recognizer = get_ocr_recognizer(mock_mode)
    return recognizer.recognize(image_data)