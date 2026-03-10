# src/ai/detector.py
import numpy as np
from retinaface import RetinaFace


# ── Custom exceptions ─────────────────────────────────────────────────────────

class FaceNotDetectedException(Exception):
    """Raised when no face is found in the image."""
    pass


class MultipleFacesException(Exception):
    """Raised when more than one face is found in the image."""
    pass


# ── Detector ──────────────────────────────────────────────────────────────────

class FaceDetector:
    """
    Wrapper around RetinaFace.

    Responsibilities:
        1. Detect faces in an image
        2. Enforce exactly one face per image
        3. Return the cropped face region for ArcFace

    Why RetinaFace?
        - Works well with small faces in the frame
        - Works well with non-frontal faces
        - Fast and accurate
        - Free and open source
    """

    def detect(self, image: np.ndarray) -> np.ndarray:
        """
        Detect exactly one face in the image and return the cropped region.

        Args:
            image: BGR image as numpy array (from OpenCV)

        Returns:
            Cropped face region as numpy array

        Raises:
            FaceNotDetectedException:  no face found in the image
            MultipleFacesException:    more than one face found
        """
        # RetinaFace.detect_faces returns a dict like:
        # {
        #   "face_1": {
        #       "score": 0.99,
        #       "facial_area": [x1, y1, x2, y2],
        #       "landmarks": {...}
        #   }
        # }
        # Returns False if no face is found.
        faces = RetinaFace.detect_faces(image)

        if faces is False or len(faces) == 0:
            raise FaceNotDetectedException(
                "No face detected in the image. "
                "Make sure the face is clearly visible and well-lit."
            )

        if len(faces) > 1:
            raise MultipleFacesException(
                f"Multiple faces detected ({len(faces)}). "
                "Only one person should be in front of the camera."
            )

        # Extract the bounding box of the single detected face
        face_data = list(faces.values())[0]
        x1, y1, x2, y2 = face_data["facial_area"]

        # Add a small margin around the face for better recognition
        # ArcFace works better with a bit of context around the face
        margin = 10
        h, w = image.shape[:2]
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(w, x2 + margin)
        y2 = min(h, y2 + margin)

        # Crop and return the face region
        face_crop = image[y1:y2, x1:x2]
        return face_crop