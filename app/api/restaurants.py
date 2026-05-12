from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.models.models import User, UserRole
from app.schemas import schemas
from app.crud import restaurant as restaurant_crud
from app.api.deps import get_current_user, check_restaurant_owner, check_admin

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

@router.post("/", response_model=schemas.RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_in: schemas.RestaurantBase, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_restaurant_owner)
):
    """
    Sadece Admin ve Restoran Sahipleri restoran oluşturabilir.
    """
    # owner_id'yi current_user'dan alıyoruz
    return await restaurant_crud.create_restaurant(db, restaurant_in=restaurant_in, owner_id=current_user.id)

@router.get("/", response_model=List[schemas.RestaurantResponse])
async def list_restaurants(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Herkes restoranları listeleyebilir.
    """
    return await restaurant_crud.get_restaurants(db, skip=skip, limit=limit, search=search)

@router.get("/my", response_model=List[schemas.RestaurantResponse])
async def list_my_restaurants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_restaurant_owner)
):
    """
    Sadece restoran sahibi veya admin kendi restoranlarını listeleyebilir.
    """
    if current_user.role == UserRole.admin:
        return await restaurant_crud.get_restaurants(db)
    return await restaurant_crud.get_restaurants_by_owner(db, owner_id=current_user.id)

@router.get("/{restaurant_id}", response_model=schemas.RestaurantResponse)
async def get_restaurant(
    restaurant_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    Herkes bir restoranın detaylarını görebilir.
    """
    restaurant = await restaurant_crud.get_restaurant(db, restaurant_id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restoran bulunamadı.")
    return restaurant

@router.put("/{restaurant_id}", response_model=schemas.RestaurantResponse)
async def update_restaurant(
    restaurant_id: int,
    restaurant_in: schemas.RestaurantBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sadece Admin veya restoranın kendi sahibi güncelleyebilir.
    """
    db_restaurant = await restaurant_crud.get_restaurant(db, restaurant_id=restaurant_id)
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restoran bulunamadı.")
    
    # Yetki kontrolü: Admin değilse ve sahibi değilse hata ver
    if current_user.role != UserRole.admin and db_restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu restoranı güncelleme yetkiniz yok.")
    
    return await restaurant_crud.update_restaurant(db, db_restaurant=db_restaurant, restaurant_in=restaurant_in.dict(exclude_unset=True))

@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sadece Admin veya restoranın kendi sahibi silebilir.
    """
    db_restaurant = await restaurant_crud.get_restaurant(db, restaurant_id=restaurant_id)
    if not db_restaurant:
        raise HTTPException(status_code=404, detail="Restoran bulunamadı.")
    
    # Yetki kontrolü: Admin değilse ve sahibi değilse hata ver
    if current_user.role != UserRole.admin and db_restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu restoranı silme yetkiniz yok.")
    
    await restaurant_crud.remove_restaurant(db, restaurant_id=restaurant_id)
    return None
