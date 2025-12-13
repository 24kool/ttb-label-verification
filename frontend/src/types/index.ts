// Types matching backend API response

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ExtractedData {
  brand: string | null;
  type: string | null;
  abv: string | null;
  volume: string | null;
  error: string | null;
}

export interface BoundingBoxes {
  brand: BoundingBox | null;
  type: BoundingBox | null;
  abv: BoundingBox | null;
  volume: BoundingBox | null;
}

export interface ImageResult {
  image_index: number;
  original_filename: string;
  ocr_raw_text: string;
  extracted_data: ExtractedData;
  bounding_boxes: BoundingBoxes;
  annotated_image_base64: string;
}

export interface FieldComparison {
  match: boolean;
  form_value: string | null;
  label_value: string | null;
  normalized_form: string | null;
  normalized_label: string | null;
}

export interface ComparisonResult {
  is_match: boolean;
  field_results: {
    brand?: FieldComparison;
    type?: FieldComparison;
    abv?: FieldComparison;
    volume?: FieldComparison;
  };
  explanation: string;
}

export interface LabelVerificationResponse {
  success: boolean;
  results: ImageResult[];
  comparison: ComparisonResult;
  error: string | null;
}

export interface FormData {
  brand: string;
  type: string;
  abv: string;
  volume: string;
}
