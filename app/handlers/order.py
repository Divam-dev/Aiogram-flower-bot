from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.keyboards import get_menu_kb
from app.handlers.common import OrderStates, carts
from app.handlers.cart import view_cart
from app.payment import create_wayforpay_invoice

router = Router()

@router.message(OrderStates.choosing_delivery, F.text == "🏪 Самовивіз")
async def process_self_pickup(message: Message, state: FSMContext):
    await state.update_data(delivery_method="self_pickup")
    
    await state.set_state(OrderStates.entering_phone)
    await message.answer(
        "Ви обрали самовивіз. Для оформлення замовлення, будь ласка, введіть ваш номер телефону у форматі +380XXXXXXXXX:",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(OrderStates.choosing_delivery, F.text == "🚚 Оплатити зараз")
async def process_immediate_payment(message: Message, state: FSMContext):
    await state.update_data(delivery_method="immediate_payment")
    
    await state.set_state(OrderStates.entering_phone)
    await message.answer(
        "Ви обрали оплату зараз. Для оформлення замовлення, будь ласка, введіть ваш номер телефону у форматі +380XXXXXXXXX:",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(OrderStates.choosing_delivery, F.text == "🔙 Назад до кошику")
async def back_to_cart(message: Message, state: FSMContext):
    await view_cart(message, state)

@router.message(OrderStates.entering_phone)
async def process_phone_number(message: Message, state: FSMContext):
    chat_id = message.chat.id
    phone_number = message.text
    
    # Базова перевірка телефону
    if not (phone_number.startswith("+380") and len(phone_number) == 13 and phone_number[1:].isdigit()):
        await message.answer("Будь ласка, введіть коректний номер телефону у форматі +380XXXXXXXXX")
        return
    
    await state.update_data(phone=phone_number)
    
    await state.set_state(OrderStates.entering_email)
    await message.answer("Введіть ваш email для отримання квитанції:")

@router.message(OrderStates.entering_email)
async def process_email(message: Message, state: FSMContext):
    email = message.text
    chat_id = message.chat.id
    
    # Базова перевірка email
    if "@" not in email or "." not in email:
        await message.answer("Будь ласка, введіть коректний email")
        return
    
    await state.update_data(email=email)
    data = await state.get_data()
    
    delivery_method = data.get("delivery_method")
    
    # Створюємо дані користувача для платіжної системи
    user_data = {
        "chat_id": chat_id,
        "phone": data.get("phone"),
        "email": email,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "currency_code": data.get("currency_code", "UAH")
    }
    
    if not carts.get(chat_id):
        await message.answer("Помилка: кошик порожній")
        return
    
    if delivery_method == "self_pickup":
        await message.answer(
            "✅ Ваше замовлення на самовивіз успішно оформлено!\n\n"
            f"Наш менеджер зв'яжеться з вами за номером {data.get('phone')} "
            "для підтвердження деталей замовлення та адреси самовивозу.\n\n"
            "Дякуємо за замовлення!",
            reply_markup=get_menu_kb()
        )
        
        if chat_id in carts:
            carts[chat_id] = {}
        
        await state.set_state(OrderStates.choosing_category)
        return
    
    try:
        payment_data = create_wayforpay_invoice(carts[chat_id], user_data)
        
        if payment_data.get("reason") == "Ok" and payment_data.get("invoiceUrl"):
            payment_url = payment_data.get("invoiceUrl")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатити замовлення", url=payment_url)]
            ])
            
            await message.answer(
                "✅ Ваше замовлення сформовано!\n\n"
                "Для завершення натисніть кнопку нижче, щоб перейти до оплати.",
                reply_markup=keyboard
            )
            
            await state.update_data(payment_url=payment_url)
            await state.update_data(order_reference=payment_data.get("orderReference"))
            await state.set_state(OrderStates.confirming_payment)
            
        else:
            await message.answer(
                f"❌ Помилка при створенні платежу: {payment_data.get('reason', 'Невідома помилка')}.\n"
                "Спробуйте ще раз або зв'яжіться з нами для допомоги.",
                reply_markup=get_menu_kb()
            )
            await state.set_state(OrderStates.choosing_category)
            
    except Exception as e:
        await message.answer(
            f"❌ Виникла помилка при обробці платежу: {str(e)}.\n"
            "Будь ласка, спробуйте ще раз пізніше або зв'яжіться з нами для допомоги.",
            reply_markup=get_menu_kb()
        )
        await state.set_state(OrderStates.choosing_category)

# Обробник для підтвердження оплати
@router.message(OrderStates.confirming_payment)
async def check_payment_status(message: Message, state: FSMContext):
    
    if message.text.lower() in ["назад", "скасувати", "відмінити", "cancel"]:
        await message.answer("Ви скасували оплату і повертаєтесь до меню.", reply_markup=get_menu_kb())
        await state.set_state(OrderStates.choosing_category)
        return
    
    data = await state.get_data()
    await message.answer(
        f"Перевірка статусу оплати. Якщо ви вже оплатили замовлення, "
        f"наш менеджер зв'яжеться з вами за номером {data.get('phone')}.\n\n"
        f"Якщо ви ще не оплатили, ви можете перейти за посиланням: {data.get('payment_url')}",
        reply_markup=get_menu_kb()
    )
    
    chat_id = message.chat.id
    if chat_id in carts:
        carts[chat_id] = {}
    
    await state.set_state(OrderStates.choosing_category)
