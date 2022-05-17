class BatchTrackingApiResultDto:
    status_per_ship_id: dict

    def __init__(self, status_per_ship_id: dict) -> None:
        self.status_per_ship_id = status_per_ship_id
