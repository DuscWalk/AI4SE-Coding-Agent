from __future__ import annotations
from enum import Enum
from coding_agent.domain.feedback.classifier import ClassifiedResult


class CorrectionStrategy(str, Enum):
    RETRY = "retry"
    ROLLBACK = "rollback"
    ASK_USER = "ask_user"
    IGNORE = "ignore"


class CorrectionEngine:
    """根据分类结果和重试计数决定修正策略。

    渐进式升级策略：
    1. RETRY（附带错误信息重试）— 前 max_retries 次
    2. ROLLBACK（回退变更）— 第 max_retries+1 次
    3. ASK_USER（升级给用户）— 超过 max_retries+1 次
    """

    def __init__(self, max_retries: int = 3):
        self.retry_count = 0
        self.max_retries = max_retries

    def decide(self, classified: ClassifiedResult) -> CorrectionStrategy:
        if not classified.has_blocking:
            return CorrectionStrategy.IGNORE

        self.retry_count += 1
        if self.retry_count <= self.max_retries:
            return CorrectionStrategy.RETRY
        if self.retry_count == self.max_retries + 1:
            return CorrectionStrategy.ROLLBACK

        return CorrectionStrategy.ASK_USER

    def reset(self) -> None:
        self.retry_count = 0