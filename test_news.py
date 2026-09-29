import os
import requests
from dotenv import load_dotenv
load_dotenv(".env")
api_key = os.environ.get("FMP_API_KEY")
r = requests.get(f"https://financialmodelingprep.com/stable/news/stock?symbols=AAPL&limit=3&apikey={api_key}")
print(r.json())
