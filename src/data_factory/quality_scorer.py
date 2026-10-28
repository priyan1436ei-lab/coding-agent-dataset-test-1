"""Comprehensive heuristic and statistical code quality scoring engine."""
import re
from typing import Dict, Any, Tuple

class CodeQualityScorer:
    def __init__(
        self,
        max_line_length: int = 1000,
        min_alphanumeric_ratio: float = 0.35,
        max_mean_line_length: int = 150
    ):
        self.max_line_length = max_line_length
        self.min_alphanumeric_ratio = min_alphanumeric_ratio
        self.max_mean_line_length = max_mean_line_length

    def score_code(self, code_text: str) -> Tuple[float, Dict[str, Any]]:
        """Calculate quality score (0.0 to 1.0) and sub-metrics for code snippet."""
        if not code_text.strip():
            return 0.0, {"reason": "EMPTY_CODE"}

        lines = code_text.splitlines()
        total_chars = len(code_text)
        total_lines = len(lines)

        # 1. Alphanumeric ratio
        alnum_chars = sum(c.isalnum() for c in code_text)
        alnum_ratio = alnum_chars / max(1, total_chars)

        # 2. Line lengths
        line_lengths = [len(l) for l in lines]
        max_line = max(line_lengths) if line_lengths else 0
        mean_line = sum(line_lengths) / max(1, total_lines)

        # 3. Comment line ratio
        comment_lines = sum(
            1 for l in lines 
            if l.strip().startswith(("#", "//", "/*", "*", "--", ";", "%", "<!--"))
        )
        comment_ratio = comment_lines / max(1, total_lines)

        # 4. Check for minified code or boilerplate
        is_minified = max_line > self.max_line_length or (mean_line > self.max_mean_line_length and total_lines < 5)
        has_low_alnum = alnum_ratio < self.min_alphanumeric_ratio

        # Calculate composite score
        penalty = 0.0
        if is_minified:
            penalty += 0.5
        if has_low_alnum:
            penalty += 0.4
        if total_lines < 2:
            penalty += 0.2

        score = max(0.0, 1.0 - penalty)
        passed = score >= 0.6 and not is_minified and not has_low_alnum

        metrics = {
            "score": round(score, 3),
            "passed": passed,
            "total_lines": total_lines,
            "alnum_ratio": round(alnum_ratio, 3),
            "max_line_length": max_line,
            "mean_line_length": round(mean_line, 1),
            "comment_ratio": round(comment_ratio, 3)
        }
        return score, metrics
