"""FeedbackPipeline: orchestrates sensors, classifier, and correction engine."""
from __future__ import annotations
from dataclasses import dataclass, field
from coding_agent.domain.feedback.sensors import Sensor, SyntaxSensor, TypeCheckSensor, LintSensor, TestSensor
from coding_agent.domain.feedback.classifier import FailureClassifier, ClassifiedResult
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy
from coding_agent.domain.models import SensorReport


@dataclass
class PipelineResult:
    """Result of a feedback pipeline run."""

    feedback_text: str = ""
    strategy: CorrectionStrategy | None = None
    classified_result: ClassifiedResult | None = None
    sensor_reports: list[SensorReport] = field(default_factory=list)


class FeedbackPipeline:
    """Orchestrates sensor pipeline, failure classification, and correction strategy.

    Runs sensors in order (syntax -> typecheck -> lint -> test),
    classifies failures, decides a correction strategy, and generates
    human-readable feedback text for injection into the agent context.
    """

    def __init__(
        self,
        sensors: list[Sensor],
        classifier: FailureClassifier,
        engine: CorrectionEngine,
    ):
        self.sensors = sensors
        self.classifier = classifier
        self.engine = engine

    def run(self, changed_files: list[str]) -> PipelineResult:
        """Run the full feedback pipeline on the given changed files.

        Args:
            changed_files: List of file paths that were changed.

        Returns:
            PipelineResult with feedback text, strategy, classified result, and reports.
        """
        if not changed_files:
            return PipelineResult(
                feedback_text="All checks passed.",
                strategy=CorrectionStrategy.IGNORE,
            )

        reports: list[SensorReport] = []
        for sensor in self.sensors:
            report = sensor.sense(changed_files)
            reports.append(report)

        classified = self.classifier.classify(reports)
        strategy = self.engine.decide(classified)

        return PipelineResult(
            feedback_text=classified.summary,
            strategy=strategy,
            classified_result=classified,
            sensor_reports=reports,
        )