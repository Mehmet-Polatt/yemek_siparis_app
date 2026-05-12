from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import engine, Base
from app.models import models
from app.api import auth, restaurants, products, orders, cart, reviews

app = FastAPI(title="Yemek Sipariş Uygulaması")

# API Router'lar
app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(cart.router)
app.include_router(reviews.router)

# Static dosyalar için dizinleri oluştur
os.makedirs("frontend/static/css", exist_ok=True)
os.makedirs("frontend/static/js", exist_ok=True)

# Static dosyaları mount et
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

# Uygulama başladığında tabloları oluşturan fonksiyon
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tablolar başarıyla oluşturuldu!")