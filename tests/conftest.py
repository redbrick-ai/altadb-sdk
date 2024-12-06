"""Pytest configuration file."""

import os

import pytest

import altadb


ALTADB_API_KEY = os.environ["ALTADB_API_KEY"]
ALTADB_SECRET_KEY = os.environ["ALTADB_SECRET_KEY"]
ALTADB_URL = os.environ["ALTADB_URL"]
ALTADB_ORG_ID = os.environ["ALTADB_ORG_ID"]


@pytest.fixture(scope="session", name="altadb_api_key")
def altadb_api_key() -> str:
    return ALTADB_API_KEY


@pytest.fixture(scope="session", name="altadb_secret_key")
def altadb_secret_key() -> str:
    return ALTADB_SECRET_KEY


@pytest.fixture(scope="session", name="altadb_url")
def altadb_url() -> str:
    return ALTADB_URL


@pytest.fixture(scope="function", name="context")
def context(
    altadb_api_key: str, altadb_secret_key: str, altadb_url: str
) -> altadb.AltaDBContext:
    context = altadb.AltaDBContext(
        api_key=altadb_api_key,
        secret=altadb_secret_key,
        url=altadb_url,
    )
    altadb._populate_context(context)
    return context
