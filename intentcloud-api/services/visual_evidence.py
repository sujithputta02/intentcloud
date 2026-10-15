"""
IntentCloud - Visual Evidence Data Model
Defines the first-class data structure for embedded images, diagrams, charts, and visual figures.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class VisualEvidence(BaseModel):
    """First-class evidence model for visual figures, charts, and diagrams extracted from documents."""
    visual_id: str = Field(description="Unique identifier for this visual evidence item")
    file_id: str = Field(description="UUID of the parent document")
    filename: str = Field(default="", description="Original filename of the parent document")
    page_number: int = Field(default=1, description="1-indexed page number where this visual occurs")
    bbox: List[float] = Field(
        default_factory=lambda: [0.0, 0.0, 1.0, 1.0],
        description="Bounding box coordinates [x0, y0, x1, y1] normalized or points"
    )
    image_path: str = Field(description="Local filesystem path to original high-res image")
    thumbnail_path: str = Field(description="Local filesystem path to 256px UI thumbnail")
    image_url: str = Field(description="Web accessible URL to original image e.g. /figures/...")
    thumbnail_url: str = Field(description="Web accessible URL to thumbnail e.g. /figures/thumbnails/...")
    image_hash: str = Field(description="SHA-256 hash of image content for deduplication")
    visual_type: str = Field(default="figure", description="Category: figure, diagram, chart, table, slide, photo")
    figure_label: str = Field(default="Fig. 1", description="Display label e.g. Fig. 1, Chart 2")
    caption: Optional[str] = Field(default=None, description="Nearby caption text extracted from document")
    ocr_text: Optional[str] = Field(default=None, description="Text and labels extracted from inside the image via OCR")
    visual_description: Optional[str] = Field(default=None, description="Semantic description generated via Vision LLM")
    extraction_method: str = Field(default="embedded", description="Method: 'embedded' (PyMuPDF xref) or 'rendered' (page raster crop)")
    width: int = Field(default=0, description="Image width in pixels")
    height: int = Field(default=0, description="Image height in pixels")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when this visual asset was cataloged"
    )
    provenance: str = Field(default="", description="Citation string: 'doc.pdf, p. 3, Fig. 1'")
    relevance_score: Optional[float] = Field(default=None, description="Search relevance score (0.0 to 1.0)")
    relevance_percentage: Optional[int] = Field(default=None, description="Search relevance percentage (0 to 100)")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses and metadata serialization."""
        return self.model_dump()
