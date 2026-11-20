from datetime import datetime, timezone

from converter import db


class ConversionJob(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    source_extension = db.Column(db.String(10), nullable=False)
    source_kind = db.Column(db.String(10), nullable=False)
    output_format = db.Column(db.String(10), nullable=False)
    duration_seconds = db.Column(db.Float, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
