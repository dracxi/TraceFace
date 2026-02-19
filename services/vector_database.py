"""FAISS vector database wrapper."""
import faiss
import numpy as np
from typing import List, Tuple, Optional
import os
import logging
from config import settings
import pickle

logger = logging.getLogger(__name__)


class VectorDatabase:
    """FAISS index wrapper for face embeddings."""
    
    def __init__(self, dimension: int = 512, index_path: str = None):
        """
        Initialize vector database.
        
        Args:
            dimension: Embedding dimension
            index_path: Path to save/load index
        """
        self.dimension = dimension
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.index = None
        self.id_map = {}  # Maps FAISS index to (person_id, photo_id)
        self.reverse_map = {}  # Maps (person_id, photo_id) to FAISS index
        self.next_id = 0
        
        # Create index
        self._create_index()
        
        # Try to load existing index
        self.load_index()
    
    def _create_index(self):
        """Create FAISS index."""
        # Use IndexFlatIP for exact cosine similarity search (inner product)
        self.index = faiss.IndexFlatIP(self.dimension)
        logger.info(f"Created FAISS IndexFlatIP with dimension {self.dimension}")
    
    def add_embedding(
        self, 
        person_id: str, 
        photo_id: str, 
        embedding: np.ndarray
    ) -> bool:
        """
        Add embedding to index.
        
        Args:
            person_id: Person UUID
            photo_id: Photo UUID
            embedding: Embedding vector (512,)
        
        Returns:
            Success status
        """
        try:
            # Ensure embedding is normalized and correct shape
            embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)
            embedding = embedding / np.linalg.norm(embedding)
            
            # Add to index
            self.index.add(embedding)
            
            # Update mappings
            key = (str(person_id), str(photo_id))
            self.id_map[self.next_id] = key
            self.reverse_map[key] = self.next_id
            self.next_id += 1
            
            logger.info(f"Added embedding for person {person_id}, photo {photo_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add embedding: {e}")
            return False
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 10, 
        threshold: float = 0.6
    ) -> List[Tuple[str, str, float]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold
        
        Returns:
            List of (person_id, photo_id, similarity_score) tuples
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("Index is empty")
                return []
            
            logger.info(f"Searching index with {self.index.ntotal} embeddings")
            
            # Normalize query embedding
            query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
            query_norm = np.linalg.norm(query_embedding)
            logger.info(f"Query embedding norm before normalization: {query_norm}")
            query_embedding = query_embedding / query_norm
            
            # Search
            k_search = min(k, self.index.ntotal)
            distances, indices = self.index.search(query_embedding, k_search)
            
            logger.info(f"Search results - distances: {distances[0]}, indices: {indices[0]}")
            
            # Filter by threshold and format results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx in self.id_map:
                    person_id, photo_id = self.id_map[idx]
                    # Clamp similarity to [0, 1] to handle floating-point precision issues
                    similarity = min(1.0, max(0.0, float(dist)))
                    logger.info(f"Match: person_id={person_id}, photo_id={photo_id}, similarity={similarity}, threshold={threshold}")
                    if similarity >= threshold:
                        results.append((person_id, photo_id, similarity))
            
            # Sort by similarity descending
            results.sort(key=lambda x: x[2], reverse=True)
            
            logger.info(f"Found {len(results)} matches above threshold {threshold}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_embeddings(self, person_id: str) -> bool:
        """
        Delete all embeddings for a person.
        Note: FAISS doesn't support deletion, so we rebuild the index.
        
        Args:
            person_id: Person UUID
        
        Returns:
            Success status
        """
        try:
            person_id = str(person_id)
            
            # Find all indices for this person
            indices_to_remove = [
                idx for idx, (pid, _) in self.id_map.items() 
                if pid == person_id
            ]
            
            if not indices_to_remove:
                logger.warning(f"No embeddings found for person {person_id}")
                return True
            
            # Rebuild index without these embeddings
            self._rebuild_index_without(indices_to_remove)
            
            logger.info(f"Deleted {len(indices_to_remove)} embeddings for person {person_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embeddings: {e}")
            return False
    
    def _rebuild_index_without(self, indices_to_remove: List[int]):
        """Rebuild index excluding specified indices."""
        # Get all embeddings except those to remove
        all_embeddings = []
        new_id_map = {}
        new_reverse_map = {}
        new_id = 0
        
        for idx in range(self.index.ntotal):
            if idx not in indices_to_remove:
                # Reconstruct embedding
                embedding = self.index.reconstruct(idx)
                all_embeddings.append(embedding)
                
                # Update mappings
                key = self.id_map[idx]
                new_id_map[new_id] = key
                new_reverse_map[key] = new_id
                new_id += 1
        
        # Create new index
        self._create_index()
        
        if all_embeddings:
            embeddings_array = np.array(all_embeddings, dtype=np.float32)
            self.index.add(embeddings_array)
        
        self.id_map = new_id_map
        self.reverse_map = new_reverse_map
        self.next_id = new_id
    
    def get_index_size(self) -> int:
        """Get number of embeddings in index."""
        return self.index.ntotal
    
    def save_index(self):
        """Save index and mappings to disk."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save mappings
            mappings_path = self.index_path + '.mappings'
            with open(mappings_path, 'wb') as f:
                pickle.dump({
                    'id_map': self.id_map,
                    'reverse_map': self.reverse_map,
                    'next_id': self.next_id
                }, f)
            
            logger.info(f"Saved index to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def load_index(self):
        """Load index and mappings from disk."""
        try:
            if not os.path.exists(self.index_path):
                logger.info("No existing index found, starting fresh")
                return
            
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load mappings
            mappings_path = self.index_path + '.mappings'
            if os.path.exists(mappings_path):
                with open(mappings_path, 'rb') as f:
                    data = pickle.load(f)
                    self.id_map = data['id_map']
                    self.reverse_map = data['reverse_map']
                    self.next_id = data['next_id']
            
            logger.info(f"Loaded index from {self.index_path} with {self.index.ntotal} embeddings")
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            self._create_index()


# Global vector database instance
vector_db = VectorDatabase()
