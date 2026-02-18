"""Face alignment module."""
import cv2
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)


def align_face(image: np.ndarray, landmarks: np.ndarray, output_size: tuple = (112, 112)) -> np.ndarray:
    """
    Align face using facial landmarks with similarity transformation.
    
    Args:
        image: Input image
        landmarks: 5 facial landmarks [[x, y], ...]
        output_size: Output face size (width, height)
    
    Returns:
        Aligned face image of size output_size
    """
    # Standard landmark positions for 112x112 face
    standard_landmarks = np.array([
        [38.2946, 51.6963],  # Left eye
        [73.5318, 51.5014],  # Right eye
        [56.0252, 71.7366],  # Nose
        [41.5493, 92.3655],  # Left mouth
        [70.7299, 92.2041]   # Right mouth
    ], dtype=np.float32)
    
    # Scale standard landmarks if output size is different
    if output_size != (112, 112):
        scale_x = output_size[0] / 112.0
        scale_y = output_size[1] / 112.0
        standard_landmarks[:, 0] *= scale_x
        standard_landmarks[:, 1] *= scale_y
    
    # Convert landmarks to numpy array
    if isinstance(landmarks, list):
        landmarks = np.array(landmarks, dtype=np.float32)
    
    # Estimate similarity transform
    transform_matrix = cv2.estimateAffinePartial2D(
        landmarks, standard_landmarks, method=cv2.LMEDS
    )[0]
    
    # Apply transformation
    aligned_face = cv2.warpAffine(
        image, transform_matrix, output_size, 
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0
    )
    
    return aligned_face


def crop_face_bbox(image: np.ndarray, bbox: List[float], margin: float = 0.2) -> np.ndarray:
    """
    Crop face from image using bounding box with margin.
    
    Args:
        image: Input image
        bbox: Bounding box [x1, y1, x2, y2]
        margin: Margin to add around bbox (as fraction of bbox size)
    
    Returns:
        Cropped face image
    """
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    
    # Add margin
    x1 = max(0, int(x1 - width * margin))
    y1 = max(0, int(y1 - height * margin))
    x2 = min(image.shape[1], int(x2 + width * margin))
    y2 = min(image.shape[0], int(y2 + height * margin))
    
    cropped = image[y1:y2, x1:x2]
    return cropped


def align_and_crop_face(
    image: np.ndarray, 
    detection: dict, 
    output_size: tuple = (112, 112)
) -> np.ndarray:
    """
    Align and crop face from detection.
    
    Args:
        image: Input image
        detection: Face detection dict with 'bbox' and 'landmarks'
        output_size: Output face size
    
    Returns:
        Aligned and cropped face image
    """
    try:
        landmarks = np.array(detection['landmarks'], dtype=np.float32)
        aligned_face = align_face(image, landmarks, output_size)
        return aligned_face
    except Exception as e:
        logger.error(f"Face alignment failed: {e}")
        # Fallback to simple crop
        bbox = detection['bbox']
        cropped = crop_face_bbox(image, bbox)
        resized = cv2.resize(cropped, output_size, interpolation=cv2.INTER_LINEAR)
        return resized
