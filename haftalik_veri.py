#!/usr/bin/env python3
"""Haftalık karar turu için piyasa verilerini topla."""
import yfinance as yf
import json
from datetime import datetime

# Portföy + izleme listesi
symbols = ['MU', 'AMD', 'SNDK', 'ANET', 'AVGO', 'NVDA', 'TSM', 'MRVL', 'VRT', 'PLTR', 'MSFT', 'GOOGL']

results = {}

for sym in symbols:
    try:
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="6mo")

        if hist.empty:
            print(f"UYARI: {sym} için veri alınamadı")
            continue

        # Son fiyat
        last_price = hist['Close'].iloc[-1]

        # SMA hesapları
        sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else None

        # RSI hesabı
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))

        # Getiri hesapları
        ret_1m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-21]) - 1) * 100 if len(hist) >= 21 else None
        ret_3m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-63]) - 1) * 100 if len(hist) >= 63 else None

        # Bilanço tarihi
        try:
            calendar = ticker.calendar
            earnings_date = calendar.get('Earnings Date', [None])[0] if calendar else None
        except:
            earnings_date = None

        # Haberler (son 5)
        try:
            news = ticker.news[:5] if ticker.news else []
            news_titles = [n.get('title', '') for n in news]
        except:
            news_titles = []

        results[sym] = {
            'last_price': round(last_price, 2),
            'sma50': round(sma50, 2) if sma50 else None,
            'sma200': round(sma200, 2) if sma200 else None,
            'rsi': round(rsi, 1),
            'return_1m_pct': round(ret_1m, 1) if ret_1m else None,
            'return_3m_pct': round(ret_3m, 1) if ret_3m else None,
            'earnings_date': str(earnings_date) if earnings_date else None,
            'news_titles': news_titles
        }

        print(f"✓ {sym}: ${last_price:.2f}")

    except Exception as e:
        print(f"HATA {sym}: {e}")

# Sonuçları kaydet
with open('veri_haftalik.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n{len(results)}/{len(symbols)} sembol için veri toplandı")
print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
