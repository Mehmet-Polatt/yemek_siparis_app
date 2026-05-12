from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.models import Order, OrderItem, Product, Cart, CartItem
from app.schemas import schemas
from fastapi import HTTPException

async def get_order(db: AsyncSession, order_id: int) -> Optional[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    return result.scalars().first()

async def get_user_orders(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_restaurant_orders(db: AsyncSession, restaurant_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.restaurant_id == restaurant_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_order(db: AsyncSession, order_in: schemas.OrderCreate, user_id: int) -> Order:
    # Toplam fiyatı hesapla ve ürünleri kontrol et
    total_price = 0.0
    order_items_data = []
    
    for item in order_in.items:
        # Ürünü veritabanından al (fiyatı doğrulamak için)
        product_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalars().first()
        if not product:
            continue
        
        item_total = product.price * item.quantity
        total_price += item_total
        
        order_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": product.price
        })

    # Ana siparişi oluştur
    db_order = Order(
        user_id=user_id,
        restaurant_id=order_in.restaurant_id,
        total_price=total_price
    )
    db.add(db_order)
    await db.flush()

    # Sipariş kalemlerini oluştur
    for item_data in order_items_data:
        db_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_item)

    await db.commit()
    await db.refresh(db_order)
    return await get_order(db, db_order.id)

async def process_checkout(db: AsyncSession, user_id: int, cart: Cart) -> Order:
    """
    Sepetteki ürünleri siparişe dönüştürür ve stoktan düşer.
    Bu aşamaya gelindiğinde ödemenin başarılı olduğu varsayılır.
    """
    if not cart.items:
        raise HTTPException(status_code=400, detail="Sepetiniz boş.")

    # Sipariş için restoran bilgisini ilk üründen alalım
    first_product = cart.items[0].product
    restaurant_id = first_product.restaurant_id
    
    total_price = 0.0
    order_items_data = []

    for item in cart.items:
        product = item.product
        
        # Stok kontrolü
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Üzgünüz, {product.name} için stok yetersiz. Mevcut: {product.stock}")
        
        # Stoktan düş
        product.stock -= item.quantity
        db.add(product)

        item_total = product.price * item.quantity
        total_price += item_total
        
        order_items_data.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price": product.price
        })

    # Sipariş oluştur
    db_order = Order(
        user_id=user_id,
        restaurant_id=restaurant_id,
        total_price=total_price
    )
    db.add(db_order)
    await db.flush()

    for item_data in order_items_data:
        db_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_item)

    await db.commit()
    await db.refresh(db_order)
    return await get_order(db, db_order.id)
