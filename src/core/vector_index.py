# src/core/vector_index.py
import os
import json
import numpy as np
import faiss


class VectorIndex:
    """
    Wrapper around FAISS IndexFlatL2.

    Stores 512-dimensional face embeddings and maps each
    position in the index to a student_id in PostgreSQL.

    Two files are persisted to disk:
        face_index.faiss   — the FAISS index (binary)
        face_id_map.json   — {str(position): student_id}

    Why IndexFlatL2?
        L2 = Euclidean distance. Smaller distance = more similar faces.
        FlatL2 does an exact search (no approximation).
        Fast enough for thousands of students.
    """

    EMBEDDING_DIM = 512  # ArcFace buffalo_l produces 512-dim embeddings

    def __init__(self, index_path: str, id_map_path: str):
        self.index_path = index_path
        self.id_map_path = id_map_path

        # id_map: position (int) → student_id (int)
        # FAISS only knows positions (0, 1, 2 ...)
        # We use id_map to translate a position back to a student_id
        self.id_map: dict[int, int] = {}

        # Load from disk if files already exist, otherwise start fresh
        if os.path.exists(index_path) and os.path.exists(id_map_path):
            self._load()
        else:
            self.index = faiss.IndexFlatL2(self.EMBEDDING_DIM)

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, student_id: int, embedding: np.ndarray) -> None:
        """
        Add a student's face embedding to the index.
        Called once when the admin registers a new student.

        The student's position in the index = current index size before adding.
        We store that position → student_id in id_map.
        """
        embedding = self._prepare(embedding)

        position = self.index.ntotal  # next available position
        self.index.add(embedding)
        self.id_map[position] = student_id

        self._save()

    def search(self, embedding: np.ndarray, threshold: float) -> int | None:
        """
        Find the closest student to the given embedding.

        Returns student_id if distance <= threshold, None if no match found.
        None means the face is not recognised — mark as unknown.

        threshold comes from settings.SIMILARITY_THRESHOLD (.env)
        Lower threshold = stricter matching.
        """
        if self.index.ntotal == 0:
            return None  # Index is empty — no students registered yet

        embedding = self._prepare(embedding)

        # FAISS returns two arrays: distances and positions
        # k=1 means "find the 1 closest match"
        distances, positions = self.index.search(embedding, k=1)

        distance = float(distances[0][0])
        position = int(positions[0][0])

        if distance > threshold:
            return None  # Too far away — not a match

        return self.id_map.get(position)

    def remove(self, student_id: int) -> bool:
        """
        Remove a student's embedding from the index.
        Called when the admin deletes a student.

        FAISS IndexFlatL2 does not support deletion directly.
        We rebuild the entire index without the deleted student.

        Returns True if found and removed, False if not found.
        """
        # Find the position of this student_id in id_map
        position_to_remove = None
        for position, sid in self.id_map.items():
            if sid == student_id:
                position_to_remove = position
                break

        if position_to_remove is None:
            return False  # Student not found in index

        # Collect all embeddings except the one to remove
        all_embeddings = self.index.reconstruct_n(0, self.index.ntotal)
        new_embeddings = np.delete(all_embeddings, position_to_remove, axis=0)

        # Rebuild id_map with updated positions
        new_id_map = {}
        new_pos = 0
        for old_pos in sorted(self.id_map.keys()):
            if old_pos == position_to_remove:
                continue
            new_id_map[new_pos] = self.id_map[old_pos]
            new_pos += 1

        # Rebuild the FAISS index from scratch
        self.index = faiss.IndexFlatL2(self.EMBEDDING_DIM)
        if len(new_embeddings) > 0:
            self.index.add(new_embeddings.astype(np.float32))

        self.id_map = new_id_map
        self._save()
        return True

    def get_total(self) -> int:
        """Return the number of embeddings stored in the index."""
        return self.index.ntotal

    # ── Private helpers ───────────────────────────────────────────────────────

    def _prepare(self, embedding: np.ndarray) -> np.ndarray:
        """
        FAISS requires embeddings to be:
          - float32 dtype
          - shape (1, 512) — a 2D array with one row

        ArcFace returns shape (512,) — we reshape it here.
        """
        return embedding.astype(np.float32).reshape(1, self.EMBEDDING_DIM)

    def _save(self) -> None:
        """
        Persist the index and id_map to disk.
        Called after every add() and remove().

        Why save after every change?
        If the server crashes, we don't lose any enrollments.
        """
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)

        # JSON keys must be strings — convert int positions to str
        with open(self.id_map_path, "w") as f:
            json.dump({str(k): v for k, v in self.id_map.items()}, f)

    def _load(self) -> None:
        """
        Load the index and id_map from disk.
        Called once on startup if the files already exist.
        """
        self.index = faiss.read_index(self.index_path)

        with open(self.id_map_path, "r") as f:
            raw = json.load(f)
            # JSON keys are always strings — convert back to int
            self.id_map = {int(k): v for k, v in raw.items()}