"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormData } from "@/types";

interface LabelFormProps {
  formData: FormData;
  onFormChange: (data: FormData) => void;
  onSubmit: () => void;
  isLoading: boolean;
  disabled: boolean;
}

const FIELD_CONFIG = [
  {
    key: "brand" as const,
    label: "Brand",
    placeholder: "e.g., Jack Daniel's",
    description: "Enter the brand or distillery name shown on the label",
  },
  {
    key: "type" as const,
    label: "Type",
    placeholder: "e.g., Tennessee Whiskey",
    description: "Enter the type of alcohol (bourbon, vodka, rum, etc.)",
  },
  {
    key: "abv" as const,
    label: "ABV",
    placeholder: "e.g., 40%",
    description: "Enter the alcohol percentage (ABV or proof)",
  },
  {
    key: "volume" as const,
    label: "Volume",
    placeholder: "e.g., 750mL",
    description: "Enter the bottle size (mL, L, or oz)",
  },
];

export function LabelForm({
  formData,
  onFormChange,
  onSubmit,
  isLoading,
  disabled,
}: LabelFormProps) {
  const handleChange = (key: keyof FormData, value: string) => {
    onFormChange({ ...formData, [key]: value });
  };

  return (
    <Card className="h-full">
      <CardContent className="space-y-5">
        {FIELD_CONFIG.map((field) => (
          <div key={field.key} className="space-y-2">
            <Label htmlFor={field.key}>{field.label}</Label>
            <Input
              id={field.key}
              placeholder={field.placeholder}
              value={formData[field.key]}
              onChange={(e) => handleChange(field.key, e.target.value)}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">{field.description}</p>
          </div>
        ))}

        <Button
          onClick={onSubmit}
          disabled={disabled || isLoading}
          className="w-full mt-4"
          size="lg"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Verifying...
            </span>
          ) : (
            "Run Verify"
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

