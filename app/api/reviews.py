from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.models.models import User
from app.schemas import schemas
from app.crud import review as review_crud
from app.api.deps import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_in: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kullanıcılar restoran veya ürün için yorum yapabilir.
    """
    if not review_in.restaurant_id and not review_in.product_id:
        raise HTTPException(status_code=400, detail="Restoran veya ürün ID'si gereklidir.")
    
    return await review_crud.create_review(db, review_in=review_in, user_id=current_user.id)

@router.get("/restaurant/{restaurant_id}", response_model=List[schemas.ReviewResponse])
async def list_reviews_by_restaurant(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Bir restorana ait yorumları listeler.
    """
    return await review_crud.get_reviews_by_restaurant(db, restaurant_id=restaurant_id, skip=skip, limit=limit)

@router.get("/product/{product_id}", response_model=List[schemas.ReviewResponse])
async def list_reviews_by_product(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Bir ürüne ait yorumları listeler.
    """
    return await review_crud.get_reviews_by_product(db, product_id=product_id, skip=skip, limit=limit)
