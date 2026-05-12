from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import User
from app.schemas import schemas
from app.crud import cart as cart_crud
from app.api.deps import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("/", response_model=schemas.CartResponse)
async def get_my_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kullanıcının sepetini getirir.
    """
    return await cart_crud.get_or_create_cart(db, user_id=current_user.id)

@router.post("/add", response_model=schemas.CartResponse)
async def add_item_to_cart(
    item_in: schemas.CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sepete ürün ekler. Stok kontrolü yapar.
    """
    return await cart_crud.add_to_cart(db, user_id=current_user.id, item_in=item_in)

@router.delete("/item/{item_id}", response_model=schemas.CartResponse)
async def remove_item_from_cart(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sepetten ürün çıkarır.
    """
    return await cart_crud.remove_from_cart(db, user_id=current_user.id, item_id=item_id)
