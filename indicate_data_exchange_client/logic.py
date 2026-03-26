import datetime
import logging
from typing import Optional, Literal, cast

import indicate_data_exchange_api_client
from indicate_data_exchange_api_client import AggregationPeriodKind, ApiClient, \
    DefaultApi, ProviderResultsPostRequest, ApiException

from indicate_data_exchange_client.config.configuration import Configuration
from indicate_data_exchange_client.db import database
from indicate_data_exchange_client.model import AggregatedQualityIndicatorResult, AggregatedQualityIndicatorResults, \
    QualityIndicatorMetaData, QualityIndicatorInfo

logger = logging.getLogger("logic")


def fetch_meta_data(configuration):
    """
    Fetch meta-data for all quality indicators.

    The main reason for fetching this data is to display quality indicator \
    names instead of ids to users.
    """
    logger.info(f"Fetching quality indicator meta-data from {configuration.data_exchange_endpoint}")
    api_configuration = indicate_data_exchange_api_client.configuration.Configuration(host=configuration.data_exchange_endpoint)
    with ApiClient(api_configuration) as api_client:
        api_instance = DefaultApi(api_client)
        try:
            result = api_instance.indicator_info_get()
            logger.info(f"Successfully fetched meta-data for {len(result)} indicator(s)")
            return QualityIndicatorMetaData(
                info=[ QualityIndicatorInfo(indicator_id=info.concept_id, title=info.title)
                       for info in result ]
            )
        except ApiException as e:
            logger.error(f"Failed to fetch meta-data for quality indicators: {e}")
            raise e


def collect_aggregated_results(configuration):
    """Retrieve aggregated quality indicator results from the database."""
    usable_results, unusable_results = [], []
    with database.transaction(configuration.database) as session:
        for period_kind in [
            AggregationPeriodKind.WEEKLY,
            AggregationPeriodKind.MONTHLY,
            AggregationPeriodKind.YEARLY,
        ]:
            period_name = cast(Literal["weekly", "monthly", "yearly"], period_kind.name.lower())
            aggregated_results = database.read_results(session, period_name)

            usable_count, unusable_count = 0, 0
            for result in aggregated_results:
                internal_result = AggregatedQualityIndicatorResult(
                    indicator_id=result.observation_concept_id,
                    period_kind=period_name,
                    period_start=result.period_start,
                    period_end=result.period_end,
                    average_value=result.average_value,
                    observation_count=result.observation_count,
                )
                if internal_result.observation_count >= configuration.observation_count_threshold:
                    usable_results.append(internal_result)
                    usable_count += 1
                else:
                    unusable_results.append(internal_result)
                    unusable_count += 1
            logger.info(f"Collected {usable_count} usable result(s) and {unusable_count} unusable result(s) for {period_name} aggregation")
    return AggregatedQualityIndicatorResults(
        computed_at=datetime.datetime.now(),
        usable_results=usable_results,
        unusable_results=unusable_results)


def transmit_aggregated_results(configuration: Configuration, results: AggregatedQualityIndicatorResults):
    """Submit aggregated quality indicator results to the data exchange server."""
    logger.info(f"Submitting aggregated data to {configuration.data_exchange_endpoint}")

    results_for_api = [
        indicate_data_exchange_api_client.AggregatedQualityIndicatorResult(
            indicator_id=result.indicator_id,
            aggregation_period_kind=AggregationPeriodKind.__members__[result.period_kind.upper()],
            aggregation_period_start=result.period_start,
            average_value=result.average_value,
            observation_count=result.observation_count
        )
        for result in results.usable_results
    ]
    api_configuration = indicate_data_exchange_api_client.configuration.Configuration(host=configuration.data_exchange_endpoint)
    with ApiClient(api_configuration) as api_client:
        api_instance = DefaultApi(api_client)
        payload = ProviderResultsPostRequest(
            provider_id=configuration.provider_id,
            results=results_for_api
        )
        try:
            api_instance.provider_results_post(payload)
            logger.info("Successfully submitted aggregated data")
            return True
        except ApiException as e:
            logger.error(f"Failed to submit aggregated data: {e}")
            raise e


class State:
    """Holds meta-data about indicators as well as to-be-uploaded results, if any."""

    def __init__(self, configuration: Configuration):
        self.configuration = configuration
        self._meta_data: Optional[dict] = None
        self.results: Optional[AggregatedQualityIndicatorResults] = None

    @property
    def meta_data(self):
        if self._meta_data is None:
            try:
                self._meta_data = fetch_meta_data(self.configuration)
            except Exception as e:
                logger.error(f"Failed to fetch quality indicator meta data: {e}")
        return self._meta_data

    def fetch_results(self):
        self.results = collect_aggregated_results(self.configuration)

    def transmit_results(self):
        if self.results is None:
            raise ValueError("No results to transmit")
        transmit_aggregated_results(self.configuration, self.results)
        self.results = None

    def clear_results(self):
        self.results = None


state = None
