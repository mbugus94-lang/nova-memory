"""
Nova Memory 2.0 — Real-Time Fine-Tuning Engine

Implements lightweight in-process learning:
- Cosine-similarity memory retrieval using numpy (no heavy ML deps required)
- Optional PyTorch neural fine-tuning when torch is available
- Graceful fallback to numpy-only mode when torch is not installed
- Interaction history tracking with performance metrics

The engine is intentionally dependency-light so it works in any Python 3.9+
environment.  Install torch separately to unlock the neural fine-tuning path.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional torch import — graceful fallback
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    logger.info(
        "PyTorch not installed — FineTuningEngine will run in numpy-only mode. "
        "Install torch to enable neural fine-tuning."
    )


# ---------------------------------------------------------------------------
# Numpy-only embedding helpers
# ---------------------------------------------------------------------------

def _embed_text_numpy(text: str, hidden_size: int = 128) -> np.ndarray:
    """
    Produce a deterministic pseudo-embedding from raw text.

    Uses character n-gram hashing into a fixed-size float32 vector.
    This is intentionally simple — replace with a real sentence encoder
    (e.g. sentence-transformers) for production use.
    """
    words = text.lower().split()
    embedding = np.zeros(hidden_size, dtype=np.float32)
    for word in words:
        idx = abs(hash(word)) % hidden_size
        embedding[idx] += 1.0
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding /= norm
    return embedding


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity between two vectors."""
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-10
    return float(np.dot(a, b) / denom)


# ---------------------------------------------------------------------------
# Neural model (only instantiated when torch is available)
# ---------------------------------------------------------------------------

def _build_torch_model(config: Dict) -> "nn.Module":
    """Build a small transformer-style memory network."""

    class MemoryNetwork(nn.Module):
        def __init__(self, cfg):
            super().__init__()
            h = cfg["hidden_size"]
            self.input_proj = nn.Linear(h, h)
            self.layers = nn.ModuleList([
                nn.TransformerEncoderLayer(
                    d_model=h,
                    nhead=min(4, h // 32) or 1,
                    dim_feedforward=h * 4,
                    dropout=cfg["dropout"],
                    batch_first=True,
                )
                for _ in range(cfg["num_layers"])
            ])
            self.output = nn.Linear(h, 1)

        def forward(self, x):
            x = self.input_proj(x)
            for layer in self.layers:
                x = layer(x)
            x = x.mean(dim=1)
            return self.output(x)

    return MemoryNetwork(config)


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class FineTuningEngine:
    """
    Real-time fine-tuning engine for AI agent interactions.

    In *numpy mode* (default when torch is absent) the engine stores
    embeddings and retrieves memories via cosine similarity without any
    gradient updates.

    In *torch mode* (when torch is installed) the engine additionally
    performs online gradient descent on a small transformer network,
    adjusting weights based on user feedback signals.
    """

    _MODEL_CONFIGS = {
        "small":  {"hidden_size": 128, "num_layers": 2, "dropout": 0.1},
        "medium": {"hidden_size": 256, "num_layers": 3, "dropout": 0.2},
        "large":  {"hidden_size": 512, "num_layers": 4, "dropout": 0.3},
    }

    def __init__(self, model_size: str = "small"):
        if model_size not in self._MODEL_CONFIGS:
            raise ValueError(f"model_size must be one of {list(self._MODEL_CONFIGS)}")

        self.model_size = model_size
        self.config = self._MODEL_CONFIGS[model_size]
        self.hidden_size: int = self.config["hidden_size"]

        # Memory store (shared between numpy and torch modes)
        self.memory_texts: List[Dict] = []
        self.memory_embeddings: List[np.ndarray] = []
        self.training_history: List[Dict] = []

        # Torch components (None when torch unavailable)
        self._model = None
        self._optimizer = None
        self._device = None

        if _TORCH_AVAILABLE:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._model = _build_torch_model(self.config).to(self._device)
            self._optimizer = optim.Adam(self._model.parameters(), lr=1e-3)
            logger.info("FineTuningEngine: torch mode  device=%s", self._device)
        else:
            logger.info("FineTuningEngine: numpy-only mode")

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> np.ndarray:
        """Return a fixed-size float32 embedding for the given text."""
        return _embed_text_numpy(text, self.hidden_size)

    # ------------------------------------------------------------------
    # Memory storage / retrieval
    # ------------------------------------------------------------------

    def store_memory(
        self, text: str, metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add a text snippet to the in-memory store.

        Returns a dict with ``id`` and ``text``.
        """
        mem_id = f"mem_{len(self.memory_texts)}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        embedding = self.embed_text(text)
        self.memory_embeddings.append(embedding)
        self.memory_texts.append({
            "id": mem_id,
            "text": text,
            "embedding": embedding.tolist(),
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        })
        return {"id": mem_id, "text": text}

    def retrieve_memories(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve the top-k most relevant memories for a query.

        Uses cosine similarity over stored embeddings.
        """
        if not self.memory_embeddings:
            return []

        query_emb = self.embed_text(query)
        scored: List[Tuple[int, float]] = [
            (i, _cosine_similarity(query_emb, emb))
            for i, emb in enumerate(self.memory_embeddings)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [self.memory_texts[i] for i, _ in scored[:top_k]]

    # ------------------------------------------------------------------
    # Fine-tuning
    # ------------------------------------------------------------------

    def fine_tune_on_interaction(self, interaction_data: Dict) -> Dict:
        """
        Update the model on a single interaction.

        Args:
            interaction_data: dict with keys:
                - ``user_message`` (str)
                - ``agent_response`` (str)
                - ``user_feedback`` (str | None): ``"positive"``, ``"negative"``, or ``None``

        Returns:
            Training statistics dict.
        """
        user_msg: str = interaction_data.get("user_message", "")
        agent_resp: str = interaction_data.get("agent_response", "")
        feedback: Optional[str] = interaction_data.get("user_feedback")

        if _TORCH_AVAILABLE and self._model is not None:
            loss_val = self._torch_update(user_msg, agent_resp, feedback)
        else:
            # Numpy-only: simulate a loss based on embedding similarity
            u_emb = self.embed_text(user_msg)
            r_emb = self.embed_text(agent_resp)
            sim = _cosine_similarity(u_emb, r_emb)
            target = 1.0 if feedback == "positive" else (0.0 if feedback == "negative" else 0.5)
            loss_val = float(abs(target - sim))

        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "loss": round(loss_val, 6),
            "model_size": self.model_size,
            "mode": "torch" if _TORCH_AVAILABLE else "numpy",
            "interaction_count": len(self.training_history) + 1,
        }
        self.training_history.append(stats)

        # Persist model state if torch is available
        if _TORCH_AVAILABLE:
            self.save_model()

        return stats

    def _torch_update(
        self, user_msg: str, agent_resp: str, feedback: Optional[str]
    ) -> float:
        """Perform one gradient step and return the scalar loss."""
        assert _TORCH_AVAILABLE and self._model is not None

        target_val = 1.0 if feedback == "positive" else (0.0 if feedback == "negative" else 1.0)
        target = torch.tensor([[target_val]], dtype=torch.float32, device=self._device)

        user_emb = self.embed_text(user_msg)
        inp = torch.tensor(user_emb, dtype=torch.float32, device=self._device)
        inp = inp.unsqueeze(0).unsqueeze(0)  # (1, 1, hidden_size)

        self._model.zero_grad()
        output = self._model(inp)
        loss = nn.MSELoss()(output, target)
        loss.backward()
        self._optimizer.step()

        return float(loss.item())

    def fine_tune_batch(self, interactions: List[Dict]) -> Dict:
        """Fine-tune on a list of interactions and return aggregate stats."""
        if not interactions:
            return {"avg_loss": 0.0, "num_interactions": 0}

        losses = [self.fine_tune_on_interaction(i)["loss"] for i in interactions]
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "avg_loss": round(float(np.mean(losses)), 6),
            "min_loss": round(float(np.min(losses)), 6),
            "max_loss": round(float(np.max(losses)), 6),
            "num_interactions": len(interactions),
            "model_size": self.model_size,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_model(self, path: Optional[str] = None):
        """Save model state and memory to disk."""
        save_path = Path(path or "models/nova_memory_2.0_finetuned.pt")
        save_path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint: Dict = {
            "config": self.config,
            "training_history": self.training_history,
            "memory_texts": self.memory_texts,
            "memory_embeddings": [e.tolist() for e in self.memory_embeddings],
        }

        if _TORCH_AVAILABLE and self._model is not None:
            checkpoint["model_state_dict"] = self._model.state_dict()
            torch.save(checkpoint, save_path)
        else:
            # Save as JSON when torch is unavailable
            json_path = save_path.with_suffix(".json")
            with open(json_path, "w") as fh:
                json.dump(checkpoint, fh)

    def load_model(self, path: str):
        """Load model state and memory from disk."""
        load_path = Path(path)

        if load_path.suffix == ".json" or not _TORCH_AVAILABLE:
            json_path = load_path.with_suffix(".json")
            if json_path.exists():
                with open(json_path) as fh:
                    checkpoint = json.load(fh)
            else:
                logger.warning("Model file not found: %s", json_path)
                return
        else:
            checkpoint = torch.load(load_path, map_location=self._device)
            if "model_state_dict" in checkpoint and self._model is not None:
                self._model.load_state_dict(checkpoint["model_state_dict"])

        self.config = checkpoint.get("config", self.config)
        self.training_history = checkpoint.get("training_history", [])
        self.memory_texts = checkpoint.get("memory_texts", [])
        self.memory_embeddings = [
            np.array(e, dtype=np.float32)
            for e in checkpoint.get("memory_embeddings", [])
        ]
        print(f"[OK] Model loaded  iterations={len(self.training_history)}  "
              f"memories={len(self.memory_texts)}")

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def get_performance_metrics(self) -> Dict:
        """Return a summary of training performance."""
        if not self.training_history:
            return {
                "status": "no_training_data",
                "total_iterations": 0,
                "num_memories": len(self.memory_texts),
            }

        recent = self.training_history[-100:]
        losses = [h["loss"] for h in recent]

        return {
            "status": "training_active",
            "mode": "torch" if _TORCH_AVAILABLE else "numpy",
            "total_iterations": len(self.training_history),
            "recent_loss": round(recent[-1]["loss"], 6),
            "avg_loss_100": round(float(np.mean(losses)), 6),
            "min_loss_100": round(float(np.min(losses)), 6),
            "model_size": self.model_size,
            "num_memories": len(self.memory_texts),
        }


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Nova Memory 2.0 — Real-Time Fine-Tuning Engine")
    print("=" * 60)
    print(f"Torch available: {_TORCH_AVAILABLE}")

    engine = FineTuningEngine(model_size="small")

    # Store memories
    for text in [
        "Patient John Doe has diabetes type 2",
        "Insulin dosage: 10 units twice daily",
        "Last HbA1c: 6.8% — good control",
    ]:
        engine.store_memory(text)

    # Retrieve
    results = engine.retrieve_memories("insulin dosage", top_k=2)
    print(f"\nTop-2 memories for 'insulin dosage':")
    for r in results:
        print(f"  {r['text']}")

    # Fine-tune
    stats = engine.fine_tune_on_interaction({
        "user_message": "What is the patient's current treatment?",
        "agent_response": "Patient takes insulin twice daily.",
        "user_feedback": "positive",
    })
    print(f"\nFine-tune stats: loss={stats['loss']}  mode={stats['mode']}")

    # Metrics
    metrics = engine.get_performance_metrics()
    print(f"Metrics: {metrics}")

    print("\n[OK] Fine-tuning engine smoke test complete")
