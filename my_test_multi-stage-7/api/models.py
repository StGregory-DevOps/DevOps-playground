from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    available = Column(Boolean, default=True)

    rentals = relationship("Rental", back_populates="book")


class Reader(Base):
    __tablename__ = "readers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)

    rentals = relationship("Rental", back_populates="reader")


class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    reader_id = Column(Integer, ForeignKey("readers.id"), nullable=False)
    rented_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)

    book = relationship("Book", back_populates="rentals")
    reader = relationship("Reader", back_populates="rentals")
