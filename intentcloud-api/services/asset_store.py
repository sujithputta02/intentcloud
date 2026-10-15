"""
IntentCloud - Visual Asset Store
Manages high-resolution figures, rasterized diagram crops, fast thumbnails, and deduplication.
"""

from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image

logger = logging.getLogger("intentcloud.assets")

BASE_DIR = Path(__file__).resolve().parent.parent
FIGURES_DIR = BASE_DIR / "uploads" / "figures"
THUMBNAILS_DIR = FIGURES_DIR / "thumbnails"

# Ensure directories exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

THUMBNAIL_MAX_SIZE = (256, 256)


def compute_image_hash(image_bytes: bytes) -> str:
    """Compute SHA-256 hash of image bytes for robust deduplication."""
    return hashlib.sha256(image_bytes).hexdigest()


def save_visual_asset(
    image_bytes: bytes,
    file_id: str,
    page_num: int,
    fig_index: int,
    file_stem: str,
    extension: str = "png",
) -> Optional[Dict[str, Any]]:
    """
    Save original figure and generate an optimized 256px thumbnail.

    Returns:
        Dict with file paths, URLs, dimensions, and SHA-256 hash.
    """
    if not image_bytes or len(image_bytes) < 32:
        return None

    img_hash = compute_image_hash(image_bytes)
    ext = extension.lstrip(".").lower()
    if ext not in ("png", "jpg", "jpeg", "webp"):
        ext = "png"

    safe_stem = "".join(c for c in file_stem if c.isalnum() or c in ("-", "_"))[:30] or "fig"
    base_name = f"{safe_stem}_p{page_num}_fig{fig_index}_{img_hash[:8]}"
    orig_filename = f"{base_name}.{ext}"
    thumb_filename = f"{base_name}_thumb.webp"

    orig_path = FIGURES_DIR / orig_filename
    thumb_path = THUMBNAILS_DIR / thumb_filename

    width, height = 0, 0
    try:
        # Load in PIL to inspect and generate thumbnail
        with Image.open(io.BytesIO(image_bytes)) as pil_img:
            width, height = pil_img.size

            # Save original if not already cached
            if not orig_path.exists():
                with open(orig_path, "wb") as f:
                    f.write(image_bytes)

            # Generate high-performance 256px thumbnail
            if not thumb_path.exists():
                thumb_img = pil_img.copy()
                if thumb_img.mode in ("RGBA", "P", "LA"):
                    # Convert transparent images gracefully for WebP
                    thumb_img = thumb_img.convert("RGBA")
                else:
                    thumb_img = thumb_img.convert("RGB")
                
                thumb_img.thumbnail(THUMBNAIL_MAX_SIZE, Image.Resampling.LANCZOS)
                thumb_img.save(thumb_path, "WEBP", quality=85, method=4)

        return {
            "image_hash": img_hash,
            "image_path": str(orig_path),
            "thumbnail_path": str(thumb_path),
            "image_url": f"/figures/{orig_filename}",
            "thumbnail_url": f"/figures/thumbnails/{thumb_filename}",
            "width": width,
            "height": height,
        }
    except Exception as e:
        logger.warning(f"[AssetStore] Error processing visual asset {orig_filename}: {e}")
        # Fallback save raw bytes if PIL failed on unconventional format
        try:
            with open(orig_path, "wb") as f:
                f.write(image_bytes)
            return {
                "image_hash": img_hash,
                "image_path": str(orig_path),
                "thumbnail_path": str(orig_path),
                "image_url": f"/figures/{orig_filename}",
                "thumbnail_url": f"/figures/{orig_filename}",
                "width": width or 100,
                "height": height or 100,
            }
        except Exception:
            return None
