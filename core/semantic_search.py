"""
Semantic Memory Search
Enables finding memories by semantic similarity using embeddings
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Semantic search using sentence embeddings"""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        enabled: bool = True,
    ):
        """
        Initialize semantic search engine

        Args:
            model_name: Name of the embedding model to use
            enabled: Whether to enable semantic search
        """
        self.enabled = enabled and EMBEDDINGS_AVAILABLE
        self.model = None
        self.embeddings_cache = {}

        if not self.enabled:
            logger.warning("Semantic search disabled - install sentence-transformers")
            return

        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.enabled = False

    def embed(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self.enabled or not self.model:
            return None

        try:
            # Check cache first
            if text in self.embeddings_cache:
                return self.embeddings_cache[text]

            embedding = self.model.encode(text, convert_to_tensor=False)

            # Cache the embedding
            self.embeddings_cache[text] = embedding.tolist()

            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return None

    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for multiple texts"""
        if not self.enabled or not self.model:
            return None

        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            result = [emb.tolist() for emb in embeddings]

            # Cache embeddings
            for text, embedding in zip(texts, result):
                self.embeddings_cache[text] = embedding

            return result
        except Exception as e:
            logger.error(f"Error encoding batch: {e}")
            return None

    def semantic_search(
        self,
        query: str,
        memories: List[Dict[str, Any]],
        top_k: int = 5,
        score_threshold: float = 0.3,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search memories by semantic similarity

        Args:
            query: Search query text
            memories: List of memory dictionaries with 'content' field
            top_k: Number of top results to return
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of (memory, score) tuples sorted by score
        """
        if not self.enabled or not self.model:
            return []

        try:
            query_embedding = self.embed(query)
            if query_embedding is None:
                return []

            # Embed all memories
            memory_texts = [m.get("content", "") for m in memories]
            memory_embeddings = self.embed_batch(memory_texts)

            if memory_embeddings is None:
                return []

            # Calculate similarities
            import numpy as np
            query_emb = np.array(query_embedding)
            similarities = []

            for i, emb in enumerate(memory_embeddings):
                memory_emb = np.array(emb)
                # Cosine similarity
                similarity = float(np.dot(query_emb, memory_emb) /
                                 (np.linalg.norm(query_emb) * np.linalg.norm(memory_emb)))

                if similarity >= score_threshold:
                    similarities.append((i, similarity))

            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            results = []

            for idx, score in similarities[:top_k]:
                results.append((memories[idx], score))

            logger.info(f"Semantic search found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def find_similar_memories(
        self,
        memory: Dict[str, Any],
        all_memories: List[Dict[str, Any]],
        exclude_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find memories similar to a given memory

        Args:
            memory: The reference memory
            all_memories: All memories to search
            exclude_id: Memory ID to exclude (usually the query memory itself)
            top_k: Number of results to return

        Returns:
            List of (memory, score) tuples
        """
        # Filter out the excluded memory
        if exclude_id:
            search_memories = [m for m in all_memories
                             if m.get("id") != exclude_id]
        else:
            search_memories = all_memories

        return self.semantic_search(
            memory.get("content", ""),
            search_memories,
            top_k=top_k,
        )

    def cluster_memories(
        self,
        memories: List[Dict[str, Any]],
        num_clusters: int = 5,
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Cluster memories by semantic similarity

        Args:
            memories: Memories to cluster
            num_clusters: Number of clusters

        Returns:
            Dictionary mapping cluster ID to list of memories
        """
        if not self.enabled or not self.model or len(memories) < num_clusters:
            return {0: memories}

        try:
            from sklearn.cluster import KMeans
            import numpy as np

            # Embed all memories
            memory_texts = [m.get("content", "") for m in memories]
            embeddings = self.embed_batch(memory_texts)

            if embeddings is None:
                return {0: memories}

            # Cluster
            embeddings = np.array(embeddings)
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            labels = kmeans.fit_predict(embeddings)

            # Group memories by cluster
            clusters = {}
            for memory, label in zip(memories, labels):
                label = int(label)
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(memory)

            logger.info(f"Clustered {len(memories)} memories into {len(clusters)} clusters")
            return clusters

        except ImportError:
            logger.warning("sklearn not available for clustering")
            return {0: memories}
        except Exception as e:
            logger.error(f"Error clustering memories: {e}")
            return {0: memories}

    def clear_cache(self):
        """Clear the embeddings cache"""
        self.embeddings_cache.clear()
        logger.info("Embeddings cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "enabled": self.enabled,
            "cached_embeddings": len(self.embeddings_cache),
            "model_loaded": self.model is not None,
        }


# Singleton instance
_search_engine: Optional[SemanticSearchEngine] = None


def get_semantic_search() -> SemanticSearchEngine:
    """Get or create semantic search engine"""
    global _search_engine
    if _search_engine is None:
        _search_engine = SemanticSearchEngine()
    return _search_engine


def init_semantic_search(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> SemanticSearchEngine:
    """Initialize global semantic search engine"""
    global _search_engine
    _search_engine = SemanticSearchEngine(model_name=model_name)
    return _search_engine
