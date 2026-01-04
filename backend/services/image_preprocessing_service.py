"""
Image Preprocessing Service for SadTalker Avatar Animation

Handles preparation of avatar images for SadTalker processing:
- Face detection and verification
- Alignment checking
- Image optimization (resize, format, color space)
- Pre-processing validation before animation
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import logging
from typing import Tuple, Optional, Dict, List
import json

logger = logging.getLogger(__name__)


class ImagePreprocessingService:
    """Service for preparing images for SadTalker animation"""

    def __init__(self, cascade_path: Optional[str] = None):
        """
        Initialize preprocessing service

        Args:
            cascade_path: Path to Haar cascade XML file. If None, uses default OpenCV cascade
        """
        if cascade_path is None:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise ValueError(f"Failed to load cascade classifier from {cascade_path}")

        self.optimal_size = (512, 512)
        self.min_face_ratio = 0.25  # Face should occupy at least 25% of image
        self.max_face_ratio = 0.75  # Face should occupy at most 75% of image

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image using Haar cascade

        Args:
            image: Input image as numpy array (BGR format)

        Returns:
            List of face bounding boxes (x, y, w, h)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50),
            maxSize=(400, 400)
        )
        return faces.tolist()

    def get_face_ratio(self, image: np.ndarray, face_box: Tuple[int, int, int, int]) -> float:
        """
        Calculate percentage of image occupied by face

        Args:
            image: Input image
            face_box: Face bounding box (x, y, w, h)

        Returns:
            Ratio of face area to image area
        """
        image_area = image.shape[0] * image.shape[1]
        face_area = face_box[2] * face_box[3]
        return face_area / image_area

    def is_centered(self, image: np.ndarray, face_box: Tuple[int, int, int, int],
                    threshold: float = 0.2) -> bool:
        """
        Check if face is roughly centered in image

        Args:
            image: Input image
            face_box: Face bounding box (x, y, w, h)
            threshold: Allowed deviation from center (0.0-0.5)

        Returns:
            True if face is centered within threshold
        """
        img_h, img_w = image.shape[:2]
        face_x, face_y, face_w, face_h = face_box

        # Face center
        face_center_x = face_x + face_w / 2
        face_center_y = face_y + face_h / 2

        # Image center
        img_center_x = img_w / 2
        img_center_y = img_h / 2

        # Check distance from center
        x_deviation = abs(face_center_x - img_center_x) / img_w
        y_deviation = abs(face_center_y - img_center_y) / img_h

        return x_deviation <= threshold and y_deviation <= threshold

    def validate_image_for_sadtalker(
        self,
        image_path: str,
        return_details: bool = False
    ) -> Dict[str, any]:
        """
        Validate image is suitable for SadTalker animation

        Args:
            image_path: Path to image file
            return_details: If True, return detailed validation info

        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'image_path': str(image_path),
            'errors': [],
            'warnings': [],
            'details': {}
        }

        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                result['errors'].append('Failed to load image')
                return result

            result['details']['original_size'] = (image.shape[1], image.shape[0])

            # Check image size
            if image.shape[0] < 256 or image.shape[1] < 256:
                result['errors'].append('Image too small (minimum 256x256)')
                return result

            # Detect faces
            faces = self.detect_faces(image)
            if not faces:
                result['errors'].append('No face detected in image')
                return result

            if len(faces) > 1:
                result['warnings'].append(f'Multiple faces detected ({len(faces)}), using largest')
                face_box = max(faces, key=lambda f: f[2] * f[3])
            else:
                face_box = faces[0]

            result['details']['face_box'] = face_box
            result['details']['face_count'] = len(faces)

            # Check face ratio
            face_ratio = self.get_face_ratio(image, face_box)
            result['details']['face_ratio'] = round(face_ratio, 3)

            if face_ratio < self.min_face_ratio:
                result['errors'].append(
                    f'Face too small ({face_ratio:.1%}, minimum {self.min_face_ratio:.0%})'
                )
                return result

            if face_ratio > self.max_face_ratio:
                result['warnings'].append(
                    f'Face very large ({face_ratio:.1%}, recommended max {self.max_face_ratio:.0%})'
                )

            # Check if centered
            is_centered = self.is_centered(image, face_box)
            result['details']['is_centered'] = is_centered

            if not is_centered:
                result['warnings'].append('Face is not well centered (SadTalker works better with centered faces)')

            # Check color space
            if image.shape[2] == 4:
                result['warnings'].append('Image has alpha channel (will be converted to RGB)')

            # All checks passed
            result['valid'] = True
            return result

        except Exception as e:
            result['errors'].append(f'Validation error: {str(e)}')
            logger.error(f"Error validating image {image_path}: {e}")
            return result

    def preprocess_image(
        self,
        input_path: str,
        output_path: str,
        target_size: Tuple[int, int] = (512, 512),
        quality: int = 95
    ) -> Dict[str, any]:
        """
        Preprocess image for SadTalker animation

        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            target_size: Target image size (width, height)
            quality: JPEG quality (1-100)

        Returns:
            Dictionary with preprocessing results
        """
        result = {
            'success': False,
            'input_path': str(input_path),
            'output_path': str(output_path),
            'errors': [],
            'warnings': [],
            'details': {}
        }

        try:
            # Validate first
            validation = self.validate_image_for_sadtalker(input_path, return_details=True)
            result['validation'] = validation

            if not validation['valid']:
                result['errors'] = validation['errors']
                return result

            result['warnings'].extend(validation['warnings'])

            # Load image with PIL for better handling
            image = Image.open(input_path)
            result['details']['original_format'] = image.format
            result['details']['original_size'] = image.size

            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
                result['warnings'].append('Converted RGBA to RGB')
            elif image.mode != 'RGB':
                image = image.convert('RGB')
                result['details']['mode_converted'] = True

            # Resize maintaining aspect ratio (pad if necessary)
            image = self._resize_with_padding(image, target_size)
            result['details']['final_size'] = image.size

            # Create output directory
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Save image
            image.save(output_path, 'JPEG', quality=quality)
            result['details']['quality'] = quality
            result['success'] = True

            logger.info(f"Successfully preprocessed image: {output_path}")
            return result

        except Exception as e:
            result['errors'].append(f'Preprocessing error: {str(e)}')
            logger.error(f"Error preprocessing image: {e}")
            return result

    def _resize_with_padding(self, image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize image to target size with padding to maintain aspect ratio

        Args:
            image: PIL Image object
            target_size: Target size (width, height)

        Returns:
            Resized image with padding
        """
        # Calculate aspect ratios
        img_aspect = image.width / image.height
        target_aspect = target_size[0] / target_size[1]

        if img_aspect > target_aspect:
            # Image is wider, fit to width
            new_width = target_size[0]
            new_height = int(target_size[0] / img_aspect)
        else:
            # Image is taller, fit to height
            new_height = target_size[1]
            new_width = int(target_size[1] * img_aspect)

        # Resize
        image = image.resize((new_width, new_height), Image.LANCZOS)

        # Create new image with padding
        padded = Image.new('RGB', target_size, (255, 255, 255))
        offset = ((target_size[0] - new_width) // 2, (target_size[1] - new_height) // 2)
        padded.paste(image, offset)

        return padded

    def batch_preprocess(
        self,
        input_dir: str,
        output_dir: str,
        file_extensions: List[str] = ['jpg', 'jpeg', 'png']
    ) -> Dict[str, any]:
        """
        Batch preprocess multiple images

        Args:
            input_dir: Input directory containing images
            output_dir: Output directory for processed images
            file_extensions: List of file extensions to process

        Returns:
            Dictionary with batch processing results
        """
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'images': []
        }

        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Find all images
        image_files = []
        for ext in file_extensions:
            image_files.extend(input_path.glob(f'*.{ext}'))
            image_files.extend(input_path.glob(f'*.{ext.upper()}'))

        results['total'] = len(image_files)

        for image_file in image_files:
            output_file = output_path / f"{image_file.stem}_processed.jpg"
            result = self.preprocess_image(str(image_file), str(output_file))

            results['images'].append({
                'input': str(image_file),
                'output': str(output_file) if result['success'] else None,
                'success': result['success'],
                'errors': result['errors'],
                'warnings': result['warnings']
            })

            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1

        return results


def create_preprocessing_service() -> ImagePreprocessingService:
    """Factory function to create preprocessing service"""
    return ImagePreprocessingService()
