import logging
from datetime import datetime
from threading import Thread

import requests
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import false

from app import app, db
from app.models.letter import Letter
from app.models.status_update import StatusUpdate
from .tracking_exception import (
    CannotTrackLetterException,
    CannotUpdateLetterTrackingException,
    InvalidTrackingResponseException
)
from .tracking_response_dto import TrackingResponseDto


class TrackingService:
    # Page size used for paginated retrieval of tracked letters
    __PAGE_SIZE = 100

    # Base URL of tracking API
    api_base_url: str
    # Authorization key for tracking API
    api_key: str

    # Active database session
    db_session: Session
    # Whether the application is running in debug mode
    is_debug: bool

    def __init__(self) -> None:
        super().__init__()
        self.api_base_url = app.config.get('LA_POSTE_API_BASE_URL')
        self.api_key = app.config.get('LA_POSTE_API_KEY')
        self.db_session = db.session
        self.is_debug = app.config.get('APP_DEBUG')

    def track_letter(self, shipment_d: str) -> str:
        """
        Tracks a letter, updates tracking status in database, and returns the latest tracked status
        :param shipment_d: Shipment id of letter
        :return: Latest tracked status of letter
        :raises:
            CannotTrackLetterException: In case of unexpected tracking error
        """
        # Call API and return tracking status
        url = '{b_url}/suivi-unifie/idship/{sh_id}?lang=en_GB'.format(
            b_url=self.api_base_url,
            sh_id=shipment_d
        )
        try:
            response = requests.get(url, headers={'X-Okapi-Key': self.api_key, 'Accept': 'application/json'})
            if response.status_code != 200:
                raise CannotTrackLetterException(
                    "API call unsuccessful with status {resp_code} - \"{resp_mess}\"".format(
                        resp_code=response.status_code,
                        resp_mess=response.text
                    )
                )
            try:
                trackingResponse = TrackingResponseDto.from_json_dict(response.json())
            except InvalidTrackingResponseException:
                raise CannotTrackLetterException("Invalid response from API")
            letter_status = trackingResponse.get_last_event_status()
            try:
                self.__save_letter_tracking_info(shipment_d, letter_status, trackingResponse.is_final)
            except CannotUpdateLetterTrackingException as UpdateException:
                # Log tracking update error for future reference/audit
                logging.error(UpdateException.log_message)
            return letter_status
        except requests.exceptions.ConnectionError as e:
            # Connection exception handling
            if not self.is_debug:
                # While running in testing environment,
                # there may be some API calls without a handling process in place, which is expected
                error_text = str(e)
                logging.error(error_text)
                raise CannotTrackLetterException(error_text)
        except Exception as e:
            if not self.is_debug:
                # Uncaught exception handling
                error_text = str(e)
                logging.error(error_text)
                raise CannotTrackLetterException(error_text)

    def track_all_registered_letters(self) -> dict:
        """
        Tracks all letters that are registered in the database asynchronously,
        i.e. returns the current known status of each letter and then asynchronously updates every letter's status
        :return: Dictionary containing the latest tracked status of each letter
        """
        # Find letters in database that are not final, i.e. there is a potential change of tracking status
        # Tracking the status of only non-final letters is pivotal when it comes to scalability,
        # Since final letters will be piled up more and more in the database, without any potential change in status
        thread = Thread(target=self.track_all_registered_letters_in_database)
        # Return current tracking status
        letter_statuses = {}
        letter_results = Letter.query.order_by(Letter.updated.desc())
        for letter in letter_results:
            letter_statuses[letter.tracking_number] = letter.status
        # Start asynchronous task on return
        thread.start()
        return letter_statuses

    def track_all_registered_letters_in_database(self):
        for batch in self.__get_letter_tracking_batches():
            self.__process_letter_tracking_batch(batch)

    def track_letters_updated_between(self, from_update: datetime, to_update: datetime):
        """
        Tracks letters updated within a date/time range in the database asynchronously,
        i.e. returns the current known status of each letter and then asynchronously updates every letter's status
        :param from_update: Optional update timestamp to filter letters from
        :param to_update: Optional update timestamp to filter letters until
        :return: Dictionary containing the latest tracked status of each letter
        """
        # Find letters in database that are not final, i.e. there is a potential change of tracking status
        # Tracking the status of only non-final letters is pivotal when it comes to scalability,
        # Since final letters will be piled up more and more in the database, without any potential change in status
        thread = Thread(target=self.track_letters_in_range, args=(from_update, to_update))
        # Return current tracking status
        letter_statuses = {}
        letter_results = Letter.query.order_by(Letter.updated.desc()) \
            .filter(Letter.updated >= from_update).filter(Letter.updated <= to_update)
        for letter in letter_results:
            letter_statuses[letter.tracking_number] = letter.status
        # Start asynchronous task on return
        thread.start()
        return letter_statuses

    def track_letters_in_range(self, from_update: datetime, to_update: datetime):
        for batch in self.__get_letter_tracking_batches(from_update, to_update):
            self.__process_letter_tracking_batch(batch)

    def __get_letter_tracking_batches(self, from_update: datetime = None, to_update: datetime = None):
        """
        # Find letters in database that are not final, i.e. there is a potential change of tracking status
        # Tracking the status of only non-final letters is pivotal when it comes to scalability,
        # Since final letters will be piled up more and more in the database, without any potential change in status
        :param from_update: Optional update timestamp to filter letters from
        :param to_update: Optional update timestamp to filter letters until
        :return: Batches of non-final letters to be tracked
        """
        cur_page = 1
        res_count = self.__PAGE_SIZE
        while res_count > 0:
            letterQuery = Letter.query.filter(Letter.final == false())
            if from_update:
                letterQuery = letterQuery.filter(Letter.updated >= from_update)
            if to_update:
                letterQuery = letterQuery.filter(Letter.updated <= to_update)
            next_page = letterQuery.order_by(Letter.id.asc()).paginate(page=cur_page, per_page=self.__PAGE_SIZE)
            res_count = len(next_page.items)
            cur_page += 1
            if res_count > 0:
                yield next_page
            if res_count < self.__PAGE_SIZE:
                break

    def __process_letter_tracking_batch(self, batch):
        for letter in batch.items:
            self.track_letter(letter.tracking_number)

    def __save_letter_tracking_info(self, shipment_id: str, status: str, is_final: bool) -> None:
        """
        Updates the tracking status of a letter in the database
        :param shipment_id: Shipment id of letter
        :param status: Latest tracked status of letter
        :raises:
            CannotUpdateLetterTrackingException: In case of error while updating the tracking status in database
        """
        # Update letter status (and register letter in database if it does not exist)
        existing_letter = Letter.query.filter(Letter.tracking_number == shipment_id).first()
        if not existing_letter:
            letter = Letter(tracking_number=shipment_id, status=status)
        else:
            letter = existing_letter
            letter.status = status
        if is_final:
            letter.make_final()
        # Reload letter entity to get id of letter in database
        self.db_session.add(letter)
        self.db_session.commit()
        self.db_session.refresh(letter)
        # Save status update record (immutable)
        if not letter.id:
            raise CannotUpdateLetterTrackingException("Error while registering letter for tracking")
        new_status_update = StatusUpdate(letter_id=letter.id, status=status)
        self.db_session.add(new_status_update)
        self.db_session.commit()
        StatusUpdate.query.filter(StatusUpdate.letter_id == letter.id)
