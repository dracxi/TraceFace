import io

import cv2
import numpy as np
from PIL import Image


def resize_image(image: np.ndarray, max_dimension: int = 1024) -> np.ndarray:
    """Resize image to max dimension while maintaining aspect ratio."""
    height, width = image.shape[:2]
    
    if height <= max_dimension and width <= max_dimension:
        return image
    
    if height > width:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    else:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


def convert_to_rgb(image: np.ndarray, from_pil: bool = False) -> np.ndarray:
    """Convert image to RGB color space."""
    if len(image.shape) == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        if from_pil:
            return image[:, :, :3]
        else:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    elif image.shape[2] == 3:
        if from_pil:
            return image
        else:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize pixel values to [0, 1] range."""
    return image.astype(np.float32) / 255.0


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Complete preprocessing pipeline for uploaded images."""
    image = Image.open(io.BytesIO(image_bytes))
    image_np = np.array(image)
    image_np = resize_image(image_np, max_dimension=1024)
    image_np = convert_to_rgb(image_np, from_pil=True)
    return image_np


def load_image_from_file(file_path: str) -> np.ndarray:
    """Load and preprocess image from file path."""
    with open(file_path, 'rb') as f:
        image_bytes = f.read()
    return preprocess_image(image_bytes)
