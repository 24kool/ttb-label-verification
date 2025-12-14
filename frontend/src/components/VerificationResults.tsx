"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LabelVerificationResponse } from "@/types";
import { ComparisonCard } from "./ComparisonCard";

interface VerificationResultsProps {
  response: LabelVerificationResponse;
}

export function VerificationResults({ response }: VerificationResultsProps) {
  const { results, comparison } = response;
  const imageResult = results[0]; // Show first image result
  const { field_results, is_match } = comparison;

  return (
    <div className="space-y-6">
      {/* Header with overall status and explanation */}
      <div
        className={`p-4 rounded-lg ${
          is_match
            ? "bg-green-500/10 border border-green-500/30"
            : "bg-red-500/10 border border-red-500/30"
        }`}
      >
        <div className="text-center mb-3">
          <span
            className={`text-lg font-semibold ${
              is_match ? "text-green-600" : "text-red-600"
            }`}
          >
            {is_match ? "All Fields Match" : "Differences Found"}
          </span>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap text-center">
          {comparison.explanation}
        </p>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Annotated Image */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Annotated Image</CardTitle>
          </CardHeader>
          <CardContent>
            {imageResult?.annotated_image_base64 ? (
              <img
                src={imageResult.annotated_image_base64}
                alt="Annotated label"
                className="annotated-image rounded-md border"
              />
            ) : (
              <div className="h-48 bg-muted rounded-md flex items-center justify-center">
                <span className="text-muted-foreground">No image available</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Comparison Results */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Comparison Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ComparisonCard field="Brand" comparison={field_results.brand} />
            <ComparisonCard field="Type" comparison={field_results.type} />
            <ComparisonCard field="ABV" comparison={field_results.abv} />
            <ComparisonCard field="Volume" comparison={field_results.volume} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
