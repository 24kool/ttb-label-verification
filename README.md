# TTB Label Verification API

A FastAPI application that verifies alcohol beverage labels using PaddleOCR and Google Gemini LLM. It extracts text from label images, compares with form data, and identifies discrepancies.

## Features

- **OCR Text Extraction**: Uses PaddleOCR to extract text from label images
- **LLM-Powered Parsing**: Gemini LLM extracts structured data (brand, type, ABV, volume)
- **Unit Normalization**: Handles equivalent units (cc/mL, proof/%, etc.)
- **Visual Annotations**: Returns images with bounding boxes highlighting detected fields
- **Comparison Report**: Detailed explanation of matches and differences

## Project Structure

```
ttb-label-verification/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── models/schemas.py    # Pydantic models
│   │   ├── services/
│   │   │   ├── ocr_service.py   # PaddleOCR integration
│   │   │   ├── llm_service.py   # Gemini integration
│   │   │   ├── image_service.py # Image annotation
│   │   │   └── normalizer_service.py # Unit conversion
│   │   └── api/routes.py        # API endpoints
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # (To be added)
├── data/                        # Sample images
└── README.md
```

## Setup

### Prerequisites

- Python 3.10+
- Google Gemini API key

### Installation

```bash
cd backend

# Create conda environment
conda create -n ttb-label-verification python=3.11
conda activate ttb-label-verification

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Running the Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Usage

### POST /api/verify-label

Verify label images against form data.

**Request (multipart/form-data):**
- `images`: One or more image files
- `brand`: Brand name (string)
- `type`: Product type (string)
- `abv`: Alcohol by volume (string)
- `volume`: Bottle volume (string)

**Example with curl:**

```bash
curl -X POST "http://localhost:8000/api/verify-label" \
  -F "images=@label1.jpg" \
  -F "brand=Old Tom Distillery" \
  -F "type=Kentucky Straight Bourbon Whiskey" \
  -F "abv=45%" \
  -F "volume=750mL"
```

**Response:**

```json
{
  "success": true,
  "results": [
    {
      "image_index": 0,
      "original_filename": "label1.jpg",
      "ocr_raw_text": "Full OCR text...",
      "extracted_data": {
        "brand": "Old Tom Distillery",
        "type": "Kentucky Straight Bourbon Whiskey",
        "abv": "45%",
        "volume": "750mL"
      },
      "bounding_boxes": {
        "brand": {"x": 100, "y": 50, "width": 200, "height": 30},
        "type": {"x": 100, "y": 90, "width": 300, "height": 25},
        "abv": {"x": 150, "y": 130, "width": 50, "height": 20},
        "volume": {"x": 200, "y": 130, "width": 60, "height": 20}
      },
      "annotated_image_base64": "data:image/jpeg;base64,..."
    }
  ],
  "comparison": {
    "is_match": true,
    "field_results": {
      "brand": {
        "match": true,
        "form_value": "Old Tom Distillery",
        "label_value": "Old Tom Distillery",
        "normalized_form": "old tom distillery",
        "normalized_label": "old tom distillery"
      }
    },
    "explanation": "All fields match between the form data and label image."
  }
}
```

## Unit Normalization

The API handles equivalent values with different units:

| Input | Normalized | Rule |
|-------|------------|------|
| 750cc | 750 mL | 1cc = 1mL |
| 0.75L | 750 mL | 1L = 1000mL |
| 90 proof | 45% | proof / 2 = ABV% |
| 45% ABV | 45% | Remove suffix |

## Scenarios

### A. Form data matches label
All fields match - verification successful.

### B. Brand name differs
Form: "Tom's Distillery" → Label: "Old Tom Distillery"
Result: Mismatch with explanation.

### C. ABV differs
Form: "40%" → Label: "45%"
Result: Mismatch with explanation.

## License

MIT
