# src/ai/anti_spoofing.py
import os
import cv2
import numpy as np


class AntiSpoofing:
    """
    Liveness detection using Silent-Face Anti-Spoofing.

    Detects whether a face is real (live person) or fake (photo, screen, mask).

    Why do we need this?
        Without liveness detection, anyone can hold up a photo of a student
        in front of the camera and register their attendance fraudulently.

    How it works:
        The model was trained on thousands of real and fake face samples.
        It learned subtle differences:
            Real face  → has depth, natural skin texture, natural lighting
            Fake face  → flat, screen glow, printed texture, unnatural reflection

    Returns:
        True  → live face, continue with recognition
        False → spoof detected, reject the attempt
    """

    # Confidence threshold — above this score = real face
    # 0.8 means the model must be 80% confident it's a real face
    LIVENESS_THRESHOLD = 0.8

    def __init__(self):
        """
        The Silent-Face model is lightweight and loads quickly.
        It runs on CPU — no GPU needed.
        """
        # Model is loaded lazily on first use to speed up startup
        self._model = None

    def is_real(self, face_crop: np.ndarray) -> bool:
        """
        Check if the face is real (live) or fake (spoof).

        Args:
            face_crop: BGR image of the face (output from FaceDetector)

        Returns:
            True  if the face passes the liveness check
            False if the face is detected as a spoof attempt
        """
        score = self._get_liveness_score(face_crop)
        return score >= self.LIVENESS_THRESHOLD

    def _get_liveness_score(self, face_crop: np.ndarray) -> float:
        """
        Run the anti-spoofing model and return a confidence score.

        Score range: 0.0 to 1.0
            1.0 = definitely a real face
            0.0 = definitely a spoof

        The model expects the image resized to 80x80 pixels.
        This small size is intentional — the model looks at texture
        patterns, not fine details.
        """
        # Resize face to the size the model expects
        resized = cv2.resize(face_crop, (80, 80))

        # Normalize pixel values to [0, 1]
        normalized = resized.astype(np.float32) / 255.0

        # Add batch dimension: (80, 80, 3) → (1, 80, 80, 3)
        input_tensor = np.expand_dims(normalized, axis=0)

        # Load model on first use
        if self._model is None:
            self._model = self._load_model()

        # Run inference
        score = float(self._model.predict(input_tensor)[0][0])
        return score

    def _load_model(self):
        """
        Load the Silent-Face Anti-Spoofing model.

        The model file is expected at:
            src/ai/weights/anti_spoof_model.h5

        This file must be downloaded separately and placed in that path.
        See README for download instructions.
        """
        try:
            import tensorflow as tf
            weights_path = os.path.join(
                os.path.dirname(__file__),
                "weights",
                "anti_spoof_model.h5"
            )
            if not os.path.exists(weights_path):
                raise FileNotFoundError(
                    f"Anti-spoofing model not found at: {weights_path}\n"
                    "Please download the model weights and place them at that path.\n"
                    "See the README for download instructions."
                )
            return tf.keras.models.load_model(weights_path)
        except ImportError:
            raise ImportError(
                "TensorFlow is required for anti-spoofing. "
                "Install it with: pip install tensorflow"
            )