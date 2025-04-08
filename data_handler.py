import sqlite3
import requests

def currency_convert():
    response = requests.get('https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5') 
    data = response.json()
    usd_price = next(item["sale"] for item in data if item["ccy"] == "USD")
    return usd_price

def get_category():
    conn = sqlite3.connect('flowers.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM flowers")
    categories = cursor.fetchall()
    conn.close()
    return list(set(category[0] for category in categories))

def get_colors(category):
    conn = sqlite3.connect('flowers.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT color FROM flowers WHERE category = ?", (category,))
    colors = [row[0] for row in cursor.fetchall()]
    conn.close()
    return colors

def get_flowers(category, color):
    conn = sqlite3.connect('flowers.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flowers WHERE category = ? AND color = ?", (category, color))
    flowers = cursor.fetchall()
    conn.close()
    return flowers

def get_flower_by_id(flower_id):
    """Fetch a flower by its ID from the database."""
    conn = sqlite3.connect('flowers.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flowers WHERE id = ?", (flower_id,))
    flower = cursor.fetchone()
    conn.close()
    return flower

def get_flower_price(flower_name):
    conn = sqlite3.connect('flowers.db')
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM flowers WHERE name = ?", (flower_name,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return float(result[0]) 
    return 0
