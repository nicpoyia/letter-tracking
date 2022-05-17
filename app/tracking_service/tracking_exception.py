class CannotTrackLetterException(Exception):
    def __init__(self, log_message: str):
        self.log_message = log_message


class CannotUpdateLetterTrackingException(Exception):
    def __init__(self, log_message: str):
        self.log_message = log_message


class InvalidTrackingResponseException(Exception):
    def __init__(self, invalid_object: str):
        self.invalid_object = invalid_object


class NoTrackingEventException(Exception):
    pass
