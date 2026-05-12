from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional
from app.models.models import Cart, CartItem, Product
from app.schemas import schemas
from fastapi import HTTPException

async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    db_cart = result.scalars().first()
    
    if not db_cart:
        db_cart = Cart(user_id=user_id)
        db.add(db_cart)
        await db.commit()
        await db.refresh(db_cart)
    
    return db_cart

async def add_to_cart(db: AsyncSession, user_id: int, item_in: schemas.CartItemCreate) -> Cart:
    # Ürünü ve stok durumunu kontrol et
    product_result = await db.execute(select(Product).where(Product.id == item_in.product_id))
    product = product_result.scalars().first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    
    if product.stock < item_in.quantity:
        raise HTTPException(status_code=400, detail=f"Yetersiz stok. Mevcut stok: {product.stock}")

    db_cart = await get_or_create_cart(db, user_id)
    
    # Sepette zaten var mı kontrol et
    result = await db.execute(
        select(CartItem)
        .where(CartItem.cart_id == db_cart.id, CartItem.product_id == item_in.product_id)
    )
    existing_item = result.scalars().first()
    
    if existing_item:
        new_quantity = existing_item.quantity + item_in.quantity
        if product.stock < new_quantity:
            raise HTTPException(status_code=400, detail=f"Sepetteki toplam miktar stok limitini aşıyor. Mevcut stok: {product.stock}")
        existing_item.quantity = new_quantity
    else:
        db_item = CartItem(
            cart_id=db_cart.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(db_item)
    
    await db.commit()
    return await get_or_create_cart(db, user_id)

async def remove_from_cart(db: AsyncSession, user_id: int, item_id: int) -> Cart:
    db_cart = await get_or_create_cart(db, user_id)
    
    result = await db.execute(
        select(CartItem)
        .where(CartItem.id == item_id, CartItem.cart_id == db_cart.id)
    )
    db_item = result.scalars().first()
    
    if db_item:
        if db_item.quantity > 1:
            db_item.quantity -= 1
        else:
            await db.delete(db_item)
        await db.commit()
    
    return await get_or_create_cart(db, user_id)

async def clear_cart(db: AsyncSession, cart_id: int):
    # Bu fonksiyon genellikle sipariş tamamlandıktan sonra çağrılır
    # CartItem'ları siler
    from sqlalchemy import delete
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
    await db.commit()
