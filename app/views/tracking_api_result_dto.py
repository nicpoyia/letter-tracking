class TrackingApiResultDto:
    status: str

    def __init__(self, status: str) -> None:
        self.status = status
