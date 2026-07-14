from datetime import datetime
from app.database import db

class Link(db.Model):
    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clicks = db.relationship("Click", backref="link", lazy=True)


class Click(db.Model):
    __tablename__ = "clicks"

    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey("links.id"), nullable=False)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
