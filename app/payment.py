import requests
import time
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

def create_wayforpay_invoice(order_data, user_data):

    print("Creating WayForPay invoice with data:", order_data)
    
    merchant_account = os.getenv("WAYFORPAY_MERCHANT_ACCOUNT", "test_merch_n1")
    merchant_secret_key = os.getenv("WAYFORPAY_SECRET_KEY", "flk3409refn54t54t*FNJRET")
    merchant_domain_name = os.getenv("WAYFORPAY_DOMAIN", "www.yourdomain.com")
    
    order_reference = f"order_{int(time.time())}_{user_data['chat_id']}"
    order_date = int(time.time())
    
    product_names = []
    product_counts = []
    product_prices = []
    
    total_amount = 0
    
    for flower_name, item in order_data.items():
        product_names.append(flower_name)
        quantity = item["quantity"]
        product_counts.append(quantity)
        price = float(item["price"])
        product_prices.append(price)
        total_amount += price * quantity
    
    # Форматування даних
    total_amount_formatted = "{:.2f}".format(total_amount)
    product_prices_formatted = ["{:.2f}".format(price) for price in product_prices]
    
    # Дані користувача для WayForPay
    signature_elements = [
        merchant_account,
        merchant_domain_name,
        order_reference,
        str(order_date),
        total_amount_formatted,
        user_data["currency_code"],
        *product_names,
        *[str(count) for count in product_counts],
        *product_prices_formatted
    ]

    signature_string = ";".join(signature_elements)
    print("Signature string:", signature_string)
    
    # Розрахунок сигнатури
    merchant_signature = hmac.new(
        merchant_secret_key.encode("utf-8"),
        signature_string.encode("utf-8"),
        hashlib.md5
    ).hexdigest()
    
    print("Generated signature:", merchant_signature)

    payload = {
        "transactionType": "CREATE_INVOICE",
        "merchantAccount": merchant_account,
        "merchantDomainName": merchant_domain_name,
        "merchantSignature": merchant_signature,
        "apiVersion": 1,
        "orderReference": order_reference,
        "orderDate": order_date,
        "amount": total_amount_formatted,
        "currency": user_data["currency_code"],
        "productName": product_names,
        "productPrice": product_prices_formatted,
        "productCount": product_counts,
        "clientFirstName": user_data.get("first_name", ""),
        "clientLastName": user_data.get("last_name", "") if user_data.get("last_name") else "Unknown",
        "clientEmail": user_data.get("email", ""),
        "clientPhone": user_data["phone"],
        "language": "UA",
        "serviceUrl": os.getenv("WAYFORPAY_CALLBACK_URL", "https://yourdomain.com/wfpcallback")
    }

    print("WayForPay payload:", payload)

    response = requests.post("https://api.wayforpay.com/api", json=payload)
    
    print("WayForPay response:", response.text)
    
    return response.json()