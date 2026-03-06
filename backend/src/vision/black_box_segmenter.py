"""
Black Box Segmentation Module

This module provides black box segmentation for visual verification.
Phase 2: Mock implementation returning simulated detection results.
"""

import asyncio
import numpy as np
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field


class SegmentationResult(BaseModel):
    """Result of black box segmentation."""
    success: bool = Field(..., description="Segmentation process success")
    bounding_boxes: List[Tuple[int, int, int, int]] = Field(default_factory=list,
                                                           description="List of [x1, y1, x2, y2] bounding boxes")
    confidence_scores: List[float] = Field(default_factory=list,
                                          description="Confidence scores for each bounding box")
    error_message: Optional[str] = Field(None, description="Error message if segmentation failed")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class BlackBoxSegmenter:
    """
    Black box segmentation for detecting text labels in images.

    Phase 2: Mock implementation that simulates black box detection.
    Returns simulated bounding boxes for development and testing.
    """

    def __init__(self, mock_mode: bool = True):
        """
        Initialize black box segmenter.

        Args:
            mock_mode: If True, use mock detection (always True for Phase 2)
        """
        self.mock_mode = mock_mode
        print("[BlackBoxSegmenter] Initialized in mock mode")

    async def segment(self, image_data: np.ndarray) -> SegmentationResult:
        """
        Segment black boxes in an image.

        Args:
            image_data: Input image as numpy array (H, W, C) in RGB format

        Returns:
            SegmentationResult with detected bounding boxes
        """
        import time
        start_time = time.time()

        # Simulate processing delay
        await asyncio.sleep(0.15)

        try:
            height, width = image_data.shape[:2]

            # Mock detection logic
            # In real implementation, this would use computer vision algorithms
            # to detect dark/black rectangular regions (text labels)

            bounding_boxes = []
            confidence_scores = []

            # Always detect at least one box in the center (simulating main text label)
            box_width = width // 3
            box_height = height // 6
            center_x = width // 2 - box_width // 2
            center_y = height // 2 - box_height // 2

            bounding_boxes.append((center_x, center_y, center_x + box_width, center_y + box_height))
            confidence_scores.append(0.92)

            # Randomly add 0-2 additional boxes (simulating secondary labels)
            import random
            num_additional = random.randint(0, 2)

            for i in range(num_additional):
                # Random position and size
                box_w = random.randint(width // 8, width // 4)
                box_h = random.randint(height // 12, height // 8)
                pos_x = random.randint(width // 8, width - box_w - width // 8)
                pos_y = random.randint(height // 8, height - box_h - height // 8)

                bounding_boxes.append((pos_x, pos_y, pos_x + box_w, pos_y + box_h))
                confidence_scores.append(random.uniform(0.65, 0.85))

            processing_time = (time.time() - start_time) * 1000

            return SegmentationResult(
                success=True,
                bounding_boxes=bounding_boxes,
                confidence_scores=confidence_scores,
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return SegmentationResult(
                success=False,
                error_message=f"Segmentation error: {e}",
                processing_time_ms=processing_time
            )

    async def segment_base64(self, image_base64: str) -> SegmentationResult:
        """
        Segment black boxes from base64 encoded image.

        Args:
            image_base64: Base64 encoded image string

        Returns:
            SegmentationResult with detected bounding boxes
        """
        import time
        start_time = time.time()

        # Simulate processing delay
        await asyncio.sleep(0.2)

        try:
            # In mock mode, we don't actually decode the image
            # Just simulate detection based on expected characteristics

            # Mock image dimensions (typical camera resolution)
            mock_width = 640
            mock_height = 480

            # Generate mock bounding boxes
            bounding_boxes = []
            confidence_scores = []

            # Main box
            box_width = mock_width // 3
            box_height = mock_height // 6
            center_x = mock_width // 2 - box_width // 2
            center_y = mock_height // 2 - box_height // 2

            bounding_boxes.append((center_x, center_y, center_x + box_width, center_y + box_height))
            confidence_scores.append(0.91)

            # Possibly a secondary box
            import random
            if random.random() > 0.4:  # 60% chance
                small_box_width = mock_width // 5
                small_box_height = mock_height // 9
                small_x = mock_width // 4 - small_box_width // 2
                small_y = mock_height // 3 - small_box_height // 2

                bounding_boxes.append((small_x, small_y,
                                      small_x + small_box_width, small_y + small_box_height))
                confidence_scores.append(0.76)

            processing_time = (time.time() - start_time) * 1000

            return SegmentationResult(
                success=True,
                bounding_boxes=bounding_boxes,
                confidence_scores=confidence_scores,
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return SegmentationResult(
                success=False,
                error_message=f"Base64 segmentation error: {e}",
                processing_time_ms=processing_time
            )


# Global segmenter instance for easy access
_segmenter_instance: Optional[BlackBoxSegmenter] = None


async def get_black_box_segmenter(mock_mode: bool = True) -> BlackBoxSegmenter:
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


async def segment_black_boxes(image_data: np.ndarray, mock_mode: bool = True) -> SegmentationResult:
    """
    Convenience function to segment black boxes.

    Args:
        image_data: Input image as numpy array
        mock_mode: Whether to use mock mode

    Returns:
        SegmentationResult
    """
    segmenter = await get_black_box_segmenter(mock_mode)
    return await segmenter.segment(image_data)


async def segment_black_boxes_base64(image_base64: str, mock_mode: bool = True) -> SegmentationResult:
    """
    Convenience function to segment black boxes from base64 image.

    Args:
        image_base64: Base64 encoded image string
        mock_mode: Whether to use mock mode

    Returns:
        SegmentationResult
    """
    segmenter = await get_black_box_segmenter(mock_mode)
    return await segmenter.segment_base64(image_base64)