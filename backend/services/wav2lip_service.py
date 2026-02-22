"""
Lip-Sync Video Generation Service

This service generates lip-synced talking head videos using MediaPipe face mesh
and audio-driven mouth animation. It detects the face in the source image,
extracts audio energy, and morphs the mouth region to create realistic lip-sync.

Pipeline:
1. Input Validation - Verify image and audio files exist and are valid
2. Audio Processing - Convert to 16kHz mono WAV, extract energy envelope
3. Face Detection - Use MediaPipe to find face mesh landmarks
4. Frame Generation - Morph mouth landmarks based on audio energy
5. Video Encoding - Write frames with cv2.VideoWriter
6. Audio Muxing - Combine video with audio using ffmpeg
"""

import os
import cv2
import numpy as np
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure structured logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
)

# Thread pool for async execution
executor = ThreadPoolExecutor(max_workers=2)


class LipSyncService:
    """Service for generating lip-synced videos using MediaPipe face mesh"""
    
    # MediaPipe lip landmark indices (468 face mesh)
    OUTER_LIP_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78]
    INNER_LIP_INDICES = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
    UPPER_LIP_CENTER = 13
    LOWER_LIP_CENTER = 14
    
    def __init__(self):
        self.cache_dir = Path('cache/videos')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.face_landmarker = None
        self.model_loaded = False
        self._init_mediapipe()
        logger.info(f"LipSyncService initialized, cache_dir={self.cache_dir}")
    
    def _init_mediapipe(self) -> bool:
        """Initialize MediaPipe face landmarker using the Tasks API (v0.10+)"""
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            # Store mediapipe reference
            self.mp = mp
            
            # Model path
            model_path = Path(__file__).parent.parent / 'models' / 'face_landmarker.task'
            
            if not model_path.exists():
                logger.warning(f"Face landmarker model not found at {model_path}")
                logger.info("Downloading face_landmarker.task model...")
                model_path.parent.mkdir(parents=True, exist_ok=True)
                import urllib.request
                urllib.request.urlretrieve(
                    'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
                    str(model_path)
                )
                logger.info(f"Downloaded face landmarker model to {model_path}")
            
            # Create FaceLandmarker
            base_options = python.BaseOptions(model_asset_path=str(model_path))
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5
            )
            self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
            self.model_loaded = True
            logger.info("MediaPipe FaceLandmarker initialized successfully")
            return True
        except ImportError as e:
            logger.error(f"MediaPipe not installed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe: {e}", exc_info=True)
            return False
    
    def load_model(self) -> bool:
        """Compatibility method - MediaPipe loads on init"""
        return self.model_loaded
    
    def _validate_inputs(self, image_path: str, audio_path: str) -> Dict[str, Any]:
        """
        Stage 1: Validate input files
        Returns dict with validated paths and metadata
        """
        logger.debug(f"[STAGE 1] Validating inputs: image={image_path}, audio={audio_path}")
        
        errors = []
        result = {"valid": False, "image_path": image_path, "audio_path": audio_path}
        
        # Check image
        if not os.path.exists(image_path):
            errors.append(f"Image file not found: {image_path}")
        else:
            img = cv2.imread(image_path)
            if img is None:
                errors.append(f"Failed to decode image: {image_path}")
            else:
                result["image_shape"] = img.shape
                logger.debug(f"Image validated: shape={img.shape}, dtype={img.dtype}")
        
        # Check audio
        if not os.path.exists(audio_path):
            errors.append(f"Audio file not found: {audio_path}")
        else:
            result["audio_size"] = os.path.getsize(audio_path)
            logger.debug(f"Audio file exists: size={result['audio_size']} bytes")
        
        if errors:
            logger.error(f"[STAGE 1] Validation failed: {errors}")
            result["errors"] = errors
        else:
            result["valid"] = True
            logger.info("[STAGE 1] Input validation passed")
        
        return result
    
    def _process_audio(self, audio_path: str, target_sr: int = 16000) -> Tuple[np.ndarray, float]:
        """
        Stage 2: Process audio - convert to mono 16kHz, extract energy envelope
        Returns (energy_envelope, duration_seconds)
        """
        logger.debug(f"[STAGE 2] Processing audio: {audio_path}")
        
        try:
            import librosa
            
            # Load and resample to 16kHz mono
            wav, sr = librosa.load(audio_path, sr=target_sr, mono=True)
            duration = len(wav) / sr
            logger.debug(f"Audio loaded: samples={len(wav)}, sr={sr}, duration={duration:.2f}s")
            
            # Extract energy envelope using RMS
            frame_length = int(sr / 25)  # ~640 samples at 16kHz for 25fps
            hop_length = frame_length
            
            rms = librosa.feature.rms(y=wav, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Normalize to 0-1
            if rms.max() > 0:
                energy = rms / rms.max()
            else:
                energy = rms
            
            logger.info(f"[STAGE 2] Audio processed: {len(energy)} energy frames, duration={duration:.2f}s")
            return energy, duration
            
        except ImportError:
            logger.error("librosa not installed. Install with: pip install librosa")
            raise
        except Exception as e:
            logger.error(f"[STAGE 2] Audio processing failed: {e}")
            raise
    
    def _detect_face(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Stage 3: Detect face and extract landmarks using MediaPipe FaceLandmarker (v0.10+ Tasks API)
        Returns dict with landmarks and bounding box
        """
        logger.debug(f"[STAGE 3] Detecting face in image: shape={image.shape}")
        
        if self.face_landmarker is None:
            logger.error("MediaPipe FaceLandmarker not initialized")
            return None
        
        # Convert BGR to RGB for MediaPipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb_image)
        
        # Detect face landmarks
        results = self.face_landmarker.detect(mp_image)
        
        if not results.face_landmarks or len(results.face_landmarks) == 0:
            logger.warning("[STAGE 3] No face detected in image")
            return None
        
        # Get first face landmarks
        face_landmarks = results.face_landmarks[0]
        h, w = image.shape[:2]
        
        # Convert normalized landmarks to pixel coordinates
        landmarks = []
        for lm in face_landmarks:
            landmarks.append({
                "x": int(lm.x * w),
                "y": int(lm.y * h),
                "z": lm.z
            })
        
        # Get mouth region (landmarks 13 and 14 are upper/lower lip centers)
        upper_lip = landmarks[self.UPPER_LIP_CENTER]
        lower_lip = landmarks[self.LOWER_LIP_CENTER]
        mouth_height = lower_lip["y"] - upper_lip["y"]
        
        result = {
            "landmarks": landmarks,
            "mouth_center": ((upper_lip["x"] + lower_lip["x"]) // 2, 
                            (upper_lip["y"] + lower_lip["y"]) // 2),
            "mouth_height": mouth_height,
            "image_size": (w, h)
        }
        
        logger.info(f"[STAGE 3] Face detected: mouth_center={result['mouth_center']}, mouth_height={mouth_height}")
        return result
    
    def _generate_lip_frames(
        self, 
        image: np.ndarray, 
        face_data: Dict[str, Any], 
        energy: np.ndarray,
        fps: int = 25
    ) -> List[np.ndarray]:
        """
        Stage 4: Generate lip-synced frames by morphing mouth based on audio energy
        Returns list of frames
        """
        logger.debug(f"[STAGE 4] Generating {len(energy)} lip-synced frames")
        
        frames = []
        landmarks = face_data["landmarks"]
        h, w = face_data["image_size"]
        
        # Get mouth landmarks for morphing
        upper_lip_idx = self.UPPER_LIP_CENTER
        lower_lip_idx = self.LOWER_LIP_CENTER
        
        # Base mouth opening (pixels)
        base_mouth_height = face_data["mouth_height"]
        max_extra_opening = int(base_mouth_height * 0.8)  # Max 80% additional opening
        
        for i, energy_val in enumerate(energy):
            if i % 50 == 0:
                logger.debug(f"Processing frame {i+1}/{len(energy)}, energy={energy_val:.3f}")
            
            # Create frame copy
            frame = image.copy()
            
            # Calculate mouth opening based on energy (smoothed)
            opening_amount = int(energy_val * max_extra_opening)
            
            if opening_amount > 2:  # Only morph if significant energy
                frame = self._morph_mouth(frame, landmarks, opening_amount)
            
            frames.append(frame)
        
        logger.info(f"[STAGE 4] Generated {len(frames)} frames")
        return frames
    
    def _morph_mouth(self, image: np.ndarray, landmarks: List[Dict], opening: int) -> np.ndarray:
        """
        Morph the mouth region to simulate opening
        Uses simple vertical displacement of lower lip region
        """
        h, w = image.shape[:2]
        
        # Get mouth region bounding box
        mouth_points = [landmarks[i] for i in self.OUTER_LIP_INDICES if i < len(landmarks)]
        if not mouth_points:
            return image
        
        xs = [p["x"] for p in mouth_points]
        ys = [p["y"] for p in mouth_points]
        
        x1, x2 = max(0, min(xs) - 10), min(w, max(xs) + 10)
        y1, y2 = max(0, min(ys) - 5), min(h, max(ys) + opening + 10)
        
        # Create morphed region using simple warp
        lower_lip_y = landmarks[self.LOWER_LIP_CENTER]["y"]
        
        # Shift pixels below lower lip down
        result = image.copy()
        
        for y in range(min(y2 + opening, h - 1), lower_lip_y, -1):
            src_y = y - opening
            if src_y >= 0 and y < h:
                # Smooth transition
                alpha = min(1.0, (y - lower_lip_y) / (opening + 1))
                result[y, x1:x2] = cv2.addWeighted(
                    image[src_y, x1:x2], alpha,
                    image[y, x1:x2], 1 - alpha,
                    0
                )
        
        return result
    
    def _save_video(self, frames: List[np.ndarray], output_path: str, fps: int = 25) -> bool:
        """
        Stage 5: Save frames to MP4 video file (without audio)
        """
        logger.debug(f"[STAGE 5] Saving {len(frames)} frames to {output_path}")
        
        try:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            if len(frames) == 0:
                raise ValueError("No frames to save")
            
            height, width = frames[0].shape[:2]
            logger.debug(f"Frame dimensions: {width}x{height}")
            
            # Use mp4v codec - widely compatible
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                raise RuntimeError(f"Failed to open video writer for {output_path}")
            
            for i, frame in enumerate(frames):
                # Ensure uint8
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                out.write(frame)
            
            out.release()
            
            # Verify file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"[STAGE 5] Video saved: {output_path}, size={os.path.getsize(output_path)} bytes")
                return True
            else:
                logger.error(f"[STAGE 5] Video file not created or empty")
                return False
            
        except Exception as e:
            logger.error(f"[STAGE 5] Error saving video: {e}")
            raise
    
    def _mux_audio(self, video_path: str, audio_path: str, output_path: str) -> bool:
        """
        Stage 6: Mux audio with video using ffmpeg
        """
        logger.debug(f"[STAGE 6] Muxing audio: video={video_path}, audio={audio_path}")
        
        # Check ffmpeg availability
        if not shutil.which('ffmpeg'):
            logger.error("ffmpeg not found in PATH")
            # Fallback: copy video without audio
            shutil.copy(video_path, output_path)
            return False
        
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                '-loglevel', 'warning',
                output_path
            ]
            
            logger.debug(f"Running ffmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"ffmpeg failed: {result.stderr}")
                shutil.copy(video_path, output_path)
                return False
            
            logger.info(f"[STAGE 6] Audio muxed successfully: {output_path}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg timed out")
            return False
        except Exception as e:
            logger.error(f"[STAGE 6] Audio muxing failed: {e}")
            return False
    
    async def generate_video(
        self,
        image_path: str,
        audio_path: str,
        output_path: Optional[str] = None,
        fps: int = 25,
        pads: Tuple[int, int, int, int] = (0, 10, 0, 0)
    ) -> str:
        """
        Generate lip-synced video asynchronously
        
        Pipeline:
        1. Validate inputs
        2. Process audio (extract energy envelope)
        3. Detect face (MediaPipe face mesh)
        4. Generate lip-synced frames
        5. Save video
        6. Mux audio with ffmpeg
        
        Args:
            image_path: Path to avatar image
            audio_path: Path to audio file
            output_path: Path to save output video
            fps: Frames per second for output video
            pads: Padding for face detection (unused, kept for API compatibility)
        
        Returns:
            Path to generated video with audio
        """
        logger.info(f"=== Starting lip-sync generation ===")
        logger.info(f"Image: {image_path}")
        logger.info(f"Audio: {audio_path}")
        
        # Generate output path if not provided
        if output_path is None:
            cache_key = f"{Path(image_path).stem}_{Path(audio_path).stem}"
            output_path = str(self.cache_dir / f"{cache_key}.mp4")
        
        # Check cache
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"Using cached video: {output_path}")
            return output_path
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                self._generate_video_sync,
                image_path,
                audio_path,
                output_path,
                fps
            )
            return result
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}", exc_info=True)
            raise
    
    def _generate_video_sync(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        fps: int = 25
    ) -> str:
        """
        Synchronous video generation pipeline (runs in thread pool)
        """
        logger.info(f"[PIPELINE START] Generating lip-sync video")
        
        # Stage 1: Validate inputs
        validation = self._validate_inputs(image_path, audio_path)
        if not validation["valid"]:
            raise ValueError(f"Input validation failed: {validation.get('errors', 'Unknown error')}")
        
        # Stage 2: Process audio
        energy, duration = self._process_audio(audio_path)
        logger.debug(f"Audio duration: {duration:.2f}s, energy frames: {len(energy)}")
        
        # Stage 3: Detect face
        image = cv2.imread(image_path)
        face_data = self._detect_face(image)
        
        if face_data is None:
            logger.warning("No face detected, generating static video with audio")
            # Fallback: create static frames
            num_frames = int(duration * fps)
            frames = [image for _ in range(num_frames)]
        else:
            # Stage 4: Generate lip-synced frames
            frames = self._generate_lip_frames(image, face_data, energy, fps)
        
        # Stage 5: Save video (without audio)
        temp_video = output_path.replace('.mp4', '_temp.mp4')
        self._save_video(frames, temp_video, fps)
        
        # Stage 6: Mux audio
        mux_success = self._mux_audio(temp_video, audio_path, output_path)
        
        # Cleanup temp file
        if os.path.exists(temp_video) and mux_success:
            os.remove(temp_video)
        elif not mux_success:
            # If muxing failed, use temp video as output
            shutil.move(temp_video, output_path)
        
        logger.info(f"[PIPELINE COMPLETE] Output: {output_path}")
        return output_path
    
    def is_available(self) -> bool:
        """Check if service is available and ready"""
        return self.model_loaded
    
    def get_status(self) -> dict:
        """Get service status"""
        return {
            "available": self.model_loaded,
            "backend": "mediapipe",
            "cache_dir": str(self.cache_dir),
            "cached_videos": len(list(self.cache_dir.glob("*.mp4")))
        }


# Backward compatibility alias
Wav2LipService = LipSyncService

# Singleton instance
_service: Optional[LipSyncService] = None


def get_wav2lip_service() -> LipSyncService:
    """Get or create LipSync service instance"""
    global _service
    if _service is None:
        _service = LipSyncService()
    return _service


# Alias for backward compatibility
def get_lipsync_service() -> LipSyncService:
    """Alias for get_wav2lip_service"""
    return get_wav2lip_service()


async def load_wav2lip_model():
    """Async function to load model on startup (no-op for MediaPipe)"""
    service = get_wav2lip_service()
    logger.info(f"LipSync service status: {service.get_status()}")
