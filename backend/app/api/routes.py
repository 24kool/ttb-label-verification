"""API routes for label verification."""

import os
import uuid
import tempfile
from pathlib import Path
from PIL import Image
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from app.models.schemas import (
    LabelVerificationResponse,
    ImageResult,
    ExtractedData,
    BoundingBox,
    BoundingBoxes,
    FieldComparison,
    ComparisonResult,
)
from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService
from app.services.image_service import ImageService
from app.services.normalizer_service import NormalizerService


router = APIRouter(prefix="/api", tags=["Label Verification"])

# Initialize services
ocr_service = OCRService()
llm_service = LLMService()
image_service = ImageService()
normalizer_service = NormalizerService()

# Temporary directory for image processing
TEMP_DIR = Path(tempfile.gettempdir()) / "ttb_label_verification"


def ensure_temp_dir():
    """Ensure temporary directory exists."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def save_temp_image(image_bytes: bytes, original_filename: str) -> Path:
    """
    Save image bytes to temporary file.
    
    Args:
        image_bytes: Image file bytes
        original_filename: Original filename for extension
        
    Returns:
        Path to saved temporary file
    """
    ensure_temp_dir()
    
    # Get file extension from original filename
    ext = Path(original_filename).suffix or ".jpg"
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{ext}"
    temp_path = TEMP_DIR / unique_filename
    
    # Write bytes to file
    with open(temp_path, "wb") as f:
        f.write(image_bytes)
    
    return temp_path


def delete_temp_file(file_path: Path):
    """
    Delete temporary file if it exists.
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if file_path.exists():
            os.remove(file_path)
    except Exception:
        pass  # Ignore deletion errors


@router.post("/verify-label", response_model=LabelVerificationResponse)
async def verify_label(
    images: list[UploadFile] = File(..., description="Label images to verify"),
    brand: str = Form(..., description="Brand name from form"),
    type: str = Form(..., description="Product type from form"),
    abv: str = Form(..., description="ABV from form"),
    volume: str = Form(..., description="Volume from form"),
    use_vision: bool = Form(default=False, description="Use vision model instead of OCR"),
) -> LabelVerificationResponse:
    """
    Verify label images against form data.

    This endpoint:
    1. Saves uploaded images to temporary files
    2. Extracts info using either:
       - OCR + LLM (default): PaddleOCR extracts text, then Gemini parses it
       - Vision mode (use_vision=true): Gemini vision model reads image directly
    3. Normalizes values for comparison (handles unit conversions)
    4. Compares form data with extracted label data
    5. Returns annotated images with bounding boxes and comparison results
    6. Deletes temporary files after processing
    """
    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required")

    form_data = {
        "brand": brand,
        "type": type,
        "abv": abv,
        "volume": volume,
    }

    results: list[ImageResult] = []
    aggregated_extracted_data = {
        "brand": None,
        "type": None,
        "abv": None,
        "volume": None,
    }
    
    # Track temporary files for cleanup
    temp_files: list[Path] = []

    try:
        for idx, image_file in enumerate(images):
            # Read image bytes
            image_bytes = await image_file.read()
            
            # Save to temporary file
            temp_path = save_temp_image(
                image_bytes, 
                image_file.filename or f"image_{idx}.jpg"
            )
            temp_files.append(temp_path)

            ocr_text = ""
            ocr_results = []
            bboxes = {"brand": None, "type": None, "abv": None, "volume": None}

            if use_vision:
                # Hybrid mode: Vision for extraction + OCR for bounding boxes
                # Step 1: Run OCR to get text positions
                ocr_text, ocr_results = ocr_service.extract_text_from_path(str(temp_path))
                
                # Step 2: Use Vision model for extraction (includes validation)
                extracted = llm_service.extract_from_image_simple(str(temp_path))
                
                # Check validation from extraction result
                if not extracted.get("is_valid", True):
                    # Clean up temp files before raising error
                    for temp_file in temp_files:
                        delete_temp_file(temp_file)
                    
                    # Build error message
                    if not extracted.get("is_alcohol_label", True):
                        error_msg = "This image does not appear to be an alcohol beverage label. Please upload a valid alcohol label image."
                    elif not extracted.get("quality_ok", True):
                        error_msg = f"Image quality issue: {extracted.get('validation_message', 'Please upload a clearer image.')}"
                    else:
                        error_msg = extracted.get("validation_message", "Invalid image")
                    
                    raise HTTPException(status_code=400, detail=error_msg)
                
                # Step 3: Use OCR results to find bounding boxes for extracted values
                bboxes = ocr_service.find_field_bboxes(ocr_results, extracted)
                
                ocr_text = f"(Hybrid mode) OCR: {ocr_text}"
            else:
                # OCR mode: Extract text with OCR, then parse with LLM
                ocr_text, ocr_results = ocr_service.extract_text_from_path(str(temp_path))
                extracted = llm_service.parse_label_text(ocr_text)
                # Find bounding boxes for extracted fields
                bboxes = ocr_service.find_field_bboxes(ocr_results, extracted)

            # Update aggregated data (use first non-null value found)
            for field in ["brand", "type", "abv", "volume"]:
                if aggregated_extracted_data[field] is None and extracted.get(field):
                    aggregated_extracted_data[field] = extracted[field]

            # Create BoundingBoxes object
            bbox_objects = BoundingBoxes(
                brand=BoundingBox(**bboxes["brand"]) if bboxes.get("brand") else None,
                type=BoundingBox(**bboxes["type"]) if bboxes.get("type") else None,
                abv=BoundingBox(**bboxes["abv"]) if bboxes.get("abv") else None,
                volume=BoundingBox(**bboxes["volume"]) if bboxes.get("volume") else None,
            )

            # Annotate image with bounding boxes and encode as Base64
            with open(temp_path, "rb") as f:
                image_bytes_for_annotation = f.read()
            annotated_image_base64 = image_service.annotate_and_encode(
                image_bytes_for_annotation, bboxes
            )

            # Create result for this image
            result = ImageResult(
                image_index=idx,
                original_filename=image_file.filename or f"image_{idx}",
                ocr_raw_text=ocr_text,
                extracted_data=ExtractedData(**extracted),
                bounding_boxes=bbox_objects,
                annotated_image_base64=annotated_image_base64,
            )
            results.append(result)

        # Compare form data with aggregated label data
        field_results = {}
        all_match = True

        for field in ["brand", "type", "abv", "volume"]:
            form_value = form_data.get(field)
            label_value = aggregated_extracted_data.get(field)

            match, norm_form, norm_label = normalizer_service.compare_values(
                field, form_value, label_value
            )

            field_results[field] = FieldComparison(
                match=match,
                form_value=form_value,
                label_value=label_value,
                normalized_form=norm_form,
                normalized_label=norm_label,
            )

            if not match:
                all_match = False

        # Generate LLM explanation
        field_results_dict = {
            k: v.model_dump() for k, v in field_results.items()
        }
        explanation = llm_service.generate_comparison_explanation(
            form_data, aggregated_extracted_data, field_results_dict
        )

        comparison = ComparisonResult(
            is_match=all_match,
            field_results=field_results,
            explanation=explanation,
        )

        return LabelVerificationResponse(
            success=True,
            results=results,
            comparison=comparison,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing images: {str(e)}"
        )
    
    finally:
        # Clean up: Delete all temporary files
        for temp_path in temp_files:
            delete_temp_file(temp_path)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "TTB Label Verification API"}
