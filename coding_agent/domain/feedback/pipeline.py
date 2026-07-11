"""FeedbackPipeline: orchestrates sensors, classifier, and correction engine."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from coding_agent.domain.feedback.sensors import Sensor
from coding_agent.domain.feedback.classifier import FailureClassifier, ClassifiedResult
from coding_agent.domain.feedback.engine import CorrectionEngine, CorrectionStrategy
from coding_agent.domain.models import SensorReport, SensorFailure, FailureSeverity, FailureCategory


@dataclass
class PipelineResult:
    """Result of a feedback pipeline run."""

    feedback_text: str = ""
    strategy: CorrectionStrategy | None = None
    classified_result: ClassifiedResult | None = None
    sensor_reports: list[SensorReport] = field(default_factory=list)


class FeedbackPipeline:
    """Orchestrates sensor pipeline, failure classification, and correction strategy.

    Runs sensors in parallel (ThreadPoolExecutor) for performance,
    then classifies failures and decides a correction strategy.
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

        Sensors are executed in parallel using a thread pool.
        Results are collected and passed to the classifier and engine.

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
        with ThreadPoolExecutor(max_workers=len(self.sensors)) as executor:
            future_to_sensor = {
                executor.submit(sensor.sense, changed_files): sensor
                for sensor in self.sensors
            }
            for future in as_completed(future_to_sensor):
                try:
                    report = future.result()
                    reports.append(report)
                except Exception:
                    sensor = future_to_sensor[future]
                    reports.append(SensorReport(
                        sensor_name=sensor.name,
                        passed=False,
                        failures=[SensorFailure(
                            file_path="",
                            severity=FailureSeverity.ERROR,
                            category=FailureCategory.UNKNOWN,
                            message=f"Sensor '{sensor.name}' execution failed",
                            raw_output="",
                        )],
                        duration_ms=0,
                    ))

        # Sort reports by sensor order (syntax -> typecheck -> lint -> test)
        name_order = {s.name: i for i, s in enumerate(self.sensors)}
        reports.sort(key=lambda r: name_order.get(r.sensor_name, 999))

        classified = self.classifier.classify(reports)
        strategy = self.engine.decide(classified)

        return PipelineResult(
            feedback_text=classified.summary,
            strategy=strategy,
            classified_result=classified,
            sensor_reports=reports,
        )