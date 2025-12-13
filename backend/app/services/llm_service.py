"""Service for LLM-based text parsing and comparison using Gemini."""

import json
import logging
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

    @property
    def model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            self._model = genai.GenerativeModel("gemini-2.5-flash")

        return self._model

    def parse_label_text(self, ocr_text: str) -> dict:

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
                # Remove first line (```json) and last line (```)
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
