import random

async def process_payment(card_number: str, amount: float) -> bool:
    """
    Basit sahte ödeme sistemi.
    Gerçek dünyada burada bir ödeme gateway'ine istek atılırdı.
    """
    # Rastgele %90 başarı oranı verelim (veya istersen hep başarılı yapabiliriz)
    success = random.random() < 0.9
    return success
