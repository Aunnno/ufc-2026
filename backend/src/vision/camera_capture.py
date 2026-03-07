"""
Camera Capture Module

This module provides camera capture functionality for visual verification.
Backend captures images from server-connected camera using OpenCV (cv2.VideoCapture).
Currently implements mock capture for Phase 2 development; real camera integration planned for Phase 3+.
"""

import base64
from typing import Optional
from pydantic import BaseModel


class CameraCaptureResult(BaseModel):
    """Result of camera capture operation."""
    success: bool
    image_data: Optional[str] = None  # Base64 encoded image data
    error_message: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class CameraCapture:
    """Camera capture interface for visual verification."""

    def __init__(self, mock_mode: bool = True):
        """
        Initialize camera capture.

        Args:
            mock_mode: If True, use mock images instead of real camera.
        """
        self.mock_mode = mock_mode
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize camera hardware."""
        if self.mock_mode:
            print("[CameraCapture] Using mock camera mode")
            self._initialized = True
            return True

        # TODO: Real camera initialization
        print("[CameraCapture] Real camera initialization not implemented")
        self._initialized = False
        return False

    async def capture_image(self) -> CameraCaptureResult:
        """
        Capture a single image from camera.

        Returns:
            CameraCaptureResult with image data or error.
        """
        if not self._initialized:
            init_success = await self.initialize()
            if not init_success:
                return CameraCaptureResult(
                    success=False,
                    error_message="Camera initialization failed"
                )

        if self.mock_mode:
            # Return a mock base64 encoded image (small 1x1 pixel black PNG)
            mock_image_base64 = (
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            )
            return CameraCaptureResult(
                success=True,
                image_data=mock_image_base64,
                width=1,
                height=1
            )

        # TODO: Real camera capture
        return CameraCaptureResult(
            success=False,
            error_message="Real camera capture not implemented"
        )

    async def capture_multiple(self, count: int = 3) -> list[CameraCaptureResult]:
        """
        Capture multiple images in sequence.

        Args:
            count: Number of images to capture

        Returns:
            List of CameraCaptureResult objects
        """
        results = []
        for i in range(count):
            result = await self.capture_image()
            results.append(result)
        return results

    async def cleanup(self):
        """Clean up camera resources."""
        if self._initialized:
            print("[CameraCapture] Cleaning up camera resources")
            self._initialized = False


# Global camera instance for easy access
_camera_instance: Optional[CameraCapture] = None


async def get_camera_capture(mock_mode: bool = True) -> CameraCapture:
    """
    Get or create global camera capture instance.

    Args:
        mock_mode: Whether to use mock mode

    Returns:
        CameraCapture instance
    """
    global _camera_instance
    if _camera_instance is None:
        _camera_instance = CameraCapture(mock_mode=mock_mode)
        await _camera_instance.initialize()
    return _camera_instance


async def capture_single_image(mock_mode: bool = True) -> CameraCaptureResult:
    """
    Convenience function to capture a single image.

    Args:
        mock_mode: Whether to use mock mode

    Returns:
        CameraCaptureResult
    """
    camera = await get_camera_capture(mock_mode)
    return await camera.capture_image()