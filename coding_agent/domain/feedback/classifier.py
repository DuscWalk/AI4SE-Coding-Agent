from __future__ import annotations
from dataclasses import dataclass, field
from coding_agent.domain.models import SensorReport, SensorFailure, FailureCategory, FailureSeverity


@dataclass
class ClassifiedResult:
    """分类结果，标记本轮传感是否包含阻断性失败。"""

    total_failures: int = 0
    by_category: dict[FailureCategory, list[SensorFailure]] = field(default_factory=dict)
    by_file: dict[str, list[SensorFailure]] = field(default_factory=dict)
    has_blocking: bool = False
    blocking_failures: list[SensorFailure] = field(default_factory=list)
    summary: str = ""


BLOCKING_CATEGORIES = {
    FailureCategory.SYNTAX_ERROR,
    FailureCategory.TYPE_ERROR,
    FailureCategory.TEST_FAILURE,
    FailureCategory.IMPORT_ERROR,
    FailureCategory.TIMEOUT,
}


class FailureClassifier:
    """按类别和文件聚合 SensorReport 中的失败，生成 ClassifiedResult。"""

    def classify(self, reports: list[SensorReport]) -> ClassifiedResult:
        result = ClassifiedResult()

        all_failures: list[SensorFailure] = []
        for report in reports:
            all_failures.extend(report.failures)

        result.total_failures = len(all_failures)

        for f in all_failures:
            result.by_category.setdefault(f.category, []).append(f)
            result.by_file.setdefault(f.file_path, []).append(f)

        result.blocking_failures = [
            f for f in all_failures
            if f.category in BLOCKING_CATEGORIES and f.severity == FailureSeverity.ERROR
        ]

        result.has_blocking = len(result.blocking_failures) > 0

        result.summary = self._build_summary(result)
        return result

    def _build_summary(self, result: ClassifiedResult) -> str:
        if result.total_failures == 0:
            return "All checks passed."

        lines = [f"Feedback: {result.total_failures} issue(s) found.\n"]
        priority_order = [
            FailureCategory.SYNTAX_ERROR,
            FailureCategory.TYPE_ERROR,
            FailureCategory.TEST_FAILURE,
            FailureCategory.IMPORT_ERROR,
            FailureCategory.LINT_WARNING,
            FailureCategory.TIMEOUT,
            FailureCategory.UNKNOWN,
        ]
        for cat in priority_order:
            if cat in result.by_category:
                failures = result.by_category[cat]
                lines.append(f"\n[{cat.value.upper()}] ({len(failures)} issues):")
                for f in failures[:5]:
                    loc = f"{f.file_path}:{f.line}" if f.line else f.file_path
                    lines.append(f"  - {loc}: {f.message}")

        return "\n".join(lines)