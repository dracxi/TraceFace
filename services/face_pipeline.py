"""Complete face processing pipeline."""
import numpy as np
from typing import List, Dict
import logging
from services.face_detection import face_detector
from services.face_alignment import align_and_crop_face
from services.face_embedding import generate_embedding
from models.schemas import FaceDetection, FaceEmbedding

logger = logging.getLogger(__name__)


class FaceProcessingPipeline:
    """Complete pipeline for face detection, alignment, and embedding generation."""
    
    def __init__(self):
        """Initialize the pipeline."""
        self.detector = face_detector
    
    def process_image(self, image: np.ndarray) -> List[Dict]:
        """
        Process image through complete pipeline.
        
        Args:
            image: Input image as numpy array (RGB)
        
        Returns:
            List of dicts containing detection info and embeddings
        """
        results = []
        
        try:
            # Use InsightFace to get faces with embeddings directly
            if self.detector.app is None:
                self.detector.load_model()
            
            # Convert to BGR for InsightFace
            image_bgr = image[:, :, ::-1]
            faces = self.detector.app.get(image_bgr)
            
            if not faces:
                logger.warning("No faces detected in image")
                return results
            
            # Process each detected face
            for face in faces:
                try:
                    # Filter by confidence
                    if face.det_score < self.detector.confidence_threshold:
                        continue
                    
                    # Extract detection info
                    detection = {
                        'bbox': face.bbox.tolist(),
                        'landmarks': face.kps.tolist(),
                        'confidence': float(face.det_score)
                    }
                    
                    # Get embedding from InsightFace (already normalized)
                    embedding = face.embedding
                    
                    # Normalize to be sure
                    embedding = embedding / np.linalg.norm(embedding)
                    
                    # Create result
                    result = {
                        'detection': detection,
                        'embedding': embedding.tolist(),
                        'aligned_face': None  # Not needed since we have embedding
                    }
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed to process detected face: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(results)} faces")
            return results
            
        except Exception as e:
            logger.error(f"Face processing pipeline failed: {e}")
            raise
    
    def process_image_to_schemas(self, image: np.ndarray) -> List[FaceEmbedding]:
        """
        Process image and return Pydantic schemas.
        
        Args:
            image: Input image as numpy array (RGB)
        
        Returns:
            List of FaceEmbedding schemas
        """
        results = self.process_image(image)
        
        face_embeddings = []
        for result in results:
            detection_data = result['detection']
            face_detection = FaceDetection(
                bbox=detection_data['bbox'],
                landmarks=detection_data['landmarks'],
                confidence=detection_data['confidence']
            )
            
            face_embedding = FaceEmbedding(
                embedding=result['embedding'],
                detection=face_detection
            )
            face_embeddings.append(face_embedding)
        
        return face_embeddings


# Global pipeline instance
face_pipeline = FaceProcessingPipeline()
