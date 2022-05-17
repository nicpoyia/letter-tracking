from dateutil import parser
from dateutil.parser import ParserError

from app import app
from app.tracking_service.tracking_exception import CannotTrackLetterException
from app.tracking_service.tracking_service import TrackingService
from app.views.batch_tracking_api_result_dto import BatchTrackingApiResultDto
from app.views.tracking_api_result_dto import TrackingApiResultDto


@app.route("/letters/all", methods=["GET"])
def get_all_letters_statuses():
    trackingService = TrackingService()
    tracking_statuses = trackingService.track_all_registered_letters()
    return BatchTrackingApiResultDto(tracking_statuses).__dict__


@app.route("/letters/by_ship_id/<string:shipment_id>", methods=["GET"])
def get_letter_status(shipment_id: str):
    trackingService = TrackingService()
    try:
        tracking_status = trackingService.track_letter(shipment_id)
    except CannotTrackLetterException as e:
        return f"Cannot track letter due to \"{e.log_message}\"", 422
    return TrackingApiResultDto(tracking_status).__dict__


@app.route("/letters/by_update/<string:from_date>/<string:to_date>", methods=["GET"])
def get_letter_status_updated_within(from_date: str, to_date: str):
    try:
        from_date = parser.parse(from_date)
    except ParserError:
        return "Invalid from-date", 400
    try:
        to_date = parser.parse(to_date)
    except ParserError:
        return "Invalid to-date", 400
    trackingService = TrackingService()
    tracking_statuses = trackingService.track_letters_updated_between(from_date, to_date)
    return BatchTrackingApiResultDto(tracking_statuses).__dict__
