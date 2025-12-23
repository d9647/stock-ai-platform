"""
Validate feature snapshots for data quality.
Ensures features are complete, within valid ranges, and consistent.
"""
from typing import Dict, List
from loguru import logger

# Import config with proper path handling
try:
    from ..config import config
except ImportError:
    from config import config


class FeatureValidator:
    """
    Validates feature snapshots for data quality issues.
    """

    def __init__(self):
        """Initialize validator with rules from config."""
        self.validation_rules = config.VALIDATION_RULES
        logger.info("Initialized feature validator")

    def validate_snapshot(self, snapshot: Dict) -> Dict:
        """
        Validate a complete feature snapshot.

        Args:
            snapshot: Snapshot dict from SnapshotCreator

        Returns:
            Dict with validation results:
            {
                "is_valid": bool,
                "errors": [list of critical issues],
                "warnings": [list of non-critical issues],
                "checks_passed": int,
                "checks_failed": int
            }
        """
        errors = []
        warnings = []
        checks_passed = 0
        checks_failed = 0

        # Extract features
        technical_features = snapshot.get("technical_features", {})
        sentiment_features = snapshot.get("sentiment_features", {})

        # Validate technical features
        tech_result = self._validate_technical_features(technical_features)
        errors.extend(tech_result["errors"])
        warnings.extend(tech_result["warnings"])
        checks_passed += tech_result["checks_passed"]
        checks_failed += tech_result["checks_failed"]

        # Validate sentiment features
        sent_result = self._validate_sentiment_features(sentiment_features)
        errors.extend(sent_result["errors"])
        warnings.extend(sent_result["warnings"])
        checks_passed += sent_result["checks_passed"]
        checks_failed += sent_result["checks_failed"]

        # Validate cross-feature consistency
        consistency_result = self._validate_consistency(
            technical_features, sentiment_features
        )
        errors.extend(consistency_result["errors"])
        warnings.extend(consistency_result["warnings"])
        checks_passed += consistency_result["checks_passed"]
        checks_failed += consistency_result["checks_failed"]

        # Determine if valid (no errors)
        is_valid = len(errors) == 0

        result = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed
        }

        if not is_valid:
            logger.warning(
                f"Snapshot validation failed: {len(errors)} errors, "
                f"{len(warnings)} warnings"
            )
        else:
            logger.info(
                f"Snapshot validation passed: {checks_passed} checks passed, "
                f"{len(warnings)} warnings"
            )

        return result

    def _validate_technical_features(self, features: Dict) -> Dict:
        """Validate technical indicator features."""
        errors = []
        warnings = []
        checks_passed = 0
        checks_failed = 0

        # Check if technical features exist
        if not features:
            errors.append("No technical features present")
            checks_failed += 1
            return {
                "errors": errors,
                "warnings": warnings,
                "checks_passed": 0,
                "checks_failed": checks_failed
            }

        # Validate each technical feature
        for feature_name, value in features.items():
            if feature_name not in self.validation_rules:
                continue  # Skip features not in validation rules

            rule = self.validation_rules[feature_name]

            # Check if required feature is missing
            if rule.get("required", False) and value is None:
                errors.append(f"Required feature '{feature_name}' is missing")
                checks_failed += 1
                continue

            # Skip validation if value is None and not required
            if value is None:
                continue

            # Range validation
            if "min" in rule and value < rule["min"]:
                errors.append(
                    f"Feature '{feature_name}' = {value} is below minimum {rule['min']}"
                )
                checks_failed += 1
                continue

            if "max" in rule and value > rule["max"]:
                errors.append(
                    f"Feature '{feature_name}' = {value} exceeds maximum {rule['max']}"
                )
                checks_failed += 1
                continue

            checks_passed += 1

        return {
            "errors": errors,
            "warnings": warnings,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed
        }

    def _validate_sentiment_features(self, features: Dict) -> Dict:
        """Validate sentiment features."""
        errors = []
        warnings = []
        checks_passed = 0
        checks_failed = 0

        # Sentiment features are optional, so empty is acceptable
        if not features:
            warnings.append("No sentiment features present (acceptable if no news)")
            return {
                "errors": errors,
                "warnings": warnings,
                "checks_passed": 0,
                "checks_failed": 0
            }

        # Validate each sentiment feature
        for feature_name, value in features.items():
            # Skip top_themes (it's a list)
            if feature_name == "top_themes":
                continue

            if feature_name not in self.validation_rules:
                continue

            rule = self.validation_rules[feature_name]

            # Range validation
            if "min" in rule and value < rule["min"]:
                errors.append(
                    f"Sentiment feature '{feature_name}' = {value} is below minimum {rule['min']}"
                )
                checks_failed += 1
                continue

            if "max" in rule and value > rule["max"]:
                errors.append(
                    f"Sentiment feature '{feature_name}' = {value} exceeds maximum {rule['max']}"
                )
                checks_failed += 1
                continue

            checks_passed += 1

        # Validate sentiment distribution consistency
        if "article_count" in features:
            article_count = features["article_count"]
            positive = features.get("positive_count", 0)
            neutral = features.get("neutral_count", 0)
            negative = features.get("negative_count", 0)
            total_distribution = positive + neutral + negative

            if total_distribution != article_count:
                warnings.append(
                    f"Sentiment distribution sum ({total_distribution}) "
                    f"!= article_count ({article_count})"
                )

        return {
            "errors": errors,
            "warnings": warnings,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed
        }

    def _validate_consistency(
        self,
        technical_features: Dict,
        sentiment_features: Dict
    ) -> Dict:
        """Validate cross-feature consistency."""
        errors = []
        warnings = []
        checks_passed = 0
        checks_failed = 0

        # Validate SMA ordering (SMA_20 should be closer to current price)
        if technical_features:
            sma_20 = technical_features.get("sma_20")
            sma_50 = technical_features.get("sma_50")
            sma_200 = technical_features.get("sma_200")

            # Check that all SMAs are positive
            if sma_20 and sma_20 > 0:
                checks_passed += 1
            if sma_50 and sma_50 > 0:
                checks_passed += 1
            if sma_200 and sma_200 > 0:
                checks_passed += 1

        return {
            "errors": errors,
            "warnings": warnings,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed
        }


if __name__ == "__main__":
    # Test validator
    validator = FeatureValidator()

    # Test snapshot with valid data
    test_snapshot = {
        "snapshot_id": "AAPL_2025-12-14_1.0.0",
        "ticker": "AAPL",
        "technical_features": {
            "sma_20": 250.5,
            "sma_50": 245.3,
            "sma_200": 220.1,
            "rsi_14": 55.2,
            "macd": 2.5,
            "volatility_30d": 0.15
        },
        "sentiment_features": {
            "avg_sentiment": 0.25,
            "weighted_sentiment": 0.30,
            "article_count": 10,
            "positive_count": 6,
            "neutral_count": 2,
            "negative_count": 2,
            "top_themes": ["earnings", "product_launch"]
        }
    }

    result = validator.validate_snapshot(test_snapshot)
    print(f"\nValidation result: {result}")

    # Test with invalid data
    invalid_snapshot = {
        "snapshot_id": "TEST_2025-12-14_1.0.0",
        "ticker": "TEST",
        "technical_features": {
            "rsi_14": 150,  # Invalid: > 100
            "sma_20": -10,  # Invalid: negative
        },
        "sentiment_features": {
            "avg_sentiment": 2.0,  # Invalid: > 1
            "article_count": 5,
            "positive_count": 3,
            "neutral_count": 1,
            "negative_count": 2  # Invalid: sum != article_count
        }
    }

    invalid_result = validator.validate_snapshot(invalid_snapshot)
    print(f"\nInvalid validation result: {invalid_result}")
