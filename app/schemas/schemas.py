from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from app.models.models import UserRole, OrderStatus

# --- Restoran Şemaları ---
class RestaurantBase(BaseModel):
    name: str
    address: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    owner_id: int

class ReviewBase(BaseModel):
    rating: int
    comment: str
    restaurant_id: Optional[int] = None
    product_id: Optional[int] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    created_at: datetime
    # Opsiyonel olarak kullanıcı adını da dönebiliriz (UserResponse ile)
    # user: UserResponse 

    class Config:
        from_attributes = True

class RestaurantResponse(RestaurantBase):
    id: int
    owner_id: int
    rating: float
    # reviews: List[ReviewResponse] = []

    class Config:
        from_attributes = True

# --- Ürün Şemaları ---
class ProductBase(BaseModel):
    name: str
    price: float
    description: str
    stock: int
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    restaurant_id: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    restaurant_id: int
    # reviews: List[ReviewResponse] = []

    class Config:
        from_attributes = True

# --- Sipariş Şemaları ---
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    price: float
    product: ProductResponse

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    restaurant_id: int

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderResponse(OrderBase):
    id: int
    user_id: int
    total_price: float
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

# --- Sepet Şemaları ---
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ProductResponse

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    items: List[CartItemResponse]

    class Config:
        from_attributes = True

# --- Ödeme Şemaları ---
class PaymentRequest(BaseModel):
    card_number: str
    expiry_date: str
    cvv: str

# --- Kullanıcı Şemaları ---
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: UserRole

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str