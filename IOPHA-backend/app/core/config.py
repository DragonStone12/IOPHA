from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for observability and logging.

    Values are read from environment variables (and a local ``.env`` file in
    development). AWS Lambda Powertools additionally honours
    ``POWERTOOLS_DEV=true`` locally to pretty-print metrics instead of
    emitting strict EMF JSON blobs to stdout.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Powertools EMF configuration. The namespace groups all custom metrics
    # in CloudWatch; the service name becomes the ``service`` dimension.
    POWERTOOLS_SERVICE_NAME: str = "iopha-backend"
    POWERTOOLS_METRICS_NAMESPACE: str = "IOPHA/Backend"
    LOG_LEVEL: str = "INFO"
    # Master switch for EMF metric emission (middleware + cold start).
    METRICS_ENABLED: bool = True
    # Local-dev only: expose the pull/scrape Prometheus ``/metrics`` endpoint.
    # Never enabled on Lambda -- Prometheus cannot scrape ephemeral containers.
    PROMETHEUS_ENABLED: bool = False


settings = Settings()

__all__ = ["Settings", "settings"]
