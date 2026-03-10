# src/ai/embedder.py
import numpy as np
import insightface
from insightface.app import FaceAnalysis


class FaceEmbedder:
    """
    Wrapper around ArcFace (InsightFace buffalo_l model).

    Converts a cropped face image into a 512-dimensional embedding.
    The embedding is a numeric "fingerprint" of the face.

    Same person  → embeddings are close to each other (low L2 distance)
    Different people → embeddings are far apart (high L2 distance)

    Why buffalo_l?
        - Best accuracy in the InsightFace model zoo
        - 512-dim embeddings (good balance of accuracy vs storage)
        - Works well across different lighting and angles
    """

    def __init__(self):
        """
        Load the ArcFace model on startup.
        This takes a few seconds the first time — the model is downloaded
        and cached locally. Subsequent startups load from cache.

        ctx_id=-1 means use CPU. Set ctx_id=0 to use GPU if available.
        """
        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"]
        )
        # det_size is the image size passed to the detection model inside
        # InsightFace. (640, 640) is the recommended size for buffalo_l.
        self.app.prepare(ctx_id=-1, det_size=(640, 640))

    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """
        Convert a cropped face image to a 512-dim embedding.

        Args:
            face_crop: BGR image of the face (output from FaceDetector)

        Returns:
            Normalized 512-dimensional numpy array (float32)

        Raises:
            ValueError: if no face is detected in the crop
                        (shouldn't happen since detector already ran,
                         but we guard against edge cases)

        Why normalize?
            Normalization makes all embeddings the same length (magnitude = 1).
            This makes L2 distance comparisons more reliable and consistent
            regardless of the original image brightness or contrast.
        """
        faces = self.app.get(face_crop)

        if not faces:
            raise ValueError(
                "ArcFace could not extract embedding from the face crop. "
                "The crop may be too small or blurry."
            )

        # .embedding is a 512-dim numpy array
        embedding = faces[0].embedding

        # Normalize to unit length
        # After normalization: np.linalg.norm(embedding) == 1.0
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.astype(np.float32)