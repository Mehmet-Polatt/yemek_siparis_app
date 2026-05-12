from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import User
from app.schemas import schemas
from app.crud import user as user_crud
from app.core import security
from app.core.config import settings
from datetime import timedelta
from app.api.deps import get_current_user, oauth2_scheme

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Bu e-posta adresi zaten kullanımda."
        )
    return await user_crud.create_user(db, user=user_in)

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı e-posta veya şifre.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/update-password")
async def update_password(
    data: schemas.PasswordUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not security.verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifreniz hatalı.")
    
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Yeni şifreler eşleşmiyor.")
    
    await user_crud.update_user_password(db, db_user=current_user, new_password=data.new_password)
    return {"message": "Şifreniz başarıyla güncellendi."}

@router.post("/password-reset-request")
async def password_reset_request(request: schemas.PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_user_by_email(db, email=request.email)
    if not user:
        # Güvenlik nedeniyle kullanıcı yoksa da başarılı dönebiliriz ama basitlik için hata verelim.
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    
    # Şifre sıfırlama tokenı oluştur (15 dakikalık)
    reset_token = security.create_access_token(
        subject=user.email, 
        expires_delta=timedelta(minutes=15)
    )
    
    # Burada normalde e-posta gönderilir.
    print(f"DEBUG: Şifre sıfırlama tokenı (Email: {user.email}): {reset_token}")
    
    return {"message": "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi (Simüle edildi).", "token": reset_token}

@router.post("/password-reset-confirm")
async def password_reset_confirm(confirm: schemas.PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    try:
        from jose import jwt
        payload = jwt.decode(confirm.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Geçersiz token.")
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş token.")
    
    user = await user_crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    
    await user_crud.update_user_password(db, db_user=user, new_password=confirm.new_password)
    return {"message": "Şifreniz başarıyla güncellendi."}
