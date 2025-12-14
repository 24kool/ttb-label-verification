"use client";

import { FieldComparison } from "@/types";

interface ComparisonCardProps {
  field: string;
  comparison?: FieldComparison;
}

export function ComparisonCard({ field, comparison }: ComparisonCardProps) {
  if (!comparison) {
    return (
      <div className="p-3 rounded-md border bg-muted/50 border-muted">
        <div className="flex items-center justify-between">
          <span className="font-medium">{field}</span>
          <span className="text-sm text-muted-foreground">No data</span>
        </div>
      </div>
    );
  }

  const isMatch = comparison.match;

  return (
    <div
      className={`p-3 rounded-md border ${
        isMatch
          ? "bg-green-500/5 border-green-500/20"
          : "bg-red-500/5 border-red-500/20"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium">{field}</span>
        <span
          className={`flex items-center gap-1 text-sm ${
            isMatch ? "text-green-600" : "text-red-600"
          }`}
        >
          {isMatch ? (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              Match
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              Mismatch
            </>
          )}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-muted-foreground text-xs">Label Value:</span>
          <p className="font-mono bg-background px-2 py-1 rounded mt-1 truncate">
            {comparison.label_value || "-"}
          </p>
        </div>
        <div>
          <span className="text-muted-foreground text-xs">Form Value:</span>
          <p className="font-mono bg-background px-2 py-1 rounded mt-1 truncate">
            {comparison.form_value || "-"}
          </p>
        </div>
      </div>
    </div>
  );
}

