"""
Black Box Segmentation Module

This module provides black box segmentation using DeepLabV3 MobileNetV2 TFLite model.
Detects black rectangular boxes (likely text labels) in images.
"""

import numpy as np
from typing import Optional, Tuple
from pydantic import BaseModel
from pathlib import Path

# Try to import TensorFlow Lite
try:
    import tflite_runtime.interpreter as tflite
    TFLITE_AVAILABLE = True
except ImportError:
    try:
        import tensorflow.lite as tflite
        TFLITE_AVAILABLE = True
    except ImportError:
        TFLITE_AVAILABLE = False
        print("[BlackBoxSegmenter] TensorFlow Lite not available, using mock mode")

from src.config.general import BLACK_BOX_SEGMENTATION_MODEL_PATH


class SegmentationResult(BaseModel):
    """Result of black box segmentation."""
    success: bool
    bounding_boxes: list = []  # List of [x1, y1, x2, y2] bounding boxes
    mask: Optional[np.ndarray] = None  # Binary mask of detected black boxes
    confidence_scores: list[float] = []
    error_message: Optional[str] = None
    processing_time_ms: Optional[float] = None


class BlackBoxSegmenter:
    """Black box segmentation using DeepLabV3 MobileNetV2 TFLite model."""

    def __init__(self, mock_mode: bool = False):
        """
        Initialize black box segmenter.

        Args:
            mock_mode: If True, use mock detection instead of real model.
        """
        self.mock_mode = mock_mode or not TFLITE_AVAILABLE
        self.model_loaded = False
        self.interpreter = None
        self.input_details = None
        self.output_details = None

        if not self.mock_mode:
            self._load_model()

    def _load_model(self):
        """Load TFLite model."""
        try:
            if not BLACK_BOX_SEGMENTATION_MODEL_PATH.exists():
                print(f"[BlackBoxSegmenter] Model not found at {BLACK_BOX_SEGMENTATION_MODEL_PATH}")
                self.mock_mode = True
                return

            print(f"[BlackBoxSegmenter] Loading model from {BLACK_BOX_SEGMENTATION_MODEL_PATH}")
            self.interpreter = tflite.Interpreter(
                model_path=str(BLACK_BOX_SEGMENTATION_MODEL_PATH)
            )
            self.interpreter.allocate_tensors()

            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

            self.model_loaded = True
            print(f"[BlackBoxSegmenter] Model loaded successfully")

        except Exception as e:
            print(f"[BlackBoxSegmenter] Failed to load model: {e}")
            self.mock_mode = True

    def preprocess_image(self, image_data: np.ndarray) -> np.ndarray:
        """
        Preprocess image for DeepLabV3 model.

        Args:
            image_data: Input image as numpy array (H, W, C) in RGB format

        Returns:
            Preprocessed image ready for inference
        """
        # DeepLabV3 expects images normalized to [0, 1]
        if image_data.dtype != np.float32:
            image_data = image_data.astype(np.float32)

        # Normalize to [0, 1]
        if image_data.max() > 1.0:
            image_data = image_data / 255.0

        # Resize to model input size (typically 513x513 for DeepLabV3)
        target_size = (513, 513)
        if image_data.shape[:2] != target_size:
            # Simple resize (for now - should use proper interpolation)
            # In production, use cv2.resize or similar
            from scipy import ndimage
            scale_y = target_size[0] / image_data.shape[0]
            scale_x = target_size[1] / image_data.shape[1]
            image_data = ndimage.zoom(image_data, (scale_y, scale_x, 1), order=1)

        # Add batch dimension
        image_data = np.expand_dims(image_data, axis=0)

        return image_data

    def postprocess_output(self, output_data: np.ndarray,
                          original_shape: Tuple[int, int]) -> SegmentationResult:
        """
        Postprocess model output to extract black box bounding boxes.

        Args:
            output_data: Model output tensor
            original_shape: Original image shape (H, W, C)

        Returns:
            SegmentationResult with detected bounding boxes
        """
        try:
            # Get segmentation mask (remove batch dimension)
            mask = output_data[0]

            # For DeepLabV3, we need to identify the class for "black box"
            # This depends on the Pascal VOC dataset classes
            # Class 0: background, we'll look for other dark/black regions

            # Simple thresholding for black/dark regions
            # Assuming output is probability map for each class
            if len(mask.shape) == 3:  # (H, W, num_classes)
                # Take argmax to get class predictions
                class_map = np.argmax(mask, axis=-1)
                # Look for non-background classes that might represent black boxes
                # This is a simplification - in reality need proper class mapping
                black_box_mask = (class_map > 0).astype(np.uint8)
            else:
                # Assume binary mask
                black_box_mask = (mask > 0.5).astype(np.uint8)

            # Find connected components (bounding boxes)
            from scipy import ndimage
            labeled_mask, num_features = ndimage.label(black_box_mask)

            bounding_boxes = []
            confidence_scores = []

            for i in range(1, num_features + 1):
                # Get coordinates of this component
                positions = np.argwhere(labeled_mask == i)
                if len(positions) == 0:
                    continue

                y_min, x_min = positions.min(axis=0)
                y_max, x_max = positions.max(axis=0)

                # Scale back to original image size
                scale_y = original_shape[0] / mask.shape[0]
                scale_x = original_shape[1] / mask.shape[1]

                x1 = int(x_min * scale_x)
                y1 = int(y_min * scale_y)
                x2 = int((x_max + 1) * scale_x)
                y2 = int((y_max + 1) * scale_y)

                # Filter by size (remove too small boxes)
                box_area = (x2 - x1) * (y2 - y1)
                if box_area < 100:  # Minimum 100 pixels
                    continue

                # Simple confidence based on area and compactness
                component_mask = (labeled_mask == i)
                area = component_mask.sum()
                bbox_area = (x_max - x_min + 1) * (y_max - y_min + 1)
                compactness = area / bbox_area if bbox_area > 0 else 0

                confidence = min(compactness * 0.8 + 0.2, 1.0)  # 0.2-1.0 range

                bounding_boxes.append([x1, y1, x2, y2])
                confidence_scores.append(confidence)

            return SegmentationResult(
                success=True,
                bounding_boxes=bounding_boxes,
                mask=black_box_mask,
                confidence_scores=confidence_scores
            )

        except Exception as e:
            return SegmentationResult(
                success=False,
                error_message=f"Postprocessing error: {e}"
            )

    def segment(self, image_data: np.ndarray) -> SegmentationResult:
        """
        Segment black boxes in an image.

        Args:
            image_data: Input image as numpy array (H, W, C) in RGB format

        Returns:
            SegmentationResult with detected bounding boxes
        """
        import time
        start_time = time.time()

        if self.mock_mode:
            # Mock detection for development
            return self._mock_segment(image_data)

        if not self.model_loaded:
            return SegmentationResult(
                success=False,
                error_message="Model not loaded"
            )

        try:
            # Preprocess
            original_shape = image_data.shape
            processed_image = self.preprocess_image(image_data)

            # Run inference
            self.interpreter.set_tensor(self.input_details[0]['index'], processed_image)
            self.interpreter.invoke()

            # Get output
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])

            # Postprocess
            result = self.postprocess_output(output_data, original_shape)

            # Add processing time
            processing_time = (time.time() - start_time) * 1000  # ms
            result.processing_time_ms = processing_time

            return result

        except Exception as e:
            return SegmentationResult(
                success=False,
                error_message=f"Inference error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000
            )

    def _mock_segment(self, image_data: np.ndarray) -> SegmentationResult:
        """Mock segmentation for development."""
        import time
        start_time = time.time()

        # Simulate processing delay
        import random
        time.sleep(0.1 + random.random() * 0.1)

        # Create mock bounding boxes
        height, width = image_data.shape[:2]

        # Add some mock boxes (simulating detected text labels)
        bounding_boxes = []
        confidence_scores = []

        # Center box (simulating main text label)
        box_width = width // 3
        box_height = height // 6
        center_x = width // 2 - box_width // 2
        center_y = height // 2 - box_height // 2

        bounding_boxes.append([
            center_x, center_y,
            center_x + box_width, center_y + box_height
        ])
        confidence_scores.append(0.92)

        # Possibly a second smaller box
        if width > 200 and height > 200:
            small_box_width = width // 6
            small_box_height = height // 8
            small_x = width // 4 - small_box_width // 2
            small_y = height // 4 - small_box_height // 2

            bounding_boxes.append([
                small_x, small_y,
                small_x + small_box_width, small_y + small_box_height
            ])
            confidence_scores.append(0.78)

        processing_time = (time.time() - start_time) * 1000

        return SegmentationResult(
            success=True,
            bounding_boxes=bounding_boxes,
            confidence_scores=confidence_scores,
            processing_time_ms=processing_time
        )

    def segment_base64(self, image_base64: str) -> SegmentationResult:
        """
        Segment black boxes from base64 encoded image.

        Args:
            image_base64: Base64 encoded image string

        Returns:
            SegmentationResult with detected bounding boxes
        """
        try:
            import base64
            import cv2
            from io import BytesIO
            from PIL import Image

            # Decode base64
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_bytes))

            # Convert to numpy array (RGB)
            image_np = np.array(image)

            # Convert RGB to BGR for OpenCV if needed
            if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                # Already RGB, good for our model
                pass

            return self.segment(image_np)

        except Exception as e:
            return SegmentationResult(
                success=False,
                error_message=f"Base64 decoding error: {e}"
            )


# Global segmenter instance for easy access
_segmenter_instance: Optional[BlackBoxSegmenter] = None


def get_black_box_segmenter(mock_mode: bool = False) -> BlackBoxSegmenter:
    """
    Get or create global black box segmenter instance.

    Args:
        mock_mode: Whether to use mock mode

    Returns:
        BlackBoxSegmenter instance
    """
    global _segmenter_instance
    if _segmenter_instance is None:
        _segmenter_instance = BlackBoxSegmenter(mock_mode=mock_mode)
    return _segmenter_instance


async def segment_black_boxes(image_data: np.ndarray, mock_mode: bool = False) -> SegmentationResult:
    """
    Convenience function to segment black boxes.

    Args:
        image_data: Input image as numpy array
        mock_mode: Whether to use mock mode

    Returns:
        SegmentationResult
    """
    segmenter = get_black_box_segmenter(mock_mode)
    return segmenter.segment(image_data)