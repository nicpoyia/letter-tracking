import uuid

from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from pytest_httpserver import HTTPServer

from tests.test_fixtures import prepare_mock_la_poste_api


def test_get_letter_status_e2e(test_db: SQLAlchemy, httpserver: HTTPServer, test_api_client: FlaskClient):
    # Setup mock server behaviour in response to La Poste API requests (use a mock server)
    shipment_id = str(uuid.uuid4())
    latest_status = f"Letter status {uuid.uuid4()}"
    prepare_mock_la_poste_api(httpserver, shipment_id, latest_status)
    # Test the full application using mock dependencies via its HTTP API
    response = test_api_client.get(f"/letters/by_ship_id/{shipment_id}")
    response_object = response.json
    assert response_object['status'] == latest_status
