from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# --- Book ---

class BookCreate(BaseModel):
    title: str
    author: str
    year: int


class Book(BaseModel):
    id: int
    title: str
    author: str
    year: int
    available: bool

    class Config:
        from_attributes = True


# --- Reader ---

class ReaderCreate(BaseModel):
    name: str
    email: EmailStr


class Reader(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


# --- Rental ---

class RentalCreate(BaseModel):
    book_id: int
    reader_id: int
    due_date: datetime


class Rental(BaseModel):
    id: int
    book_id: int
    reader_id: int
    rented_at: datetime
    due_date: datetime
    returned_at: Optional[datetime] = None

    class Config:
        from_attributes = True
