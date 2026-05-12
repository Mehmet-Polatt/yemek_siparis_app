from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from app.models.models import Review, Restaurant, Product
from app.schemas import schemas

async def create_review(db: AsyncSession, review_in: schemas.ReviewCreate, user_id: int) -> Review:
    db_review = Review(
        **review_in.dict(),
        user_id=user_id
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    
    # Restoran veya ürün puanını güncelle
    if review_in.restaurant_id:
        await update_restaurant_rating(db, review_in.restaurant_id)
    elif review_in.product_id:
        # Ürün için de puan sistemi eklenebilir ama şu an Restaurant modelinde rating alanı var
        pass
        
    return db_review

async def get_reviews_by_restaurant(db: AsyncSession, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Review]:
    # Restoranın kendi yorumları + o restorana ait ürünlerin yorumları
    query = select(Review).outerjoin(Product).where(
        (Review.restaurant_id == restaurant_id) | (Product.restaurant_id == restaurant_id)
    )
    result = await db.execute(
        query.order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_reviews_by_product(db: AsyncSession, product_id: int, skip: int = 0, limit: int = 100) -> List[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.product_id == product_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_restaurant_rating(db: AsyncSession, restaurant_id: int):
    # Ortalama puanı hesapla
    result = await db.execute(
        select(func.avg(Review.rating)).where(Review.restaurant_id == restaurant_id)
    )
    avg_rating = result.scalar() or 0.0
    
    # Restoranı güncelle
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    db_restaurant = result.scalars().first()
    if db_restaurant:
        db_restaurant.rating = float(avg_rating)
        db.add(db_restaurant)
        await db.commit()
