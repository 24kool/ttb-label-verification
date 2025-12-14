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
      "original_filename": "test_label.jpg",
      "ocr_raw_text": "JUMP BANDWAGON Original WHISKEY BOTTEK 10686 PRODUCT OF THE USA 4139 001 FUCUCED AND BOTTLED STRAIGHT BOURBON WHISKEY BATCH No FOR BANDWAGON VOLUME CRAFTED BY GintoutasDnda e700ML",
      "extracted_data": {
        "brand": "BANDWAGON",
        "type": "STRAIGHT BOURBON WHISKEY",
        "abv": "41.3%",
        "volume": "700ML",
        "error": null
      },
      "bounding_boxes": {
        "brand": {
          "x": 99,
          "y": 62,
          "width": 768,
          "height": 383
        },
        "type": {
          "x": 387,
          "y": 547,
          "width": 435,
          "height": 142
        },
        "abv": null,
        "volume": {
          "x": 228,
          "y": 728,
          "width": 122,
          "height": 48
        }
      },
      "annotated_image_base64": "data:image/jpeg;base64,..."
    }
  ],
  "comparison": {
    "is_match": false,
    "field_results": {
      "brand": {
        "match": false,
        "form_value": "Jack Daniel's",
        "label_value": "BANDWAGON",
        "normalized_form": "jack daniel's",
        "normalized_label": "bandwagon"
      },
      "type": {
        "match": false,
        "form_value": "Tennessee Sour Mash Whiskey",
        "label_value": "STRAIGHT BOURBON WHISKEY",
        "normalized_form": "tennessee sour mash whiskey",
        "normalized_label": "straight bourbon whiskey"
      },
      "abv": {
        "match": false,
        "form_value": "40%",
        "label_value": "41.3%",
        "normalized_form": "40%",
        "normalized_label": "41.3%"
      },
      "volume": {
        "match": true,
        "form_value": "70cl",
        "label_value": "700ML",
        "normalized_form": "700 mL",
        "normalized_label": "700 mL"
      }
    },
    "explanation": "Discrepancies exist between the form and label data for Brand, Type, and ABV, while Volume data is consistent after normalization. Specifically, the Brand and Type are entirely different, and there is a variance in the ABV percentage. Further investigation is required to determine the correct information and make necessary corrections."
  },
  "error": null
}
```