import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.cache import get_cached_items, invalidate_items_cache, set_cached_items
from app.database import get_db
from app.models import Item
from app.schemas import ItemOut

router = APIRouter(prefix="/items", tags=["items"])

THUMBNAIL_SIZE = (128, 128)


@router.post("", response_model=ItemOut)
async def create_item(
    name: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents))
        img.thumbnail(THUMBNAIL_SIZE)
        buffer = io.BytesIO()
        img.save(buffer, format=img.format or "PNG")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Некорректное изображение: {exc}")

    item = Item(name=name, thumbnail=buffer.getvalue())
    db.add(item)
    db.commit()
    db.refresh(item)
    invalidate_items_cache()
    return item


@router.get("", response_model=list[ItemOut])
async def list_items(db: Session = Depends(get_db)):
    cached = get_cached_items()
    if cached is not None:
        return cached

    items = db.query(Item).all()
    result = [ItemOut.model_validate(item).model_dump() for item in items]
    set_cached_items(result)
    return items
