# TTB Label Verification

A full-stack application that verifies alcohol beverage labels using Google Gemini Vision and PaddleOCR. It extracts text from label images, compares with form data, and identifies discrepancies.

## Features

- **Vision-Based Extraction**: Gemini Vision extracts structured data (brand, type, ABV, volume) directly from images
- **Hybrid Bounding Box Detection**: PaddleOCR locates text positions for visual annotations
- **Unit Normalization**: Handles equivalent units (cc/mL, proof/%, L/mL)
- **Visual Annotations**: Returns images with bounding boxes highlighting detected fields
- **Image Validation**: Validates if the uploaded image is an alcohol label with sufficient quality
- **Comparison Report**: Detailed explanation of matches and differences

## Project Structure

```
ttb-label-verification/
├── backend/                         # FastAPI Backend
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Environment configuration
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic models
│   │   ├── services/
│   │   │   ├── ocr_service.py       # PaddleOCR integration
│   │   │   ├── llm_service.py       # Gemini Vision integration
│   │   │   ├── image_service.py     # Image annotation
│   │   │   └── normalizer_service.py # Unit conversion
│   │   └── api/
│   │       └── routes.py            # API endpoints
│   ├── requirements.txt
│   └── test.http                    # REST Client test file
│
├── frontend/                        # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # Main page
│   │   │   ├── layout.tsx           # Root layout
│   │   │   └── globals.css          # Global styles (TTB theme)
│   │   ├── components/
│   │   │   ├── ImageUpload.tsx      # Image upload with preview
│   │   │   ├── LabelForm.tsx        # Form inputs
│   │   │   ├── VerificationResults.tsx # Results display
│   │   │   ├── ComparisonCard.tsx   # Match/mismatch indicator
│   │   │   └── ui/                  # shadcn/ui components
│   │   ├── lib/
│   │   │   ├── api.ts               # API client
│   │   │   └── utils.ts             # Utility functions
│   │   └── types/
│   │       └── index.ts             # TypeScript types
│   ├── package.json
│   └── tsconfig.json
│
├── data/                            # Sample images for testing
│   └── test_label.jpg
└── README.md
```

## Tech Stack

### Backend
- **FastAPI** - Web framework
- **PaddleOCR** - Text detection and bounding box extraction
- **Google Gemini** - Vision model for text extraction and validation
- **Pillow** - Image processing and annotation

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key

### Backend Installation

```bash
cd backend

# Create conda environment
conda create -n ttb-label-verification python=3.11
conda activate ttb-label-verification

# Install dependencies
pip install -r requirements.txt

# Edit .env and add your GEMINI_API_KEY
```

### Frontend Installation

```bash
cd frontend

# Install dependencies
npm install
```

### Running the Application

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## API Usage

### POST /api/verify-label

Verify label images against form data.

**Request (multipart/form-data):**
- `images`: One or more image files
- `brand`: Brand name (string)
- `type`: Product type (string)
- `abv`: Alcohol by volume (string)
- `volume`: Bottle volume (string)


**Backend Response:**

```json
{
  "success": true,
  "results": [
    {
      "image_index": 0,
      "original_filename": "label.jpg",
      "ocr_raw_text": "(Hybrid mode) OCR: ...",
      "extracted_data": {
        "brand": "Jack Daniel's",
        "type": "Tennessee Whiskey",
        "abv": "40%",
        "volume": "750mL",
        "is_valid": true,
        "is_alcohol_label": true,
        "quality_ok": true
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
        "form_value": "Jack Daniel's",
        "label_value": "Jack Daniel's",
        "normalized_form": "jack daniel's",
        "normalized_label": "jack daniel's"
      }
    },
    "explanation": "All fields match between the form data and label image."
  }
}
```