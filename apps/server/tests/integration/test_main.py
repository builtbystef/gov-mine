import logging
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"app": "Test API"}


def test_openapi_operation_ids(client: TestClient):
    schema = client.get("/openapi.json").json()
    assert schema["paths"]["/"]["get"]["operationId"] == "read_root"
    assert schema["paths"]["/health/"]["get"]["operationId"] == "health-read_health"
    assert schema["paths"]["/health/db"]["get"]["operationId"] == "health-read_health_db"


def test_real_app_answers_with_a_request_id(client: TestClient):
    response = client.get("/health/")
    assert response.status_code == 200
    assert len(response.headers["x-request-id"]) == 16


def test_health_checks_are_not_in_the_access_log(
    client: TestClient, caplog: pytest.LogCaptureFixture
):
    with caplog.at_level(logging.INFO, logger="gov_mine.access"):
        client.get("/health/")
        client.get("/")
    assert [r.getMessage()[:6] for r in caplog.records if r.name == "gov_mine.access"] == ["GET / "]
