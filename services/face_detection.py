import logging
from typing import List

import numpy as np
from insightface.app import FaceAnalysis

from config import settings

logger = logging.getLogger(__name__)


class FaceDetector:
    def __init__(self):
        self.app = None
        self.confidence_threshold = settings.FACE_DETECTION_CONFIDENCE
    
    def load_model(self):
        if self.app is None:
            try:
                self.app = FaceAnalysis(providers=['CPUExecutionProvider'])
                self.app.prepare(ctx_id=0, det_size=(640, 640))
                logger.info("Face detection model loaded")
            except Exception as e:
                logger.error(f"Failed to load face detection model: {e}")
                raise
    
    def detect_faces(self, image: np.ndarray) -> List[dict]:
        """Detect faces in RGB image, returns list of detections with bbox, landmarks, and confidence."""
        if self.app is None:
            self.load_model()
        
        try:
            # InsightFace expects BGR
            image_bgr = image[:, :, ::-1]
            faces = self.app.get(image_bgr)
            
            detections = []
            for face in faces:
                if face.det_score < self.confidence_threshold:
                    continue
                
                detections.append({
                    'bbox': face.bbox.tolist(),
                    'landmarks': face.kps.tolist(),
                    'confidence': float(face.det_score)
                })
            
            logger.info(f"Detected {len(detections)} faces")
            return detections
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            raise


face_detector = FaceDetector()
