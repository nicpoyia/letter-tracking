import asyncio
import uuid

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from pytest_httpserver import HTTPServer

from tests.test_fixtures import prepare_mock_la_poste_api, DEFAULT_TRACKING_STATUS_FOR_TESTING


@pytest.mark.asyncio
async def test_get_all_letters_statuses_e2e(
        test_db: SQLAlchemy,
        test_http_server: HTTPServer,
        test_api_client: FlaskClient
):
    # Setup mock server behaviour in response to La Poste API requests (use a mock server)
    # Register letter and update its status in the system
    shipment_id = str(uuid.uuid4())
    first_status = f"Letter status {uuid.uuid4()}"
    prepare_mock_la_poste_api(test_http_server, shipment_id, first_status)
    test_api_client.get(f"/letters/by_ship_id/{shipment_id}")
    # Test the full application using mock dependencies via its HTTP API
    # Setup mock status update when La Poste API is called again
    second_status = DEFAULT_TRACKING_STATUS_FOR_TESTING
    prepare_mock_la_poste_api(test_http_server, shipment_id, second_status)
    # At this point the system does not know about the second status
    # We will use this to evaluate whether the operation is asynchronous
    # The first status (the outdated one) should be returned,
    # because the update operation will begin after the API has been responded
    response_object = test_api_client.get("/letters/all").json
    assert 'status_per_ship_id' in response_object
    status_per_ship_id = response_object['status_per_ship_id']
    assert shipment_id in status_per_ship_id
    assert status_per_ship_id[shipment_id] == first_status
    # Wait for a few seconds and check again
    # Here we intentionally do not check the internal database state, since we are performing end-to-end testing
    await asyncio.sleep(3)
    # Check updated tracking status
    status_per_ship_id = test_api_client.get("/letters/all").json['status_per_ship_id']
    assert status_per_ship_id[shipment_id] == second_status
