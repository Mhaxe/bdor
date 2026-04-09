from api.services.external_stats_service import ExternalStatsService


def fetch_data():
    """Fetch external stats and store raw payloads plus normalized rows."""

    return ExternalStatsService.fetch_external_stats()


def fetch_data_if_stale():
    """Fetch external stats only when today's data is not already stored."""

    return ExternalStatsService.update_stats()


if __name__ == "__main__":
    fetch_data()
