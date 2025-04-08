from aiogram import Router

from app.handlers.catalog import router as catalog_router
from app.handlers.cart import router as cart_router
from app.handlers.order import router as order_router

router = Router()

router.include_router(catalog_router)
router.include_router(cart_router)
router.include_router(order_router)

__all__ = ['router']