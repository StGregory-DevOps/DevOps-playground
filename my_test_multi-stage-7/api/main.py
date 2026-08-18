from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import models, schemas, crud
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Library API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Books ---

@app.post("/books/", response_model=schemas.Book, status_code=201)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.create_book(db, book)


@app.get("/books/", response_model=List[schemas.Book])
def list_books(db: Session = Depends(get_db)):
    return crud.get_books(db)


@app.get("/books/{book_id}", response_model=schemas.Book)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    if not crud.delete_book(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")


# --- Readers ---

@app.post("/readers/", response_model=schemas.Reader, status_code=201)
def create_reader(reader: schemas.ReaderCreate, db: Session = Depends(get_db)):
    return crud.create_reader(db, reader)


@app.get("/readers/", response_model=List[schemas.Reader])
def list_readers(db: Session = Depends(get_db)):
    return crud.get_readers(db)


@app.get("/readers/{reader_id}", response_model=schemas.Reader)
def get_reader(reader_id: int, db: Session = Depends(get_db)):
    reader = crud.get_reader(db, reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")
    return reader


# --- Rentals ---

@app.post("/rentals/", response_model=schemas.Rental, status_code=201)
def create_rental(rental: schemas.RentalCreate, db: Session = Depends(get_db)):
    book = crud.get_book(db, rental.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not book.available:
        raise HTTPException(status_code=400, detail="Book is not available")
    reader = crud.get_reader(db, rental.reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")
    return crud.create_rental(db, rental)


@app.get("/rentals/", response_model=List[schemas.Rental])
def list_rentals(db: Session = Depends(get_db)):
    return crud.get_rentals(db)


@app.patch("/rentals/{rental_id}/return", response_model=schemas.Rental)
def return_book(rental_id: int, db: Session = Depends(get_db)):
    rental = crud.return_rental(db, rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental


@app.get("/rentals/overdue/", response_model=List[schemas.Rental])
def list_overdue(db: Session = Depends(get_db)):
    return crud.get_overdue_rentals(db)
