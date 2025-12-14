"use client";

import { useState } from "react";
import { ImageUpload } from "@/components/ImageUpload";
import { LabelForm } from "@/components/LabelForm";
import { VerificationResults } from "@/components/VerificationResults";
import { verifyLabel } from "@/lib/api";
import { FormData, LabelVerificationResponse } from "@/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const INITIAL_FORM_DATA: FormData = {
  brand: "",
  type: "",
  abv: "",
  volume: "",
};

function LoadingOverlay() {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-4 border-muted"></div>
          <div className="w-12 h-12 rounded-full border-4 border-primary border-t-transparent animate-spin absolute top-0 left-0"></div>
        </div>
        <p className="text-lg font-medium">Verifying label...</p>
        <p className="text-sm text-muted-foreground">This may take a few seconds</p>
      </div>
    </div>
  );
}

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [formData, setFormData] = useState<FormData>(INITIAL_FORM_DATA);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<LabelVerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSubmit = async () => {
    if (!selectedImage) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await verifyLabel([selectedImage], formData);
      setResult(response);
      setIsModalOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const isFormValid =
    selectedImage &&
    formData.brand.trim() &&
    formData.type.trim() &&
    formData.abv.trim() &&
    formData.volume.trim();

  return (
    <div className="min-h-screen bg-background">
      {/* Loading Overlay */}
      {isLoading && <LoadingOverlay />}

      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">TTB: Alcohol and Tobacco Tax and Trade Bureau</h1>
          <p className="text-sm text-muted-foreground">
            by KC Kim | devby.kc@gmail.com | 541-232-8956
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 items-stretch">
          <div className="flex flex-col">
            <h2 className="text-lg font-semibold mb-3">Upload Label Image</h2>
            <div className="flex-1">
              <ImageUpload
                onImageSelect={setSelectedImage}
                selectedImage={selectedImage}
              />
            </div>
          </div>
          <div className="flex flex-col">
            <h2 className="text-lg font-semibold mb-3">Enter Label Details</h2>
            <div className="flex-1">
              <LabelForm
                formData={formData}
                onFormChange={setFormData}
                onSubmit={handleSubmit}
                isLoading={isLoading}
                disabled={!isFormValid}
              />
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-8 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-600 font-medium">Error</p>
            <p className="text-sm text-red-500">{error}</p>
          </div>
        )}
      </main>

      {/* Results Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-6xl w-[90vw] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Verification Results</DialogTitle>
          </DialogHeader>
          {result && <VerificationResults response={result} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
