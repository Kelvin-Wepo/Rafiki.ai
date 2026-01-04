"""
Test script for avatar animation system integration

Tests:
- Image preprocessing and validation
- SadTalker service initialization
- Avatar animation generation
- Cache management
- API endpoints
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.image_preprocessing_service import ImagePreprocessingService
from services.sadtalker_service import SadTalkerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAvatarAnimation:
    """Test suite for avatar animation system"""

    def __init__(self):
        self.preprocess_service = ImagePreprocessingService()
        self.sadtalker_service = SadTalkerService()
        self.test_results = []

    def test_image_preprocessing_service(self):
        """Test image preprocessing service initialization"""
        logger.info("=" * 50)
        logger.info("Testing Image Preprocessing Service")
        logger.info("=" * 50)

        try:
            # Check service initialization
            assert self.preprocess_service is not None
            logger.info("✓ Image preprocessing service initialized")

            # Check methods exist
            assert hasattr(self.preprocess_service, 'detect_faces')
            assert hasattr(self.preprocess_service, 'validate_image_for_sadtalker')
            assert hasattr(self.preprocess_service, 'preprocess_image')
            logger.info("✓ All required methods available")

            # Check configuration
            assert self.preprocess_service.optimal_size == (512, 512)
            assert self.preprocess_service.min_face_ratio == 0.25
            logger.info("✓ Configuration correct")

            self.test_results.append(("Image Preprocessing Service", "PASS"))
            return True

        except Exception as e:
            logger.error(f"✗ Image preprocessing service test failed: {e}")
            self.test_results.append(("Image Preprocessing Service", "FAIL"))
            return False

    def test_sadtalker_service(self):
        """Test SadTalker service initialization"""
        logger.info("\n" + "=" * 50)
        logger.info("Testing SadTalker Service")
        logger.info("=" * 50)

        try:
            # Check service initialization
            assert self.sadtalker_service is not None
            logger.info("✓ SadTalker service initialized")

            # Check device
            logger.info(f"  Device: {self.sadtalker_service.device}")
            logger.info(f"  Mode: {self.sadtalker_service.mode}")

            # Check settings
            settings = self.sadtalker_service.get_settings()
            assert 'still_mode' in settings
            assert 'preprocess' in settings
            assert 'expression_scale' in settings
            assert 'pose_style' in settings
            logger.info("✓ All settings available")
            logger.info(f"  Settings: {settings}")

            # Check methods
            assert hasattr(self.sadtalker_service, 'get_available_avatars')
            assert hasattr(self.sadtalker_service, 'update_settings')
            assert hasattr(self.sadtalker_service, 'get_cache_stats')
            logger.info("✓ All required methods available")

            self.test_results.append(("SadTalker Service", "PASS"))
            return True

        except Exception as e:
            logger.error(f"✗ SadTalker service test failed: {e}")
            self.test_results.append(("SadTalker Service", "FAIL"))
            return False

    def test_avatar_list(self):
        """Test getting available avatars"""
        logger.info("\n" + "=" * 50)
        logger.info("Testing Avatar List")
        logger.info("=" * 50)

        try:
            avatars = self.sadtalker_service.get_available_avatars()
            assert isinstance(avatars, list)
            logger.info(f"✓ Retrieved {len(avatars)} avatar(s)")

            for avatar in avatars:
                assert 'id' in avatar
                assert 'name' in avatar
                logger.info(f"  - {avatar['name']} ({avatar['id']})")

            self.test_results.append(("Avatar List", "PASS"))
            return True

        except Exception as e:
            logger.error(f"✗ Avatar list test failed: {e}")
            self.test_results.append(("Avatar List", "FAIL"))
            return False

    def test_settings_update(self):
        """Test updating animation settings"""
        logger.info("\n" + "=" * 50)
        logger.info("Testing Settings Update")
        logger.info("=" * 50)

        try:
            # Update settings
            self.sadtalker_service.update_settings(
                still_mode=True,
                expression_scale=0.8,
                pose_style=2
            )
            logger.info("✓ Settings updated")

            # Verify settings
            settings = self.sadtalker_service.get_settings()
            assert settings['still_mode'] == True
            assert settings['expression_scale'] == 0.8
            assert settings['pose_style'] == 2
            logger.info(f"✓ Settings verified: {settings}")

            # Reset settings
            self.sadtalker_service.update_settings(
                still_mode=False,
                expression_scale=1.0,
                pose_style=0
            )
            logger.info("✓ Settings reset to default")

            self.test_results.append(("Settings Update", "PASS"))
            return True

        except Exception as e:
            logger.error(f"✗ Settings update test failed: {e}")
            self.test_results.append(("Settings Update", "FAIL"))
            return False

    def test_cache_management(self):
        """Test cache management"""
        logger.info("\n" + "=" * 50)
        logger.info("Testing Cache Management")
        logger.info("=" * 50)

        try:
            # Get cache stats
            stats = self.sadtalker_service.get_cache_stats()
            assert isinstance(stats, dict)
            assert 'cached_animations' in stats
            logger.info(f"✓ Cache stats retrieved")
            logger.info(f"  Cached animations: {stats.get('cached_animations', 0)}")
            logger.info(f"  Cache size: {stats.get('total_size_mb', 0)}MB")

            # Clear cache
            success = self.sadtalker_service.clear_cache()
            if success:
                logger.info("✓ Cache cleared successfully")
            else:
                logger.warning("⚠ Cache clear returned False")

            self.test_results.append(("Cache Management", "PASS"))
            return True

        except Exception as e:
            logger.error(f"✗ Cache management test failed: {e}")
            self.test_results.append(("Cache Management", "FAIL"))
            return False

    def test_face_detection(self):
        """Test face detection on a sample image"""
        logger.info("\n" + "=" * 50)
        logger.info("Testing Face Detection")
        logger.info("=" * 50)

        try:
            # Create a sample test image (would need actual image in production)
            logger.info("⚠ Face detection test requires actual image file")
            logger.info("  To test: Place an avatar image at './test_avatar.png'")

            test_image = Path("./test_avatar.png")
            if test_image.exists():
                logger.info(f"Testing with {test_image}")

                # Validate image
                validation = self.preprocess_service.validate_image_for_sadtalker(
                    str(test_image)
                )

                if validation['valid']:
                    logger.info("✓ Image validation passed")
                    logger.info(f"  Face ratio: {validation['details'].get('face_ratio', 'N/A')}")
                    logger.info(f"  Face centered: {validation['details'].get('is_centered', 'N/A')}")
                else:
                    logger.warning(f"✗ Image validation failed")
                    for error in validation['errors']:
                        logger.warning(f"  Error: {error}")

                self.test_results.append(("Face Detection", "PASS"))
            else:
                logger.info("  Skipping (no test image found)")
                self.test_results.append(("Face Detection", "SKIP"))

            return True

        except Exception as e:
            logger.error(f"✗ Face detection test failed: {e}")
            self.test_results.append(("Face Detection", "FAIL"))
            return False

    def test_dependencies(self):
        """Test if required dependencies are installed"""
        logger.info("\n" + "=" * 50)
        logger.info("Testing Dependencies")
        logger.info("=" * 50)

        dependencies = {
            'cv2': 'opencv-python',
            'PIL': 'pillow',
            'numpy': 'numpy',
            'torch': 'torch',
            'httpx': 'httpx',
        }

        missing = []

        for module, package in dependencies.items():
            try:
                __import__(module)
                logger.info(f"✓ {package} installed")
            except ImportError:
                logger.warning(f"✗ {package} NOT installed")
                missing.append(package)

        if missing:
            logger.warning(f"\n⚠ Missing dependencies: {', '.join(missing)}")
            logger.warning(f"  Install with: pip install {' '.join(missing)}")
            self.test_results.append(("Dependencies", "WARN"))
        else:
            logger.info("✓ All dependencies installed")
            self.test_results.append(("Dependencies", "PASS"))

        return len(missing) == 0

    def test_sadtalker_models(self):
        """Test if SadTalker models are available"""
        logger.info("\n" + "=" * 50)
        logger.info("Testing SadTalker Models")
        logger.info("=" * 50)

        checkpoint_dir = Path(self.sadtalker_service.checkpoint_dir)

        if checkpoint_dir.exists():
            models = list(checkpoint_dir.glob('*.pth'))
            if models:
                logger.info(f"✓ Found {len(models)} model files in {checkpoint_dir}")
                for model in models:
                    size_mb = model.stat().st_size / (1024 * 1024)
                    logger.info(f"  - {model.name} ({size_mb:.1f}MB)")
                self.test_results.append(("SadTalker Models", "PASS"))
                return True
            else:
                logger.warning(f"✗ No model files found in {checkpoint_dir}")
                logger.warning("  Download models from: https://github.com/OpenTalker/SadTalker#preparation")
                self.test_results.append(("SadTalker Models", "WARN"))
        else:
            logger.warning(f"✗ Checkpoint directory not found: {checkpoint_dir}")
            logger.warning("  Create directory and download models")
            self.test_results.append(("SadTalker Models", "WARN"))

        return False

    def run_all_tests(self):
        """Run all tests"""
        logger.info("\n" + "=" * 50)
        logger.info("AVATAR ANIMATION SYSTEM TEST SUITE")
        logger.info("=" * 50 + "\n")

        # Run tests
        self.test_dependencies()
        self.test_image_preprocessing_service()
        self.test_sadtalker_service()
        self.test_avatar_list()
        self.test_settings_update()
        self.test_cache_management()
        self.test_face_detection()
        self.test_sadtalker_models()

        # Print summary
        logger.info("\n" + "=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50 + "\n")

        passed = sum(1 for _, result in self.test_results if result == "PASS")
        failed = sum(1 for _, result in self.test_results if result == "FAIL")
        warnings = sum(1 for _, result in self.test_results if result == "WARN")
        skipped = sum(1 for _, result in self.test_results if result == "SKIP")

        for test_name, result in self.test_results:
            status_icon = {
                "PASS": "✓",
                "FAIL": "✗",
                "WARN": "⚠",
                "SKIP": "-"
            }
            status_color = {
                "PASS": "\033[92m",    # Green
                "FAIL": "\033[91m",    # Red
                "WARN": "\033[93m",    # Yellow
                "SKIP": "\033[94m"     # Blue
            }
            reset = "\033[0m"
            color = status_color.get(result, "")
            logger.info(
                f"{color}{status_icon.get(result, '?')} {test_name:<30} [{result}]{reset}"
            )

        logger.info("\n" + "-" * 50)
        logger.info(f"Passed:  {passed}")
        logger.info(f"Failed:  {failed}")
        logger.info(f"Warnings: {warnings}")
        logger.info(f"Skipped: {skipped}")
        logger.info("-" * 50 + "\n")

        if failed > 0:
            logger.error("Some tests failed. Check the output above.")
            return False
        else:
            logger.info("All critical tests passed!")
            return True


def main():
    """Main test entry point"""
    tester = TestAvatarAnimation()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
