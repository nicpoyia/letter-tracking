import os.path
import re
import uuid
from datetime import datetime

import pytest
from alembic import command
from alembic.config import Config
from pytest_httpserver import HTTPServer

from app import app, db

DEFAULT_TRACKING_STATUS_FOR_TESTING = 'THIS IS A DEFAULT TRACKING STATUS FOR TESTING'


@pytest.fixture()
def test_app():
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///../local_testing/testing.db",
        "LA_POSTE_API_BASE_URL": "http://localhost:12312/mock-la-poste-api",
        "LA_POSTE_API_KEY": "mock_api_key"
    })
    yield app


@pytest.fixture(scope="session")
def httpserver_listen_address():
    # Configure mock HTTP server
    return "127.0.0.1", 12312


@pytest.fixture()
def test_api_client(test_app):
    return test_app.test_client()


@pytest.fixture()
def test_db(test_app):
    # Run database migrations on testing database (prepare schema)
    with test_app.app_context():
        config = Config(os.path.dirname(os.path.abspath(__file__)) + "/../migrations/alembic.ini")
        config.set_main_option("script_location", os.path.dirname(os.path.abspath(__file__)) + "/../migrations")
        command.upgrade(config, "head")
    # Provide testing database
    yield db
    # Close connection after tests are finshed
    db.session.close()


@pytest.fixture()
def test_http_server(httpserver: HTTPServer) -> HTTPServer:
    # Set up a default request handling for testing purposes
    default_response_object = {'shipment': {'isFinal': False, 'event': [
        {'date': datetime.now().isoformat(), 'label': DEFAULT_TRACKING_STATUS_FOR_TESTING}
    ]}}
    httpserver.expect_request(re.compile("/mock-la-poste-api/suivi-unifie/idship/.+")) \
        .respond_with_json(default_response_object)
    return httpserver


def prepare_mock_la_poste_api(httpserver: HTTPServer,
                              shipment_id: str,
                              latest_status: str = None,
                              latest_event_date: str = None):
    latest_status = latest_status or f"Letter status {uuid.uuid4()}"
    latest_event_date = latest_event_date or datetime.now().isoformat()
    responseObject = {'shipment': {'isFinal': False, 'event': [{'date': latest_event_date, 'label': latest_status}]}}
    httpserver.clear()
    httpserver.expect_request(f"/mock-la-poste-api/suivi-unifie/idship/{shipment_id}").respond_with_json(responseObject)
