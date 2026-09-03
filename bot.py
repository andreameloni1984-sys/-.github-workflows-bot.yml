import os
import requests

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

if not API_KEY:
    raise RuntimeError("TWELVE_DATA_API_KEY non configurata")

url = "https://api.twelvedata.com/price"

params = {
    "symbol": "XAU/USD",
    "apikey": API_KEY
}

response = requests.get(url, params=params, timeout=15)

print("Status:", response.status_code)
print("Risposta:", response.text)

response.raise_for_status()

data = response.json()

if "price" not in data:
    raise RuntimeError(f"Prezzo non ricevuto: {data}")

print("ORO XAU/USD:", data["price"])