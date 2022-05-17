import asyncio
import uuid
from datetime import datetime, timedelta

import pytest
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from pytest_httpserver import HTTPServer

from tests.test_fixtures import prepare_mock_la_poste_api, DEFAULT_TRACKING_STATUS_FOR_TESTING


def test_get_letter_status_updated_within_bad_request(test_api_client: FlaskClient):
    response = test_api_client.get("/letters/by_update/invalid_timestamp1/invalid_timestamp2")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_letter_status_updated_within(
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
    from_update1 = datetime.utcnow() - timedelta(hours=4)
    to_update1 = datetime.utcnow() + timedelta(minutes=10)
    response_object = test_api_client.get(
        f"/letters/by_update/{from_update1.isoformat()}/{to_update1.isoformat()}").json
    assert 'status_per_ship_id' in response_object
    status_per_ship_id = response_object['status_per_ship_id']
    assert shipment_id in status_per_ship_id
    assert status_per_ship_id[shipment_id] == first_status
    # Wait for a few seconds and check again
    # Here we intentionally do not check the internal database state, since we are performing end-to-end testing
    await asyncio.sleep(3)
    # Check updated tracking status
    status_per_ship_id = test_api_client.get(
        f"/letters/by_update/{from_update1.isoformat()}/{to_update1.isoformat()}").json['status_per_ship_id']
    assert status_per_ship_id[shipment_id] == second_status
    # Check that the letter is not included in the response if out of the timestamp range specified
    from_update2 = datetime.utcnow() + timedelta(minutes=10)
    to_update2 = datetime.utcnow() + timedelta(minutes=20)
    response_object = test_api_client.get(
        f"/letters/by_update/{from_update2.isoformat()}/{to_update2.isoformat()}").json
    assert 'status_per_ship_id' in response_object
    assert not response_object['status_per_ship_id']
