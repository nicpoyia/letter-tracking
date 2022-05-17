from sqlalchemy.sql import func

from app import db


class Letter(db.Model):
    __tablename__ = "letter"

    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(256), unique=True, index=True)
    status = db.Column(db.String(191))
    final = db.Column(db.Boolean(), index=True, default=False)
    updated = db.Column(db.DateTime(timezone=True),
                        server_default=func.now(),
                        onupdate=func.now(),
                        index=True)

    def get_tracking_number(self) -> bool:
        return self.tracking_number

    def get_status_text(self) -> str:
        return self.status

    def is_final(self) -> bool:
        return self.final

    def get_last_update_timestamp(self) -> bool:
        return self.updated

    def make_final(self) -> None:
        self.final = True
