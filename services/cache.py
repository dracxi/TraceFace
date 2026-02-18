"""Redis caching service for embeddings."""
import redis
import numpy as np
import hashlib
import json
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Redis cache for face embeddings."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)
            self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.redis_client = None
    
    def _generate_cache_key(self, person_id: str, photo_hash: str) -> str:
        """Generate cache key for embedding."""
        return f"embedding:{person_id}:{photo_hash}"
    
    def _compute_photo_hash(self, photo_bytes: bytes) -> str:
        """Compute hash of photo for cache key."""
        return hashlib.sha256(photo_bytes).hexdigest()[:16]
    
    def get_embedding(self, person_id: str, photo_hash: str) -> Optional[np.ndarray]:
        """
        Get cached embedding.
        
        Args:
            person_id: Person UUID
            photo_hash: Photo hash
        
        Returns:
            Cached embedding or None
        """
        if self.redis_client is None:
            return None
        
        try:
            key = self._generate_cache_key(person_id, photo_hash)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                # Deserialize embedding
                embedding_list = json.loads(cached_data)
                embedding = np.array(embedding_list, dtype=np.float32)
                logger.info(f"Cache hit for {key}")
                return embedding
            
            logger.debug(f"Cache miss for {key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None
    
    def set_embedding(
        self, 
        person_id: str, 
        photo_hash: str, 
        embedding: np.ndarray,
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """
        Cache embedding.
        
        Args:
            person_id: Person UUID
            photo_hash: Photo hash
            embedding: Embedding vector
            ttl: Time to live in seconds
        
        Returns:
            Success status
        """
        if self.redis_client is None:
            return False
        
        try:
            key = self._generate_cache_key(person_id, photo_hash)
            
            # Serialize embedding
            embedding_list = embedding.tolist()
            cached_data = json.dumps(embedding_list)
            
            # Set with TTL
            self.redis_client.setex(key, ttl, cached_data)
            logger.info(f"Cached embedding for {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    def invalidate_person(self, person_id: str) -> bool:
        """
        Invalidate all cache entries for a person.
        
        Args:
            person_id: Person UUID
        
        Returns:
            Success status
        """
        if self.redis_client is None:
            return False
        
        try:
            # Find all keys for this person
            pattern = f"embedding:{person_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for person {person_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cached embeddings."""
        if self.redis_client is None:
            return False
        
        try:
            pattern = "embedding:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


# Global cache instance
embedding_cache = EmbeddingCache()
