"""Service for OCR text extraction using PaddleOCR."""

from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import io


class OCRService:
    """Handles OCR text extraction with bounding box information."""

    def __init__(self):
        """Initialize PaddleOCR with English language support."""
        self._ocr = None

    @property
    def ocr(self) -> PaddleOCR:
        """Lazy initialization of PaddleOCR instance."""
        if self._ocr is None:
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                show_log=False,
            )
        return self._ocr

    def _process_ocr_result(self, result) -> tuple[str, list[dict]]:
        """
        Process OCR result and return formatted output.

        Args:
            result: Raw OCR result from PaddleOCR

        Returns:
            Tuple of (full_text, ocr_results)
        """
        ocr_results = []
        text_parts = []

        if result and result[0]:
            for line in result[0]:
                bbox_points = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text = line[1][0]
                confidence = line[1][1]

                # Convert polygon to rectangle bounding box
                xs = [p[0] for p in bbox_points]
                ys = [p[1] for p in bbox_points]
                bbox = {
                    "x": int(min(xs)),
                    "y": int(min(ys)),
                    "width": int(max(xs) - min(xs)),
                    "height": int(max(ys) - min(ys)),
                }

                ocr_results.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox,
                    "polygon": [[int(p[0]), int(p[1])] for p in bbox_points],
                })
                text_parts.append(text)

        full_text = " ".join(text_parts)
        return full_text, ocr_results

    def extract_text(self, image_bytes: bytes) -> tuple[str, list[dict]]:
        """
        Extract text from image bytes with bounding box information.

        Args:
            image_bytes: Image file bytes

        Returns:
            Tuple of (full_text, ocr_results)
            - full_text: All detected text concatenated
            - ocr_results: List of dicts with 'text', 'confidence', 'bbox' keys
        """
        # Convert bytes to numpy array
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)

        # Run OCR
        result = self.ocr.ocr(image_np, cls=True)

        return self._process_ocr_result(result)

    def extract_text_from_path(self, image_path: str) -> tuple[str, list[dict]]:
        """
        Extract text from image file path with bounding box information.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (full_text, ocr_results)
            - full_text: All detected text concatenated
            - ocr_results: List of dicts with 'text', 'confidence', 'bbox' keys
        """
        # Run OCR directly on file path (more efficient)
        result = self.ocr.ocr(image_path, cls=True)

        return self._process_ocr_result(result)

    def find_text_bbox(
        self, ocr_results: list[dict], search_text: str
    ) -> dict | None:
        """
        Find bounding box for a specific text in OCR results.

        Args:
            ocr_results: OCR results with bounding boxes
            search_text: Text to search for

        Returns:
            Bounding box dict or None if not found
        """
        if not search_text:
            return None

        search_lower = search_text.lower().strip()

        # First try exact match
        for result in ocr_results:
            if result["text"].lower().strip() == search_lower:
                return result["bbox"]

        # Try partial match (search text contains or is contained by result)
        for result in ocr_results:
            result_lower = result["text"].lower().strip()
            if search_lower in result_lower or result_lower in search_lower:
                return result["bbox"]

        # Try word-by-word matching for multi-word text
        search_words = search_lower.split()
        if len(search_words) > 1:
            # Find first word
            for result in ocr_results:
                if search_words[0] in result["text"].lower():
                    return result["bbox"]

        return None

    def find_field_bboxes(
        self, ocr_results: list[dict], extracted_data: dict
    ) -> dict:
        """
        Find bounding boxes for all extracted fields.

        Args:
            ocr_results: OCR results with bounding boxes
            extracted_data: Dict with brand, type, abv, volume values

        Returns:
            Dict with bounding boxes for each field
        """
        bboxes = {}

        for field in ["brand", "type", "abv", "volume"]:
            value = extracted_data.get(field)
            bbox = self.find_text_bbox(ocr_results, value)
            bboxes[field] = bbox

        return bboxes

