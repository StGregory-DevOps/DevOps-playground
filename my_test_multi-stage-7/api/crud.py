from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
import models, schemas


# --- Books ---

def create_book(db: Session, book: schemas.BookCreate) -> models.Book:
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def get_books(db: Session):
    return db.query(models.Book).all()


def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def delete_book(db: Session, book_id: int) -> bool:
    book = get_book(db, book_id)
    if not book:
        return False
    db.delete(book)
    db.commit()
    return True


# --- Readers ---

def create_reader(db: Session, reader: schemas.ReaderCreate) -> models.Reader:
    db_reader = models.Reader(**reader.model_dump())
    db.add(db_reader)
    db.commit()
    db.refresh(db_reader)
    return db_reader


def get_readers(db: Session):
    return db.query(models.Reader).all()


def get_reader(db: Session, reader_id: int):
    return db.query(models.Reader).filter(models.Reader.id == reader_id).first()


# --- Rentals ---

def create_rental(db: Session, rental: schemas.RentalCreate) -> models.Rental:
    db_rental = models.Rental(**rental.model_dump())
    db.add(db_rental)
    # Mark book as unavailable
    book = get_book(db, rental.book_id)
    book.available = False
    db.commit()
    db.refresh(db_rental)
    return db_rental


def get_rentals(db: Session):
    return db.query(models.Rental).all()


def return_rental(db: Session, rental_id: int):
    rental = db.query(models.Rental).filter(models.Rental.id == rental_id).first()
    if not rental:
        return None
    rental.returned_at = datetime.now(timezone.utc)
    # Mark book as available again
    book = get_book(db, rental.book_id)
    book.available = True
    db.commit()
    db.refresh(rental)
    return rental


def get_overdue_rentals(db: Session):
    now = datetime.now(timezone.utc)
    return db.query(models.Rental).filter(
        models.Rental.due_date < now,
        models.Rental.returned_at.is_(None)
    ).all()
