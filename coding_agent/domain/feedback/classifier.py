from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ClassifiedResult:
    """分类结果，标记本轮传感是否包含阻断性失败。"""

    has_blocking: bool = False