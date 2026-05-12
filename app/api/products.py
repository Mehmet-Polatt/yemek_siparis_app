from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.models.models import User, UserRole
from app.schemas import schemas
from app.crud import product as product_crud
from app.crud import restaurant as restaurant_crud
from app.api.deps import get_current_user, check_restaurant_owner

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_restaurant_owner)
):
    """
    Sadece Admin veya ilgili restoranın sahibi ürün ekleyebilir.
    """
    # Restoranı kontrol et
    restaurant = await restaurant_crud.get_restaurant(db, restaurant_id=product_in.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restoran bulunamadı.")
    
    # Yetki kontrolü
    if current_user.role != UserRole.admin and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu restorana ürün ekleme yetkiniz yok.")
    
    return await product_crud.create_product(db, product_in=product_in)

@router.get("/", response_model=List[schemas.ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Ürünleri herkes listeleyebilir ve arayabilir.
    """
    return await product_crud.get_products(db, skip=skip, limit=limit, search=search)

@router.get("/restaurant/{restaurant_id}", response_model=List[schemas.ProductResponse])
async def list_products_by_restaurant(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Bir restorana ait ürünleri herkes listeleyebilir.
    """
    return await product_crud.get_products_by_restaurant(db, restaurant_id=restaurant_id, skip=skip, limit=limit, search=search)

@router.get("/{product_id}", response_model=schemas.ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Ürün detaylarını herkes görebilir.
    """
    product = await product_crud.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    return product

@router.put("/{product_id}", response_model=schemas.ProductResponse)
async def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_restaurant_owner)
):
    """
    Sadece Admin veya ürünün sahibi olduğu restoranın sahibi güncelleyebilir.
    """
    db_product = await product_crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    
    # Ürünün ait olduğu restoranı bul
    restaurant = await restaurant_crud.get_restaurant(db, restaurant_id=db_product.restaurant_id)
    
    # Yetki kontrolü
    if current_user.role != UserRole.admin and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu ürünü güncelleme yetkiniz yok.")
    
    return await product_crud.update_product(
        db, db_product=db_product, product_in=product_in.dict(exclude_unset=True)
    )

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_restaurant_owner)
):
    """
    Sadece Admin veya ürünün sahibi olduğu restoranın sahibi silebilir.
    """
    db_product = await product_crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    
    # Ürünün ait olduğu restoranı bul
    restaurant = await restaurant_crud.get_restaurant(db, restaurant_id=db_product.restaurant_id)
    
    # Yetki kontrolü
    if current_user.role != UserRole.admin and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu ürünü silme yetkiniz yok.")
    
    await product_crud.remove_product(db, product_id=product_id)
    return None
