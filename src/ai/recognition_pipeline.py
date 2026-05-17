# src/ai/recognition_pipeline.py
import numpy as np
from src.ai.detector import FaceDetector, FaceNotDetectedException, MultipleFacesException
from src.ai.embedder import FaceEmbedder
from src.ai.anti_spoofing import AntiSpoofing
from src.core.vector_index import VectorIndex
from src.core.config import settings


# ── Result classes ────────────────────────────────────────────────────────────

class RecognitionResult:
    """
    Returned by RecognitionPipeline.recognize() on success.

    student_id  — who was recognized (maps to PostgreSQL students.id)
    confidence  — how confident we are (0.0 to 1.0, higher = more confident)
    """
    def __init__(self, student_id: int, confidence: float):
        self.student_id = student_id
        self.confidence = confidence


class RecognitionFailure:
    """
    Returned by RecognitionPipeline.recognize() when recognition fails.

    reason — human-readable explanation of why recognition failed
    """
    def __init__(self, reason: str):
        self.reason = reason


# ── Pipeline ──────────────────────────────────────────────────────────────────

class RecognitionPipeline:
    """
    Chains all 4 AI steps into a single recognize() call.

    Step 1 — FaceDetector:   find and crop the face from the image
    Step 2 — AntiSpoofing:   verify the face is real, not a photo
    Step 3 — FaceEmbedder:   convert face to 512-dim embedding
    Step 4 — VectorIndex:    search for the closest match in FAISS

    Usage:
        pipeline = RecognitionPipeline()
        result = pipeline.recognize(image)

        if isinstance(result, RecognitionResult):
            # success — mark attendance for result.student_id
        elif isinstance(result, RecognitionFailure):
            # failed — log result.reason
    """

    def __init__(self):
        self.detector  = FaceDetector()
        self.spoof     = AntiSpoofing()
        self.embedder  = FaceEmbedder()
        self.index     = VectorIndex(
            index_path=settings.FAISS_INDEX_PATH,
            id_map_path=settings.FAISS_ID_MAP_PATH,
        )

    def recognize(self, image: np.ndarray) -> RecognitionResult | RecognitionFailure:
        """
        Run the full recognition pipeline on an image.

        Args:
            image: BGR image as numpy array (from OpenCV)

        Returns:
            RecognitionResult  if a known student was recognized
            RecognitionFailure if any step failed
        """

        # ── Step 1: Detect face ───────────────────────────────────────────────
        try:
            face_crop = self.detector.detect(image)
        except FaceNotDetectedException:
            return RecognitionFailure("No face detected in the image.")
        except MultipleFacesException:
            return RecognitionFailure("Multiple faces detected. Only one person at a time.")

        # ── Step 2: Liveness check ────────────────────────────────────────────
        if not self.spoof.is_real(face_crop):
            return RecognitionFailure("Spoof attempt detected. Please use a real face.")

        # ── Step 3: Get embedding ─────────────────────────────────────────────
        # We pass the full image (not face_crop) because the embedder uses
        # InsightFace internally which does its own detection on the full image.
        try:
            embedding = self.embedder.get_embedding(image)
        except ValueError as e:
            return RecognitionFailure(f"Could not extract face embedding: {e}")

        # ── Step 4: Search FAISS ──────────────────────────────────────────────
        student_id = self.index.search(
            embedding=embedding,
            threshold=settings.SIMILARITY_THRESHOLD,
        )

        if student_id is None:
            return RecognitionFailure("Face not recognised. Student may not be registered.")

        # Convert L2 distance to a 0.0-1.0 confidence score
        # Lower distance = higher confidence
        confidence = self._distance_to_confidence(embedding)

        return RecognitionResult(student_id=student_id, confidence=confidence)

    def get_embedding_for_enrollment(self, image: np.ndarray) -> np.ndarray:
        """
        Used during student registration (not attendance marking).

        Runs only steps 1-3 (detect + spoof + embed) and returns
        the embedding so StudentService can store it in FAISS.

        Raises:
            FaceNotDetectedException
            MultipleFacesException
            ValueError (embedding failed)
            RuntimeError (spoof detected)
        """
        face_crop = self.detector.detect(image)

        if not self.spoof.is_real(face_crop):
            raise RuntimeError(
                "Spoof detected during enrollment. Please use a real face photo."
            )

        # We pass the full image (not face_crop) because the embedder uses
        # InsightFace internally which does its own detection on the full image.
        return self.embedder.get_embedding(image)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _distance_to_confidence(self, embedding: np.ndarray) -> float:
        """
        Convert L2 distance to a confidence score between 0.0 and 1.0.

        FAISS returns distance (lower = more similar).
        We want confidence (higher = more certain).

        Formula: confidence = 1 - (distance / threshold)
        Clipped to [0.0, 1.0] range.

        Example:
            distance=0.1, threshold=0.8 → confidence = 0.875
            distance=0.7, threshold=0.8 → confidence = 0.125
        """
        distances, _ = self.index.index.search(
            embedding.astype(np.float32).reshape(1, 512), k=1
        )
        distance = float(distances[0][0])
        confidence = 1.0 - (distance / settings.SIMILARITY_THRESHOLD)
        return round(float(np.clip(confidence, 0.0, 1.0)), 4)