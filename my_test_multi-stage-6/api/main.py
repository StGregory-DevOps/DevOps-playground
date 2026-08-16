from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    price = Column(Float, default=0.0)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory API")

class ItemCreate(BaseModel):
    name: str
    quantity: int
    price: float

@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}

@app.get("/items")
def list_items():
    with Session(engine) as session:
        return session.query(Item).all()

@app.post("/items", status_code=201)
def create_item(item: ItemCreate):
    with Session(engine) as session:
        db_item = Item(**item.model_dump())
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item

@app.get("/items/{item_id}")
def get_item(item_id: int):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        session.delete(item)
        session.commit()
