import { LabelVerificationResponse, FormData } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function verifyLabel(
  images: File[],
  formData: FormData
): Promise<LabelVerificationResponse> {
  const form = new window.FormData();

  // Add images
  images.forEach((image) => {
    form.append("images", image);
  });

  // Add form fields
  form.append("brand", formData.brand);
  form.append("type", formData.type);
  form.append("abv", formData.abv);
  form.append("volume", formData.volume);

  // Always use vision mode (default)
  form.append("use_vision", "true");

  const response = await fetch(`${API_BASE_URL}/api/verify-label`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

