from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.models import Product
from app.schemas import schemas

async def get_product(db: AsyncSession, product_id: int) -> Optional[Product]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalars().first()

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Product]:
    query = select(Product)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def get_products_by_restaurant(db: AsyncSession, restaurant_id: int, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Product]:
    query = select(Product).where(Product.restaurant_id == restaurant_id)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    result = await db.execute(
        query.offset(skip).limit(limit)
    )
    return result.scalars().all()

async def create_product(db: AsyncSession, product_in: schemas.ProductCreate) -> Product:
    db_product = Product(
        name=product_in.name,
        price=product_in.price,
        description=product_in.description,
        stock=product_in.stock,
        image_url=product_in.image_url,
        restaurant_id=product_in.restaurant_id
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

async def update_product(db: AsyncSession, db_product: Product, product_in: dict) -> Product:
    for field, value in product_in.items():
        setattr(db_product, field, value)
    
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

async def remove_product(db: AsyncSession, product_id: int) -> Optional[Product]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalars().first()
    if db_product:
        await db.delete(db_product)
        await db.commit()
    return db_product
