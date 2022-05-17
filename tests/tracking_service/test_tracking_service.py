import time
import uuid
from datetime import datetime, timedelta

import pytest
from flask_sqlalchemy import SQLAlchemy
from pytest_httpserver import HTTPServer

import app
from app.models.letter import Letter
from app.models.status_update import StatusUpdate
from app.tracking_service.tracking_service import TrackingService
from tests.test_fixtures import prepare_mock_la_poste_api, DEFAULT_TRACKING_STATUS_FOR_TESTING


def get_is_final():
    return [False, True]


@pytest.mark.parametrize("is_final", get_is_final())
def test_track_letter(test_db: SQLAlchemy, httpserver: HTTPServer, is_final: bool):
    # Setup mock server behaviour in response to La Poste API requests (use a mock server)
    shipment_id = str(uuid.uuid4())
    latest_status = f"Letter status {uuid.uuid4()}"
    latest_event_date = datetime.now().isoformat()
    prepare_mock_la_poste_api(httpserver, shipment_id, latest_status, latest_event_date)
    # Track a letter using the service under test
    test_tracking_service = TrackingService()
    returned_status = test_tracking_service.track_letter(shipment_id)
    assert returned_status == latest_status
    # Check if the letter has been registered and the status was updated
    letter_results = test_db.session.query(Letter).filter_by(tracking_number=shipment_id).all()
    assert len(letter_results) == 1
    assert letter_results[0].status == returned_status
    assert not letter_results[0].final
    # Check if a record has been added in the status-update history
    status_update_results = test_db.session.query(StatusUpdate).filter_by(letter_id=letter_results[0].id).all()
    assert len(status_update_results) == 1
    assert status_update_results[0].status == returned_status


def test_track_all_registered_letters(test_db: SQLAlchemy, httpserver: HTTPServer):
    # Setup mock server behaviour in response to La Poste API requests (use a mock server)
    # Register letter and update its status in the system
    shipment_id = str(uuid.uuid4())
    letter_first_status = f"Letter status {uuid.uuid4()}"
    latest_event_date = datetime.now().isoformat()
    prepare_mock_la_poste_api(httpserver, shipment_id, letter_first_status, latest_event_date)
    test_tracking_service = TrackingService()
    returned_status = test_tracking_service.track_letter(shipment_id)
    assert returned_status == letter_first_status
    # Setup mock status update when La Poste API is called again
    letter_second_status = DEFAULT_TRACKING_STATUS_FOR_TESTING
    prepare_mock_la_poste_api(httpserver, shipment_id, letter_second_status)
    # At this point the system does not know about the second status
    # We will use this to evaluate whether the operation is asynchronous
    # The first status (the outdated one) should be returned,
    # because the update operation will begin after the service has been responded
    all_returned_statuses = test_tracking_service.track_all_registered_letters()
    assert shipment_id in all_returned_statuses
    assert all_returned_statuses[shipment_id] == letter_first_status
    # Wait until the letter is updated in the database and check the updated status
    new_letter_status = __detect_status_change_in_database(shipment_id, letter_first_status)
    assert new_letter_status == letter_second_status


def test_track_letters_updated_between(test_db: SQLAlchemy, httpserver: HTTPServer):
    # Setup mock server behaviour in response to La Poste API requests (use a mock server)
    # Register letter and update its status in the system
    shipment_id = str(uuid.uuid4())
    letter_first_status = f"Letter status {uuid.uuid4()}"
    latest_event_date = datetime.now().isoformat()
    prepare_mock_la_poste_api(httpserver, shipment_id, letter_first_status, latest_event_date)
    test_tracking_service = TrackingService()
    returned_status = test_tracking_service.track_letter(shipment_id)
    assert returned_status == letter_first_status
    # Setup mock status update when La Poste API is called again
    letter_second_status = DEFAULT_TRACKING_STATUS_FOR_TESTING
    prepare_mock_la_poste_api(httpserver, shipment_id, letter_second_status)
    # At this point the system does not know about the second status
    # We will use this to evaluate whether the operation is asynchronous
    # The first status (the outdated one) should be returned,
    # because the update operation will begin after the service has been responded
    from_update1 = datetime.utcnow() - timedelta(hours=4)
    to_update1 = datetime.utcnow() + timedelta(minutes=10)
    all_returned_statuses = test_tracking_service.track_letters_updated_between(from_update1, to_update1)
    assert shipment_id in all_returned_statuses
    assert all_returned_statuses[shipment_id] == letter_first_status
    # Wait until the letter is updated in the database and check the updated status
    new_letter_status = __detect_status_change_in_database(shipment_id, letter_first_status)
    assert new_letter_status == letter_second_status
    # Check that the letter is not included in the results if out of the timestamp range specified
    from_update2 = datetime.utcnow() + timedelta(minutes=10)
    to_update2 = datetime.utcnow() + timedelta(minutes=20)
    assert not test_tracking_service.track_letters_updated_between(from_update2, to_update2)


def __detect_status_change_in_database(shipment_id: str, previous_status: str, timeout=3):
    try_until = time.time() + timeout
    while time.time() < try_until:
        letter = Letter.query.filter(Letter.tracking_number == shipment_id)[0]
        app.db.session.refresh(letter)
        if letter.status != previous_status:
            return letter.status
        time.sleep(0.1)
