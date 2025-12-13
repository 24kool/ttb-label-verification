"""Service for image annotation and Base64 encoding."""

import base64
import io
from PIL import Image, ImageDraw, ImageFont


class ImageService:
    """Handles image annotation with bounding boxes and Base64 encoding."""

    # Colors for different fields (RGB)
    FIELD_COLORS = {
        "brand": (255, 0, 0),      # Red
        "type": (0, 255, 0),       # Green
        "abv": (0, 0, 255),        # Blue
        "volume": (255, 165, 0),   # Orange
    }

    def __init__(self):
        """Initialize image service."""
        self._font = None

    @property
    def font(self) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Get font for labels (falls back to default if not available)."""
        if self._font is None:
            try:
                self._font = ImageFont.truetype("DejaVuSans.ttf", 10)
            except (OSError, IOError):
                try:
                    self._font = ImageFont.truetype("Arial.ttf", 10)
                except (OSError, IOError):
                    self._font = ImageFont.load_default()
        return self._font

    def draw_bounding_boxes(
        self,
        image_bytes: bytes,
        bounding_boxes: dict,
    ) -> bytes:
        """
        Draw bounding boxes on image for detected fields.

        Args:
            image_bytes: Original image bytes
            bounding_boxes: Dict mapping field names to bbox dicts

        Returns:
            Annotated image bytes
        """
        # Open image
        image = Image.open(io.BytesIO(image_bytes))

        # Always convert to RGB for consistent color handling
        if image.mode != "RGB":
            image = image.convert("RGB")

        draw = ImageDraw.Draw(image)

        # Draw each bounding box
        for field, bbox in bounding_boxes.items():
            if bbox is None:
                continue

            color = self.FIELD_COLORS.get(field, (128, 128, 128))

            # Draw rectangle
            x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
            draw.rectangle(
                [x, y, x + w, y + h],
                outline=color,
                width=1,
            )

            # Draw label background
            label = field.upper()
            text_bbox = draw.textbbox((0, 0), label, font=self.font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            label_x = x
            label_y = y - text_height - 4

            # Ensure label is visible (move below if above image edge)
            if label_y < 0:
                label_y = y + h + 2

            draw.rectangle(
                [label_x, label_y, label_x + text_width + 4, label_y + text_height + 2],
                fill=color,
            )

            # Draw label text
            draw.text(
                (label_x + 2, label_y),
                label,
                fill=(255, 255, 255),
                font=self.font,
            )

        # Save to bytes
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=90)
        return output.getvalue()

    def annotate_and_encode(
        self,
        image_bytes: bytes,
        bounding_boxes: dict,
    ) -> str:
        """
        Draw bounding boxes and return as Base64 encoded string.

        Args:
            image_bytes: Original image bytes
            bounding_boxes: Dict mapping field names to bbox dicts

        Returns:
            Base64 encoded annotated image (data URI format)
        """
        # Draw bounding boxes
        annotated_bytes = self.draw_bounding_boxes(image_bytes, bounding_boxes)
        
        # Convert to Base64
        base64_data = base64.b64encode(annotated_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{base64_data}"
