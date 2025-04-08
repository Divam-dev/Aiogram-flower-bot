from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.keyboards import get_cart_kb, get_menu_kb
from data_handler import get_flower_price, currency_convert
from app.handlers.common import OrderStates, carts

router = Router()

@router.message(F.text == "🛒 Переглянути кошик")
async def view_cart(message: Message, state: FSMContext):
    chat_id = message.chat.id
    await state.set_state(OrderStates.viewing_cart)
    
    if chat_id not in carts or not carts[chat_id]:
        await message.answer("🛒 Ваш кошик порожній!", reply_markup=get_cart_kb())
        return
    
    data = await state.get_data()
    is_uah = data.get("currency") == "UAH🇺🇦"
    currency_symbol = "₴" if is_uah else "$"
    usd_rate = 1 if is_uah else float(currency_convert())
    
    total_sum = 0
    cart_items = []
    
    for flower_name, item in carts[chat_id].items():
        quantity = item.get("quantity", item) if isinstance(item, dict) else item
        price = float(item.get("price", get_flower_price(flower_name))) if isinstance(item, dict) else get_flower_price(flower_name)
        
        if not is_uah:
            price = round(price / usd_rate, 2)
        
        item_sum = round(price * quantity, 2)
        total_sum += item_sum
        cart_items.append(f"{flower_name} x{quantity} = {item_sum} {currency_symbol}")
        
        if not isinstance(item, dict):
            carts[chat_id][flower_name] = {"quantity": quantity, "price": price}
    
    await message.answer(
        f"🛒 Ваш кошик:\n{'\n'.join(cart_items)}\n\nЗагальна сума: {round(total_sum, 2)} {currency_symbol}",
        reply_markup=get_cart_kb()
    )

@router.message(F.text == "🗑️ Очистити кошик")
async def clear_cart(message: Message, state: FSMContext):
    chat_id = message.chat.id
    
    if chat_id in carts:
        carts[chat_id] = {}
    
    await message.answer("🗑️ Ваш кошик очищено!", reply_markup=get_menu_kb())
    await state.set_state(OrderStates.choosing_category)

@router.message(F.text == "💵 Оформити замовлення")
async def initiate_checkout(message: Message, state: FSMContext):
    chat_id = message.chat.id
    
    if chat_id not in carts or not carts[chat_id]:
        await message.answer("🛒 Ваш кошик порожній!")
        return
    
    await state.set_state(OrderStates.choosing_delivery)
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    await message.answer(
        "Виберіть спосіб отримання:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚚 Оплатити зараз")],
                [KeyboardButton(text="🏪 Самовивіз")],
                [KeyboardButton(text="🔙 Назад до кошику")]
            ],
            resize_keyboard=True
        )
    )
