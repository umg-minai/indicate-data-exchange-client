import os
import re
from typing import Optional

import indicate_data_exchange_api_client.hub as hub
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class DatabaseConfiguration(BaseModel):
    host: str = Field(..., description="Hostname or IP address of the database server")
    port: int = Field(5432,
                      ge=0,
                      le=65535,
                      description="Port number for the database connection")
    database: str = Field("ohdsi", description="Name of the database")
    user: str = Field("postgres", description="Username for database authentication")
    password: Optional[str] = Field(None, description="Password for database authentication")


class Configuration(BaseModel):
    # Database connection (using DBConfiguration from database.py)
    database: DatabaseConfiguration = Field(..., description="Database connection settings")

    # Provider ID
    provider_id: str = Field(...,
                             pattern=re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{8}'),
                             description="Unique identifier for the data provider")

    # Data Exchange
    data_exchange: hub.Configuration = Field(..., description="Configuration for the data exchange endpoint.")

    observation_count_threshold: int = Field(5,
                                             ge=0,
                                             description="""
                                                         The minimum number of observations (patients) on which a \
                                                         quality indicator result has to be based to be transmitted \
                                                         to the hub.
                                                         """)

    # Listening endpoint
    listen_address: str = Field("", description="Address to listen on for HTTP requests (for both, trigger and review")
    listen_port: int = Field(8080,
                             ge=0,
                             le=65535,
                             description="Port to listen on for HTTP requests (for both, trigger and review)")


def load_configuration(config_file: str = ".env") -> Configuration:
    """
    Loads the configuration from a file or environment variables.
    Environment variables take precedence over values in the configuration file.
    """

    load_dotenv(config_file)

    args = {}
    def maybe_from_env(key, variable_name, transform=None):
        value = os.getenv(variable_name)
        if value is None:
            filename = os.getenv(f"{variable_name}_FILE")
            if filename is not None:
                with open(filename) as file:
                    value = file.read().strip()

        if value is not None:
            if transform:
                value = transform(value)
            container = args
            if isinstance(key, tuple):
                for step in key[:-1]:
                    if step not in container:
                        container[step] = {}
                    container = container[step]
                key = key[-1]
            container[key] = value

    maybe_from_env(("database", "host"), "DATABASE_HOST")
    maybe_from_env(("database", "port"), "DATABASE_PORT", int)
    maybe_from_env(("database", "database"), "DATABASE_NAME")
    maybe_from_env(("database", "user"), "DATABASE_USER")
    maybe_from_env(("database", "password"), "DATABASE_PASSWORD")
    maybe_from_env(("database", "dbschema"), "DATABASE_SCHEMA")

    maybe_from_env("provider_id", "PROVIDER_ID")

    maybe_from_env(("data_exchange", "endpoint"), "DATA_EXCHANGE_ENDPOINT")
    maybe_from_env(("data_exchange", "tenant_id"), "DATA_EXCHANGE_TENANT_ID")
    maybe_from_env(("data_exchange", "sp_client_id"), "DATA_EXCHANGE_SP_CLIENT_ID")
    maybe_from_env(("data_exchange", "sp_client_secret"), "DATA_EXCHANGE_SP_CLIENT_SECRET")
    maybe_from_env(("data_exchange", "apim_app_id"), "DATA_EXCHANGE_APIM_APP_ID")

    maybe_from_env("observation_count_threshold", "OBSERVATION_COUNT_THRESHOLD")

    maybe_from_env("listen_address", "LISTEN_ADDRESS")
    maybe_from_env("listen_port", "LISTEN_PORT", int)

    return Configuration(**args)
