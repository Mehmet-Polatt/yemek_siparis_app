from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.models import Restaurant
from app.schemas import schemas

async def get_restaurant(db: AsyncSession, restaurant_id: int) -> Optional[Restaurant]:
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    return result.scalars().first()

async def get_restaurants(db: AsyncSession, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Restaurant]:
    query = select(Restaurant)
    if search:
        query = query.where(Restaurant.name.ilike(f"%{search}%"))
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def get_restaurants_by_owner(db: AsyncSession, owner_id: int) -> List[Restaurant]:
    result = await db.execute(select(Restaurant).where(Restaurant.owner_id == owner_id))
    return result.scalars().all()

async def create_restaurant(db: AsyncSession, restaurant_in: schemas.RestaurantBase, owner_id: int) -> Restaurant:
    db_restaurant = Restaurant(
        name=restaurant_in.name,
        address=restaurant_in.address,
        description=restaurant_in.description,
        logo_url=restaurant_in.logo_url,
        owner_id=owner_id
    )
    db.add(db_restaurant)
    await db.commit()
    await db.refresh(db_restaurant)
    return db_restaurant

async def update_restaurant(db: AsyncSession, db_restaurant: Restaurant, restaurant_in: dict) -> Restaurant:
    for field, value in restaurant_in.items():
        setattr(db_restaurant, field, value)
    
    db.add(db_restaurant)
    await db.commit()
    await db.refresh(db_restaurant)
    return db_restaurant

async def remove_restaurant(db: AsyncSession, restaurant_id: int) -> Optional[Restaurant]:
    result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    db_restaurant = result.scalars().first()
    if db_restaurant:
        await db.delete(db_restaurant)
        await db.commit()
    return db_restaurant
