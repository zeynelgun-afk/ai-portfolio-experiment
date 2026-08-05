#!/usr/bin/env python3
"""Haftalık tur için piyasa verileri toplama."""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json

# Portföydeki pozisyonlar + izleme listesi
SEMBOLLER = ['MU', 'AMD', 'SNDK', 'ANET', 'AVGO',  # Mevcut pozisyonlar
             'NVDA', 'TSM', 'MRVL', 'VRT', 'PLTR', 'MSFT', 'GOOGL']  # İzleme

def hesapla_rsi(fiyatlar, period=14):
    """RSI(14) hesapla."""
    delta = fiyatlar.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if len(rsi) > 0 else None

def veri_topla():
    """Her sembol için teknik veriler + haberler topla."""
    sonuclar = {}

    for sembol in SEMBOLLER:
        try:
            ticker = yf.Ticker(sembol)

            # 1 yıllık fiyat geçmişi (SMA hesabı için)
            hist = ticker.history(period='1y')
            if hist.empty:
                print(f"⚠️  {sembol}: Veri yok")
                continue

            son_fiyat = hist['Close'].iloc[-1]
            sma_50 = hist['Close'].rolling(50).mean().iloc[-1]
            sma_200 = hist['Close'].rolling(200).mean().iloc[-1]
            rsi = hesapla_rsi(hist['Close'])

            # 1 ay ve 3 ay getiri
            bir_ay_once = hist['Close'].iloc[-22] if len(hist) >= 22 else hist['Close'].iloc[0]
            uc_ay_once = hist['Close'].iloc[-66] if len(hist) >= 66 else hist['Close'].iloc[0]
            getiri_1ay = ((son_fiyat / bir_ay_once) - 1) * 100
            getiri_3ay = ((son_fiyat / uc_ay_once) - 1) * 100

            # Bilanço tarihi
            try:
                cal = ticker.calendar
                bilanco = cal.get('Earnings Date', [None])[0] if cal else None
                bilanco_str = bilanco.strftime('%Y-%m-%d') if bilanco else None
            except:
                bilanco_str = None

            # Son haberler (başlıklar)
            try:
                haberler = ticker.news[:3] if hasattr(ticker, 'news') else []
                haber_basliklar = [h.get('title', '') for h in haberler]
            except:
                haber_basliklar = []

            sonuclar[sembol] = {
                'son_fiyat': round(son_fiyat, 2),
                'sma_50': round(sma_50, 2) if pd.notna(sma_50) else None,
                'sma_200': round(sma_200, 2) if pd.notna(sma_200) else None,
                'rsi_14': round(rsi, 1) if pd.notna(rsi) else None,
                'getiri_1ay_pct': round(getiri_1ay, 1),
                'getiri_3ay_pct': round(getiri_3ay, 1),
                'bilanco_tarihi': bilanco_str,
                'haberler': haber_basliklar
            }

            rsi_str = f"{rsi:.0f}" if pd.notna(rsi) else "?"
            print(f"✓ {sembol}: ${son_fiyat:.2f} (RSI {rsi_str})")

        except Exception as e:
            print(f"❌ {sembol} hatası: {e}")
            sonuclar[sembol] = {'hata': str(e)}

    return sonuclar

if __name__ == '__main__':
    print(f"\n=== Piyasa Verileri ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===\n")
    veriler = veri_topla()

    # JSON'a kaydet
    with open('piyasa_verileri.json', 'w', encoding='utf-8') as f:
        json.dump(veriler, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Veriler piyasa_verileri.json'a kaydedildi\n")
