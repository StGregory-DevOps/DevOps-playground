from sqlalchemy import Column, Integer, String, LargeBinary

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    thumbnail = Column(LargeBinary, nullable=True)
