from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from app.keyboards import get_currency_kb, get_categories_kb, get_colors_kb, get_flower_inline_kb, get_menu_kb
from data_handler import get_category, get_colors, get_flowers, get_flower_by_id, currency_convert
from app.handlers.common import OrderStates, carts
from app.handlers.cart import view_cart

router = Router()

@router.message(CommandStart())
@router.message(Command("help"))
async def cmd_start_or_help(message: Message, state: FSMContext):
    await state.set_state(OrderStates.choosing_currency)
    
    if message.text == "/start":
        text = f"Вітаю {message.from_user.first_name}, я допоможу тобі з вибором букету 💐.\nВиберіть валюту:"
    else:
        text = "Виберіть валюту:"
    
    await message.answer(text, reply_markup=get_currency_kb())

@router.message(OrderStates.choosing_currency, F.text.in_(["USD🇺🇸", "UAH🇺🇦"]))
async def process_currency_selection(message: Message, state: FSMContext):
    await state.update_data(currency=message.text)
    currency_code = "UAH" if message.text == "UAH🇺🇦" else "USD"
    await state.update_data(currency_code=currency_code)
    await message.answer(f"Ви обрали {message.text}")
    await send_categories_menu(message, state)

async def send_categories_menu(message: Message, state: FSMContext):
    await state.set_state(OrderStates.choosing_category)
    await message.answer(
        "Ви знаходитесь в меню, виберіть бажану категорію", 
        reply_markup=get_categories_kb()
    )

@router.message(OrderStates.choosing_category, F.text.in_(get_category()))
async def process_category_selection(message: Message, state: FSMContext):
    category = message.text
    await state.update_data(category=category)
    await state.set_state(OrderStates.choosing_color)
    
    await message.answer(
        f"Ви обрали категорію {category}. Тепер виберіть бажаний колір:", 
        reply_markup=get_colors_kb(category)
    )

@router.message(OrderStates.choosing_color)
async def process_color_selection(message: Message, state: FSMContext):
    color = message.text
    
    if color == "🔙 Назад до меню":
        await send_categories_menu(message, state)
        return
    
    if color == "🛒 Переглянути кошик":
        await view_cart(message, state)
        return
    
    data = await state.get_data()
    category = data.get("category")
    
    colors = get_colors(category)
    if color not in colors:
        await message.answer("Будь ласка, виберіть колір з клавіатури.")
        return
    
    await state.update_data(color=color)
    await state.set_state(OrderStates.viewing_flowers)
    
    flowers = get_flowers(category, color)
    
    await message.answer(
        f"Знайдено {len(flowers)} товарів:", 
        reply_markup=get_menu_kb()
    )
    
    currency = data.get("currency", "UAH🇺🇦")
    usd_rate = float(currency_convert()) if currency == "USD🇺🇸" else 1
    currency_symbol = "$" if currency == "USD🇺🇸" else "₴"
    
    for flower in flowers:
        flower_id = flower[0]
        price = round(float(flower[5]) / usd_rate, 2)
        
        await message.answer_photo(
            flower[6],
            f"Назва: {flower[4]}\nКатегорія: {flower[1]}\nКолір: {flower[2]}\nЦіна: {price} {currency_symbol}",
            reply_markup=get_flower_inline_kb(flower_id)
        )

@router.message(F.text == "🔙 Назад до меню")
async def back_to_menu(message: Message, state: FSMContext):
    await send_categories_menu(message, state)

@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery, state: FSMContext):
    flower_id = callback.data.split("_")[1]
    chat_id = callback.message.chat.id
    
    flower = get_flower_by_id(flower_id)
    if flower:
        flower_name = flower[4]
        flower_price = float(flower[5])
        
        if chat_id not in carts:
            carts[chat_id] = {}
        
        if flower_name in carts[chat_id]:
            carts[chat_id][flower_name]["quantity"] += 1
        else:
            carts[chat_id][flower_name] = {"quantity": 1, "price": flower_price}
        
        await callback.answer(f"✅ {flower_name} додано до кошика!")
    else:
        await callback.answer("❌ Помилка! Товар не знайдено.")
