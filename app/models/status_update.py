from sqlalchemy import ForeignKey
from sqlalchemy.sql import func

from app import db


class StatusUpdate(db.Model):
    __tablename__ = "status_history"

    id = db.Column(db.Integer, primary_key=True)
    letter_id = db.Column(db.Integer, ForeignKey('letter.id'), index=True)
    status = db.Column(db.String(191))
    timestamp_tracked = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def get_letter_id(self) -> str:
        return self.letter_id

    def get_status_text(self) -> str:
        return self.status

    def get_tracking_timestamp(self) -> bool:
        return self.timestamp_tracked
