from contextlib import contextmanager
from typing import List, Literal

import sqlalchemy
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from indicate_data_exchange_client.config.configuration import DatabaseConfiguration
from indicate_data_exchange_client.db.model import WeeklyQualityIndicatorResults, AggregatedQualityIndicatorResults, \
    MonthlyQualityIndicatorResults, YearlyQualityIndicatorResults, Observations


@contextmanager
def transaction(configuration: DatabaseConfiguration):
    database_url = sqlalchemy.engine.url.URL.create(
        drivername="postgresql",
        username=configuration.user,
        password=configuration.password,
        host=configuration.host,
        port=configuration.port,
        database=configuration.database,
    )
    engine = sqlalchemy.create_engine(database_url)
    with Session(engine) as session:
        yield session
        session.commit()


def read_results(session, aggregation_period: Literal['weekly', 'monthly', 'yearly']) -> List[AggregatedQualityIndicatorResults]:
    if aggregation_period == 'weekly':
        table = WeeklyQualityIndicatorResults
    elif aggregation_period == 'monthly':
        table = MonthlyQualityIndicatorResults
    else:
        assert(aggregation_period == 'yearly')
        table = YearlyQualityIndicatorResults
    return session.scalars(select(table))

MARKER_CONCEPT_ID = 2_000_100_091

def read_run_marker(session):
    most_recent_marker = session.scalars((select(Observations)
     .where(Observations.observation_concept_id == MARKER_CONCEPT_ID)
     .order_by(desc(Observations.observation_datetime))
     .limit(1)))
    marker_observation = next(most_recent_marker, None)
    return marker_observation.observation_datetime


