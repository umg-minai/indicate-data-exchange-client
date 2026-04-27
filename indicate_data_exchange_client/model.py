from datetime import datetime
from typing import Literal, List

from pydantic import BaseModel


class QualityIndicatorInfo(BaseModel):
    """Information about a single quality indicator."""
    indicator_id: int
    title: str

class QualityIndicatorMetaData(BaseModel):
    """Meta-data for all quality indicators."""
    info: List[QualityIndicatorInfo]

    def lookup(self, title_or_id):
        if isinstance(title_or_id, str):
            return next((indicator for indicator in self.info
                         if indicator.title == title_or_id),
                        None)
        else:
            return next((indicator for indicator in self.info
                         if indicator.indicator_id == title_or_id),
                        None)


class AggregatedQualityIndicatorResult(BaseModel):
    """Aggregated results for a single quality indicator."""
    indicator_id: int

    period_kind: Literal["weekly", "monthly", "yearly"]

    period_start: datetime

    period_end: datetime

    average_value: float

    observation_count: int

class AggregatedQualityIndicatorResults(BaseModel):
    """
    Aggregated results for all quality indicators.

    Separated into usable (e.g. results that can be uploaded) and unusable results.
    """
    profile_id: str = "benchmark-profile-v1.2" # TODO: fix this once it is clear how this is should be computed/configured

    pipeline_run_id: str

    computed_at: datetime

    usable_results: List[AggregatedQualityIndicatorResult]

    unusable_results: List[AggregatedQualityIndicatorResult]
