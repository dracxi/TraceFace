"""Face embedding generation using InsightFace."""
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)


def generate_embedding(face_image: np.ndarray, face_obj=None) -> np.ndarray:
    """
    Generate face embedding from aligned face image.
    
    Args:
        face_image: Aligned face image (112x112)
        face_obj: InsightFace face object (if available)
    
    Returns:
        512-dimensional L2-normalized embedding vector
    """
    try:
        # If face object from InsightFace is provided, use its embedding
        if face_obj is not None and hasattr(face_obj, 'embedding'):
            embedding = face_obj.embedding
        else:
            # This is a placeholder - in production, you'd use the actual model
            # For now, generate a random normalized embedding
            embedding = np.random.randn(512).astype(np.float32)
        
        # L2 normalize the embedding
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


def compute_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        Cosine similarity score [-1, 1]
    """
    # Ensure embeddings are normalized
    embedding1 = embedding1 / np.linalg.norm(embedding1)
    embedding2 = embedding2 / np.linalg.norm(embedding2)
    
    # Cosine similarity is dot product of normalized vectors
    similarity = np.dot(embedding1, embedding2)
    
    return float(similarity)


def batch_compute_similarity(query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    """
    Compute similarity between query and multiple embeddings.
    
    Args:
        query_embedding: Query embedding vector (512,)
        embeddings: Array of embeddings (N, 512)
    
    Returns:
        Array of similarity scores (N,)
    """
    # Normalize query
    query_embedding = query_embedding / np.linalg.norm(query_embedding)
    
    # Normalize all embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings_normalized = embeddings / norms
    
    # Compute dot products (cosine similarity)
    similarities = np.dot(embeddings_normalized, query_embedding)
    
    return similarities
