from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.models.models import User, UserRole
from app.schemas import schemas
from app.crud import order as order_crud
from app.crud import restaurant as restaurant_crud
from app.api.deps import get_current_user, check_restaurant_owner
from app.core.payment import process_payment
from app.crud import cart as cart_crud

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/checkout", response_model=schemas.OrderResponse)
async def checkout(
    payment_in: schemas.PaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sepetteki ürünlerle siparişi tamamlar. 
    Stok kontrolü yapılır ve sahte ödeme sistemi çalıştırılır.
    """
    cart = await cart_crud.get_or_create_cart(db, user_id=current_user.id)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Sepetiniz boş.")
    
    # Toplam tutarı hesapla (Sadece ödeme simülasyonu için)
    total_amount = sum(item.product.price * item.quantity for item in cart.items)
    
    # Sahte ödeme sistemini çağır
    payment_success = await process_payment(payment_in.card_number, total_amount)
    
    if not payment_success:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, 
            detail="Ödeme başarısız oldu. Lütfen kart bilgilerinizi kontrol edin."
        )
    
    # Ödeme başarılı, siparişi oluştur ve stoktan düş
    order = await order_crud.process_checkout(db, user_id=current_user.id, cart=cart)
    
    # Sepeti temizle
    await cart_crud.clear_cart(db, cart_id=cart.id)
    
    return order

@router.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    order_in: schemas.OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Herhangi bir giriş yapmış kullanıcı sipariş verebilir.
    """
    return await order_crud.create_order(db, order_in=order_in, user_id=current_user.id)

@router.get("/me", response_model=List[schemas.OrderResponse])
async def get_my_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Müşteri kendi sipariş geçmişini görür.
    """
    return await order_crud.get_user_orders(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/restaurant/{restaurant_id}", response_model=List[schemas.OrderResponse])
async def get_restaurant_order_history(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_restaurant_owner)
):
    """
    Sadece Admin veya restoranın sahibi kendi restoranına gelen siparişleri görebilir.
    """
    restaurant = await restaurant_crud.get_restaurant(db, restaurant_id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restoran bulunamadı.")
    
    # Yetki kontrolü
    if current_user.role != UserRole.admin and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu restoranın siparişlerini görme yetkiniz yok.")
    
    return await order_crud.get_restaurant_orders(db, restaurant_id=restaurant_id, skip=skip, limit=limit)
