# src/ai/embedder.py
import numpy as np
from insightface.app import FaceAnalysis


class FaceEmbedder:
    """
    Wrapper around ArcFace (InsightFace buffalo_l model).

    Converts a face image into a 512-dimensional embedding.
    The embedding is a numeric "fingerprint" of the face.

    Same person      → embeddings are close to each other (low L2 distance)
    Different people → embeddings are far apart (high L2 distance)

    Why buffalo_l?
        - Best accuracy in the InsightFace model zoo
        - 512-dim embeddings (good balance of accuracy vs storage)
        - Works well across different lighting and angles

    Important:
        This embedder receives the FULL image (not a cropped face).
        InsightFace handles face detection internally before extracting
        the embedding. Do NOT resize or crop before passing here.
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

    def get_embedding(self, image: np.ndarray) -> np.ndarray:
        """
        Convert a face image to a 512-dim embedding.

        Args:
            image: full BGR image as numpy array (from OpenCV).
                   InsightFace handles detection internally.
                   Do NOT pass a cropped face — pass the full image.

        Returns:
            Normalized 512-dimensional numpy array (float32)

        Raises:
            ValueError: if no face is detected in the image

        Why normalize?
            Normalization makes all embeddings the same length (magnitude = 1).
            This makes L2 distance comparisons more reliable and consistent
            regardless of the original image brightness or contrast.
        """
        faces = self.app.get(image)

        if not faces:
            raise ValueError(
                "ArcFace could not extract embedding from the image. "
                "Make sure the image contains a clear, visible face."
            )

        # Use the first detected face
        embedding = faces[0].embedding

        # Normalize to unit length
        # After normalization: np.linalg.norm(embedding) == 1.0
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.astype(np.float32)