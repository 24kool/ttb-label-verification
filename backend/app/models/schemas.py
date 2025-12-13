"""Pydantic models for request and response schemas."""

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected text."""

    x: int = Field(description="X coordinate of top-left corner")
    y: int = Field(description="Y coordinate of top-left corner")
    width: int = Field(description="Width of bounding box")
    height: int = Field(description="Height of bounding box")


class ExtractedData(BaseModel):
    """Data extracted from label image."""

    brand: str | None = Field(default=None, description="Brand name")
    type: str | None = Field(default=None, description="Product type")
    abv: str | None = Field(default=None, description="Alcohol by volume")
    volume: str | None = Field(default=None, description="Volume/size")
    error: str | None = Field(default=None, description="Error message if extraction failed")


class BoundingBoxes(BaseModel):
    """Bounding boxes for each extracted field."""

    brand: BoundingBox | None = None
    type: BoundingBox | None = None
    abv: BoundingBox | None = None
    volume: BoundingBox | None = None


class ImageResult(BaseModel):
    """Result for a single processed image."""

    image_index: int = Field(description="Index of the image in the request")
    original_filename: str = Field(description="Original filename of the image")
    ocr_raw_text: str = Field(description="Full OCR extracted text")
    extracted_data: ExtractedData = Field(description="Structured data extracted from OCR text")
    bounding_boxes: BoundingBoxes = Field(description="Bounding boxes for each field")
    annotated_image_url: str = Field(description="URL path to annotated image")


class FieldComparison(BaseModel):
    """Comparison result for a single field."""

    match: bool = Field(description="Whether the field values match")
    form_value: str | None = Field(description="Value from form input")
    label_value: str | None = Field(description="Value extracted from label")
    normalized_form: str | None = Field(description="Normalized form value")
    normalized_label: str | None = Field(description="Normalized label value")


class ComparisonResult(BaseModel):
    """Overall comparison result between form data and label data."""

    is_match: bool = Field(description="Whether all fields match")
    field_results: dict[str, FieldComparison] = Field(
        description="Comparison results for each field"
    )
    explanation: str = Field(description="LLM-generated explanation of differences")


class LabelVerificationRequest(BaseModel):
    """Request model for label verification (form fields only, images sent separately)."""

    brand: str = Field(description="Brand name from form")
    type: str = Field(description="Product type from form")
    abv: str = Field(description="ABV from form")
    volume: str = Field(description="Volume from form")


class LabelVerificationResponse(BaseModel):
    """Response model for label verification."""

    success: bool = Field(description="Whether the request was processed successfully")
    results: list[ImageResult] = Field(description="Results for each processed image")
    comparison: ComparisonResult = Field(description="Comparison between form and label data")
    error: str | None = Field(default=None, description="Error message if any")

