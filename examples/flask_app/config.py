"""Configuration for a simple flask app

Most of the settings are not used by the teeny app: they are
only included to demonstrate the various ConfigProperty options.
"""

from grift import BaseConfig, ConfigProperty
from grift import EnvLoader, JsonFileLoader
from grift.property_types import PostgresType
from schematics.types import BooleanType, StringType, IntType


class AppConfig(BaseConfig):
    # Constants that may differ between local dev and deployed environment(s)
    DEBUG = ConfigProperty(property_type=BooleanType(), default=False)
    LOG_LEVEL = ConfigProperty(property_type=StringType(), default='INFO')
    PORT = ConfigProperty(property_type=IntType(), default=5000)

    # Specify the host for another API
    API_HOST = ConfigProperty(property_type=StringType())

    # Secrets that cannot be checked in to the repository
    API_TOKEN = ConfigProperty(property_type=StringType(), exclude_from_varz=True)
    DATABASE_URL = ConfigProperty(
        property_type=PostgresType(), required=False, exclude_from_varz=True)


# Specify where to read configuration values from
loaders = [
    EnvLoader(),   # Prioritize environment variables
    JsonFileLoader('./config.json')  # Fall back on JSON file
]

app_config = AppConfig(loaders)