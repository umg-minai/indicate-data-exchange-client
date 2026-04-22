from datetime import datetime

from sqlalchemy import NUMERIC, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

SCHEMA = "cds_cdm"

class Base(DeclarativeBase):
    pass

class AggregatedQualityIndicatorResults:
    __table_args__ = {"schema": SCHEMA}

    observation_id: Mapped[int] = mapped_column(primary_key=True)
    observation_concept_id: Mapped[int]
    period_start: Mapped[datetime] = mapped_column(TIMESTAMP)
    period_end: Mapped[datetime] = mapped_column(TIMESTAMP)
    average_value: Mapped[float] = mapped_column(NUMERIC)
    observation_count: Mapped[int]

class DailyQualityIndicatorResults(Base, AggregatedQualityIndicatorResults):
    __tablename__ = "quality_indicator_daily_average"

class WeeklyQualityIndicatorResults(Base, AggregatedQualityIndicatorResults):
    __tablename__ = "quality_indicator_weekly_average"

class MonthlyQualityIndicatorResults(Base, AggregatedQualityIndicatorResults):
    __tablename__ = "quality_indicator_monthly_average"

class YearlyQualityIndicatorResults(Base, AggregatedQualityIndicatorResults):
    __tablename__ = "quality_indicator_yearly_average"
