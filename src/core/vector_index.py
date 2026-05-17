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
    """

    EMBEDDING_DIM = 512

    def __init__(self, index_path: str, id_map_path: str):
        self.index_path = index_path
        self.id_map_path = id_map_path
        self.id_map: dict[int, int] = {}

        # Load from disk if files exist AND are valid
        # If files are corrupted/empty, start fresh instead of crashing
        if os.path.exists(index_path) and os.path.exists(id_map_path):
            try:
                self._load()
                print(f"VectorIndex loaded: {self.index.ntotal} embeddings")
            except Exception as e:
                print(f"WARNING: Could not load FAISS index ({e}). Starting fresh.")
                self._init_fresh()
        else:
            self._init_fresh()

    def _init_fresh(self) -> None:
        """Start with an empty index — no students registered yet."""
        self.index = faiss.IndexFlatL2(self.EMBEDDING_DIM)
        self.id_map = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, student_id: int, embedding: np.ndarray) -> None:
        """Add a student's face embedding to the index."""
        embedding = self._prepare(embedding)
        position = self.index.ntotal
        self.index.add(embedding)
        self.id_map[position] = student_id
        self._save()

    def search(
        self, embedding: np.ndarray, threshold: float
    ) -> tuple[int | None, float]:
        """
        Find the closest student to the given embedding.
        Returns (student_id, distance) if distance <= threshold.
        Returns (None, distance) if no match found or index is empty.
        """
        if self.index.ntotal == 0:
            return None, 0.0

        embedding = self._prepare(embedding)
        distances, positions = self.index.search(embedding, k=1)

        distance = float(distances[0][0])
        position = int(positions[0][0])

        if distance > threshold:
            return None, distance

        return self.id_map.get(position), distance

    def remove(self, student_id: int) -> bool:
        """
        Remove ALL embeddings for a student from the index.
        FAISS IndexFlatL2 doesn't support deletion — we rebuild the index.
        Returns True if found and removed, False if not found.
        """
        positions_to_remove = [
            pos for pos, sid in self.id_map.items() if sid == student_id
        ]

        if not positions_to_remove:
            return False

        all_embeddings = self.index.reconstruct_n(0, self.index.ntotal)
        mask = [i for i in range(self.index.ntotal) if i not in positions_to_remove]
        new_embeddings = all_embeddings[mask]

        new_id_map = {}
        new_pos = 0
        for old_pos in sorted(self.id_map.keys()):
            if old_pos in positions_to_remove:
                continue
            new_id_map[new_pos] = self.id_map[old_pos]
            new_pos += 1

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
        """FAISS requires float32 dtype and shape (1, 512)."""
        return embedding.astype(np.float32).reshape(1, self.EMBEDDING_DIM)

    def _save(self) -> None:
        """Persist the index and id_map to disk after every change."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.id_map_path, "w") as f:
            json.dump({str(k): v for k, v in self.id_map.items()}, f)

    def _load(self) -> None:
        """
        Load the index and id_map from disk.
        Raises an exception if files are corrupted or empty —
        caller (__init__) catches this and starts fresh.
        """
        # Check file is not empty before reading
        if os.path.getsize(self.index_path) == 0:
            raise ValueError("face_index.faiss is empty")
        if os.path.getsize(self.id_map_path) == 0:
            raise ValueError("face_id_map.json is empty")

        self.index = faiss.read_index(self.index_path)
        with open(self.id_map_path, "r") as f:
            raw = json.load(f)
            self.id_map = {int(k): v for k, v in raw.items()}