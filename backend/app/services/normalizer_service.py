"""Service for normalizing units and values for comparison."""

import re


class NormalizerService:
    """Handles normalization of volume and ABV units."""

    @staticmethod
    def normalize_volume(value: str | None) -> str | None:
        """
        Normalize volume to standard mL format.

        Conversions:
        - cc -> mL (1:1)
        - L/l/liters -> mL (x1000)
        - ml/ML -> mL (case normalization)
        - oz -> mL (x29.5735)

        Args:
            value: Volume string (e.g., "750cc", "0.75L", "750ml")

        Returns:
            Normalized volume string (e.g., "750 mL") or None if parsing fails
        """
        if not value:
            return None

        value = value.strip()

        # Extract numeric value and unit
        match = re.match(r"([\d.]+)\s*([a-zA-Z]+)", value)
        if not match:
            return value  # Return original if can't parse

        numeric_str, unit = match.groups()
        try:
            numeric = float(numeric_str)
        except ValueError:
            return value

        unit_lower = unit.lower()

        # Convert to mL
        if unit_lower in ("l", "liter", "liters", "litre", "litres"):
            numeric = numeric * 1000
        elif unit_lower in ("oz", "fl oz", "floz"):
            numeric = numeric * 29.5735
        elif unit_lower in ("cl", "centiliter", "centiliters"):
            numeric = numeric * 10
        # cc, ml, mL are already in mL equivalent

        # Format result
        if numeric == int(numeric):
            return f"{int(numeric)} mL"
        else:
            return f"{numeric:.1f} mL"

    @staticmethod
    def normalize_abv(value: str | None) -> str | None:
        """
        Normalize ABV to standard percentage format.

        Conversions:
        - proof -> % (divide by 2)
        - "% ABV", "% alc/vol" -> "%" (remove suffix)
        - "percent" -> "%" (text to symbol)

        Args:
            value: ABV string (e.g., "90 proof", "45% ABV", "45 percent")

        Returns:
            Normalized ABV string (e.g., "45%") or None if parsing fails
        """
        if not value:
            return None

        value = value.strip().lower()

        # Handle proof
        proof_match = re.match(r"([\d.]+)\s*proof", value)
        if proof_match:
            proof_value = float(proof_match.group(1))
            abv_value = proof_value / 2
            if abv_value == int(abv_value):
                return f"{int(abv_value)}%"
            return f"{abv_value:.1f}%"

        # Extract percentage value
        percent_match = re.match(r"([\d.]+)\s*(%|percent|pct)", value)
        if percent_match:
            abv_value = float(percent_match.group(1))
            if abv_value == int(abv_value):
                return f"{int(abv_value)}%"
            return f"{abv_value:.1f}%"

        # Try to extract just a number (assume it's already a percentage)
        num_match = re.match(r"([\d.]+)", value)
        if num_match:
            abv_value = float(num_match.group(1))
            if abv_value == int(abv_value):
                return f"{int(abv_value)}%"
            return f"{abv_value:.1f}%"

        return value

    @staticmethod
    def normalize_text(value: str | None) -> str | None:
        """
        Normalize text for comparison (brand, type).

        - Lowercase
        - Remove extra whitespace
        - Strip leading/trailing whitespace

        Args:
            value: Text string

        Returns:
            Normalized text string
        """
        if not value:
            return None

        # Lowercase and normalize whitespace
        normalized = " ".join(value.lower().split())
        return normalized

    def compare_values(
        self, field: str, form_value: str | None, label_value: str | None
    ) -> tuple[bool, str | None, str | None]:
        """
        Compare form value with label value after normalization.

        Args:
            field: Field name (brand, type, abv, volume)
            form_value: Value from form input
            label_value: Value extracted from label

        Returns:
            Tuple of (match, normalized_form, normalized_label)
        """
        if field == "volume":
            norm_form = self.normalize_volume(form_value)
            norm_label = self.normalize_volume(label_value)
        elif field == "abv":
            norm_form = self.normalize_abv(form_value)
            norm_label = self.normalize_abv(label_value)
        else:  # brand, type
            norm_form = self.normalize_text(form_value)
            norm_label = self.normalize_text(label_value)

        match = norm_form == norm_label if norm_form and norm_label else False
        return match, norm_form, norm_label

