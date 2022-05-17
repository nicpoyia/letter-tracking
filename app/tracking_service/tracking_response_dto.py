from datetime import datetime
from typing import List

from .tracking_exception import InvalidTrackingResponseException, NoTrackingEventException


class _TrackingEventDto:
    date: datetime
    label: str

    def __init__(self, date: datetime, label: str) -> None:
        super().__init__()
        self.date = date
        self.label = label

    @staticmethod
    def from_json_dict(json_dict):
        """
        Factory method which generates an object of the class by using the received raw JSON data
        :param json_dict: Dictionary with JSON data
        :return: _TrackingEventDto
        :raises:
             InvalidTrackingResponseException: In case of invalid payload received in the response
        """
        date = json_dict.get('date')
        if not date:
            raise InvalidTrackingResponseException("event.date")
        label = json_dict.get('label')
        if not label:
            raise InvalidTrackingResponseException("event.label")
        return _TrackingEventDto(date, label)


class TrackingResponseDto:
    # Whether the tracking is final, i.e. no further changes will apply
    is_final: bool
    # Tracking events in anti-chronological order
    events: List[_TrackingEventDto]

    def __init__(self, is_final: bool, events: List[_TrackingEventDto]) -> None:
        super().__init__()
        self.is_final = is_final
        self.events = events
        self.events.sort(key=lambda ev: ev.date, reverse=True)

    @staticmethod
    def from_json_dict(json_dict):
        """
        Factory method which generates an object of the class by using the received raw JSON data
        :param json_dict: Dictionary with JSON data
        :return: TrackingResponseDto
        :raises:
             InvalidTrackingResponseException: In case of invalid payload received in the response
        """
        shipment_obj = json_dict.get('shipment')
        if not shipment_obj:
            raise InvalidTrackingResponseException("shipment")
        if 'event' not in shipment_obj:
            raise InvalidTrackingResponseException("event")
        events_data_list = shipment_obj.get('event')
        events_list = [_TrackingEventDto.from_json_dict(event_dict) for event_dict in events_data_list]
        return TrackingResponseDto(
            is_final=shipment_obj.get('isFinal'),
            events=events_list
        )

    def get_last_event_status(self) -> str:
        """
        :return: Status label of last tracking event
        :raises:
            NoTrackingEventException If no event is available
        """
        if not self.events:
            raise NoTrackingEventException()
        return self.events[0].label
