"""Service for LLM-based text parsing and comparison using Gemini."""

import json
import logging
import base64
from pathlib import Path
import google.generativeai as genai
from app.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """Handles LLM operations for text parsing and comparison."""

    def __init__(self):
        """Initialize Gemini client."""
        settings = get_settings()
        self._api_key = settings.gemini_api_key
        
        if not self._api_key or self._api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY is not configured! LLM features will not work.")
        else:
            genai.configure(api_key=self._api_key)
            logger.info("Gemini API configured successfully")
        
        self._model = None
        self._vision_model = None

    @property
    def model(self):
        """Lazy initialization of Gemini text model."""
        if self._model is None:
            self._model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("Using Gemini model: gemini-2.5-flash")
        return self._model

    @property
    def vision_model(self):
        """Lazy initialization of Gemini vision model."""
        if self._vision_model is None:
            self._vision_model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("Using Gemini vision model: gemini-2.5-flash")
        return self._vision_model

    def extract_from_image_simple(self, image_path: str) -> dict:
        """
        Extract label information directly from image using vision model.
        Simple version without bounding boxes - for hybrid mode.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with brand, type, abv, volume fields
        """
        # Check if API key is configured
        if not self._api_key or self._api_key == "your_gemini_api_key_here":
            logger.error("Cannot extract from image: GEMINI_API_KEY not configured")
            return {
                "brand": None,
                "type": None,
                "abv": None,
                "volume": None,
                "error": "GEMINI_API_KEY not configured",
            }

        prompt = """You are a label information extractor for alcohol beverage labels.
Look at this label image and extract the following information:

1. brand - The brand/distillery name (e.g., "Jack Daniel's", "Johnnie Walker")
2. type - The type of alcohol (e.g., "Tennessee Whiskey", "Single Malt Scotch Whisky")
3. abv - Alcohol by volume percentage (e.g., "40%", "43% ABV")
4. volume - The bottle volume (e.g., "750mL", "70cl", "1L")

Respond ONLY with a valid JSON object in this exact format:
{
    "brand": "extracted brand or null if not found",
    "type": "extracted type or null if not found",
    "abv": "extracted abv or null if not found",
    "volume": "extracted volume or null if not found"
}

If a field cannot be found in the image, use null.
Do not include any explanation, just the JSON object."""

        try:
            # Read and encode image
            image_path_obj = Path(image_path)
            with open(image_path_obj, "rb") as f:
                image_data = f.read()
            
            # Determine MIME type
            suffix = image_path_obj.suffix.lower()
            mime_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(suffix, "image/jpeg")
            
            # Create image part for Gemini
            image_part = {
                "mime_type": mime_type,
                "data": image_data
            }
            
            logger.info(f"Sending image to Gemini vision model (simple): {image_path_obj.name}")
            response = self.vision_model.generate_content([prompt, image_part])
            response_text = response.text.strip()
            logger.info(f"Gemini vision response: {response_text}")

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            result = json.loads(response_text)
            parsed = {
                "brand": result.get("brand"),
                "type": result.get("type"),
                "abv": result.get("abv"),
                "volume": result.get("volume"),
            }
            logger.info(f"Vision extracted result: {parsed}")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response was: {response_text}")
            return {
                "brand": None,
                "type": None,
                "abv": None,
                "volume": None,
                "error": f"JSON decode error: {e}",
            }
        except Exception as e:
            logger.error(f"Error calling Gemini Vision API: {e}")
            return {
                "brand": None,
                "type": None,
                "abv": None,
                "volume": None,
                "error": str(e),
            }

    def validate_image(self, image_path: str) -> dict:
        """
        Validate if the image is a valid alcohol beverage label with good quality.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with validation results:
            - is_valid: bool - whether the image is a valid alcohol label
            - is_alcohol_label: bool - whether this appears to be an alcohol label
            - quality_ok: bool - whether image quality is sufficient
            - message: str - explanation of any issues
        """
        # Check if API key is configured
        if not self._api_key or self._api_key == "your_gemini_api_key_here":
            logger.error("Cannot validate image: GEMINI_API_KEY not configured")
            return {
                "is_valid": False,
                "is_alcohol_label": False,
                "quality_ok": False,
                "message": "GEMINI_API_KEY not configured",
            }

        prompt = """Analyze this image and determine:

1. Is this an alcohol beverage label (beer, wine, spirits, etc.)?
2. Is the image quality sufficient to read the text on the label?

Respond ONLY with a valid JSON object in this exact format:
{
    "is_alcohol_label": true or false,
    "quality_ok": true or false,
    "message": "Brief explanation if there are any issues, or 'Valid alcohol label' if OK"
}

Consider the image as NOT an alcohol label if:
- It's a completely different product (food, cosmetics, etc.)
- It's not a product label at all (random photo, document, etc.)

Consider the quality as NOT OK if:
- The image is too blurry to read text
- The image is too dark or overexposed
- The label text is not visible or cut off
- The image resolution is too low

Only return the JSON object, no other text."""

        try:
            # Read and encode image
            image_path_obj = Path(image_path)
            with open(image_path_obj, "rb") as f:
                image_data = f.read()
            
            # Determine MIME type
            suffix = image_path_obj.suffix.lower()
            mime_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(suffix, "image/jpeg")
            
            # Create image part for Gemini
            image_part = {
                "mime_type": mime_type,
                "data": image_data
            }
            
            logger.info(f"Validating image with Gemini: {image_path_obj.name}")
            response = self.vision_model.generate_content([prompt, image_part])
            response_text = response.text.strip()
            logger.info(f"Image validation response: {response_text}")

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            result = json.loads(response_text)
            is_alcohol_label = result.get("is_alcohol_label", False)
            quality_ok = result.get("quality_ok", False)
            message = result.get("message", "")
            
            return {
                "is_valid": is_alcohol_label and quality_ok,
                "is_alcohol_label": is_alcohol_label,
                "quality_ok": quality_ok,
                "message": message,
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in validation: {e}")
            return {
                "is_valid": True,  # Default to valid on parse error
                "is_alcohol_label": True,
                "quality_ok": True,
                "message": "Validation response parse error, proceeding anyway",
            }
        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return {
                "is_valid": True,  # Default to valid on error
                "is_alcohol_label": True,
                "quality_ok": True,
                "message": f"Validation error: {e}, proceeding anyway",
            }

    def extract_from_image(self, image_path: str, image_width: int = 0, image_height: int = 0) -> tuple[dict, dict]:
        """
        Extract label information directly from image using vision model.
        Also attempts to get bounding box coordinates for each field.
        
        Args:
            image_path: Path to the image file
            image_width: Width of the image in pixels (for coordinate scaling)
            image_height: Height of the image in pixels (for coordinate scaling)
            
        Returns:
            Tuple of (extracted_data, bounding_boxes)
            - extracted_data: Dict with brand, type, abv, volume fields
            - bounding_boxes: Dict with bounding box for each field
        """
        empty_bboxes = {"brand": None, "type": None, "abv": None, "volume": None}
        
        # Check if API key is configured
        if not self._api_key or self._api_key == "your_gemini_api_key_here":
            logger.error("Cannot extract from image: GEMINI_API_KEY not configured")
            return {
                "brand": None,
                "type": None,
                "abv": None,
                "volume": None,
                "error": "GEMINI_API_KEY not configured",
            }, empty_bboxes

        prompt = f"""You are a label information extractor for alcohol beverage labels.
Look at this label image and extract the following information WITH their approximate bounding box locations.

The image dimensions are: {image_width}x{image_height} pixels.

For each field, provide:
1. The extracted text value
2. The bounding box coordinates (x, y, width, height) in pixels where:
   - x: left edge of the text
   - y: top edge of the text  
   - width: width of the text area
   - height: height of the text area

Extract these fields:
1. brand - The brand/distillery name (e.g., "Jack Daniel's", "Johnnie Walker")
2. type - The type of alcohol (e.g., "Tennessee Whiskey", "Single Malt Scotch Whisky")
3. abv - Alcohol by volume percentage (e.g., "40%", "43% ABV")
4. volume - The bottle volume (e.g., "750mL", "70cl", "1L")

Respond ONLY with a valid JSON object in this exact format:
{{
    "brand": "extracted brand or null if not found",
    "brand_bbox": {{"x": 0, "y": 0, "width": 0, "height": 0}} or null,
    "type": "extracted type or null if not found",
    "type_bbox": {{"x": 0, "y": 0, "width": 0, "height": 0}} or null,
    "abv": "extracted abv or null if not found",
    "abv_bbox": {{"x": 0, "y": 0, "width": 0, "height": 0}} or null,
    "volume": "extracted volume or null if not found",
    "volume_bbox": {{"x": 0, "y": 0, "width": 0, "height": 0}} or null
}}

If a field cannot be found in the image, use null for both value and bbox.
Estimate bounding box coordinates as accurately as possible based on where you see the text.
Do not include any explanation, just the JSON object."""

        try:
            # Read and encode image
            image_path = Path(image_path)
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Determine MIME type
            suffix = image_path.suffix.lower()
            mime_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(suffix, "image/jpeg")
            
            # Create image part for Gemini
            image_part = {
                "mime_type": mime_type,
                "data": image_data
            }
            
            logger.info(f"Sending image to Gemini vision model: {image_path.name}")
            response = self.vision_model.generate_content([prompt, image_part])
            response_text = response.text.strip()
            logger.info(f"Gemini vision response: {response_text}")

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            result = json.loads(response_text)
            
            # Extract data
            extracted = {
                "brand": result.get("brand"),
                "type": result.get("type"),
                "abv": result.get("abv"),
                "volume": result.get("volume"),
            }
            
            # Extract and validate bounding boxes
            def validate_bbox(bbox_data):
                """Validate and convert bounding box data to proper format."""
                if bbox_data is None:
                    return None
                if not isinstance(bbox_data, dict):
                    return None
                try:
                    return {
                        "x": int(bbox_data.get("x", 0)),
                        "y": int(bbox_data.get("y", 0)),
                        "width": int(bbox_data.get("width", 0)),
                        "height": int(bbox_data.get("height", 0)),
                    }
                except (TypeError, ValueError):
                    return None
            
            bboxes = {
                "brand": validate_bbox(result.get("brand_bbox")),
                "type": validate_bbox(result.get("type_bbox")),
                "abv": validate_bbox(result.get("abv_bbox")),
                "volume": validate_bbox(result.get("volume_bbox")),
            }
            
            logger.info(f"Vision extracted result: {extracted}")
            logger.info(f"Vision bounding boxes: {bboxes}")
            return extracted, bboxes
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response was: {response_text}")
            return {
                "brand": None,
                "type": None,
                "abv": None,
                "volume": None,
                "error": f"JSON decode error: {e}",
            }, empty_bboxes
        except Exception as e:
            logger.error(f"Error calling Gemini Vision API: {e}")
            return {
                "brand": None,
                "type": None,
                "abv": None,
                "volume": None,
                "error": str(e),
            }, empty_bboxes

    def parse_label_text(self, ocr_text: str) -> dict:
        """
        Parse OCR text to extract structured label information.

        Args:
            ocr_text: Raw text extracted from label image

        Returns:
            Dict with brand, type, abv, volume fields
        """
        prompt = f"""You are a label information extractor for alcohol beverage labels.
Extract the following information from the OCR text of a label image.

OCR Text:
{ocr_text}

Extract these fields:
1. brand - The brand/distillery name (e.g., "Jack Daniel's", "Old Tom Distillery")
2. type - The type of alcohol (e.g., "Tennessee Sour Mash Whiskey", "Kentucky Straight Bourbon Whiskey", "Vodka")
3. abv - Alcohol by volume percentage (e.g., "40%", "45% ABV", "40% Vol")
4. volume - The bottle volume (e.g., "750mL", "70cl", "1L")

Respond ONLY with a valid JSON object in this exact format:
{{
    "brand": "extracted brand or null if not found",
    "type": "extracted type or null if not found",
    "abv": "extracted abv or null if not found",
    "volume": "extracted volume or null if not found"
}}

If a field cannot be found, use null.
Do not include any explanation, just the JSON object."""

        try:
            logger.info(f"Sending OCR text to Gemini: {ocr_text[:100]}...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            logger.info(f"Gemini response: {response_text}")

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            result = json.loads(response_text)
            parsed = {
                "brand": result.get("brand"),
                "type": result.get("type"),
                "abv": result.get("abv"),
                "volume": result.get("volume"),
            }
            logger.info(f"Parsed result: {parsed}")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response was: {response_text}")
            return {
                "brand": None,
                "type": None,
                "abv": None,
                "volume": None,
                "error": f"JSON decode error: {e}",
            }
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {
                "brand": None,
                "type": None,
                "abv": None,
                "volume": None,
                "error": str(e),
            }

    def generate_comparison_explanation(
        self,
        form_data: dict,
        label_data: dict,
        field_results: dict,
    ) -> str:
        """
        Generate LLM explanation of differences between form and label data.

        Args:
            form_data: Dict with form input values
            label_data: Dict with label extracted values
            field_results: Dict with comparison results per field

        Returns:
            Human-readable explanation of differences
        """
        # Check if API key is configured
        if not self._api_key or self._api_key == "your_gemini_api_key_here":
            return "Unable to generate explanation: GEMINI_API_KEY not configured"

        # Build differences list
        differences = []
        matches = []

        for field, result in field_results.items():
            form_val = result.get("form_value", "N/A")
            label_val = result.get("label_value", "N/A")
            norm_form = result.get("normalized_form", "N/A")
            norm_label = result.get("normalized_label", "N/A")

            if result.get("match"):
                if form_val != label_val:
                    matches.append(
                        f"- {field.upper()}: Form says '{form_val}', label shows '{label_val}' "
                        f"(equivalent after normalization: {norm_form})"
                    )
                else:
                    matches.append(f"- {field.upper()}: '{form_val}' - exact match")
            else:
                differences.append(
                    f"- {field.upper()}: Form says '{form_val}', but label shows '{label_val}'"
                )

        if not differences:
            return "All fields match between the form data and label image. The label verification is successful."

        prompt = f"""You are a label verification assistant. Explain the differences between form data and label data clearly.

MATCHES:
{chr(10).join(matches) if matches else "None"}

DIFFERENCES:
{chr(10).join(differences)}

Provide a clear, concise explanation (2-3 sentences) of:
1. What fields don't match
2. The specific differences found
3. What action might be needed

Be professional and direct. Do not use markdown formatting."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating comparison explanation: {e}")
            # Fallback to simple explanation
            diff_summary = "; ".join(
                f"{field}: form='{r.get('form_value')}' vs label='{r.get('label_value')}'"
                for field, r in field_results.items()
                if not r.get("match")
            )
            return f"Differences found: {diff_summary}"
