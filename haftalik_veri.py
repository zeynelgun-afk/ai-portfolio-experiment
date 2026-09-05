#!/usr/bin/env python3
"""Haftalık karar turu için piyasa verilerini topla."""
import yfinance as yf
import json
import math
from datetime import datetime, timedelta

# Portföy + izleme listesi
# PLTR ve VRT tur #7'de listeden çıkarıldı; çekim listesi izleme listesiyle aynı kalmalı
symbols = ['MU', 'AMD', 'SNDK', 'ANET', 'AVGO', 'NVDA', 'TSM', 'MRVL', 'MSFT', 'GOOGL']

GUNLER = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']

results = {}
eksik_veri = []


def gun_adi_of(tarih):
    """Tarihin gün adı. Gün adı hiçbir yerde elde hesaplanmasın diye burada üretiliyor."""
    if tarih is None:
        return None
    try:
        return GUNLER[tarih.weekday()]
    except AttributeError:
        return None


def haber_basligi(item):
    """yfinance haber şeması sürümlere göre değişiyor: düz 'title' ya da 'content.title'."""
    return item.get('title') or item.get('content', {}).get('title', '')


for sym in symbols:
    try:
        ticker = yf.Ticker(sym)
        # 200 günlük SMA için en az 200 işlem günü gerekir — 6mo (~126 gün) yetmez.
        hist = ticker.history(period="2y")

        if hist.empty:
            print(f"UYARI: {sym} için veri alınamadı")
            eksik_veri.append(f"{sym}: fiyat verisi yok")
            continue

        # yfinance son satırı (kapanmamış/boş gün) tümüyle NaN döndürebiliyor. Bu satır
        # .iloc[-1] üzerinden fiyat, SMA ve getirilerin HEPSİNİ NaN yapıyordu; RSI ise
        # ewm NaN'ı atladığı için sağlam görünüyordu — yani hata sessizdi. (bkz. tur #6)
        hist = hist[hist['Close'].notna()]
        if hist.empty:
            print(f"UYARI: {sym} için geçerli kapanış yok")
            eksik_veri.append(f"{sym}: fiyat verisi yok (tüm kapanışlar NaN)")
            continue

        # Fiyatın ait olduğu gerçek gün — rapordaki tarih etiketi buna dayanmalı.
        # Gün adı da buradan veriliyor: tur #7'de "4 Eylül Çarşamba" (Cuma) ve
        # "2 Eylül Pazartesi" (Çarşamba) yazıldı — gün adı elde hesaplanınca yanılıyor.
        fiyat_gunu = hist.index[-1].date()
        fiyat_tarihi = fiyat_gunu.isoformat()
        fiyat_gun_adi = GUNLER[fiyat_gunu.weekday()]

        # Son fiyat
        last_price = hist['Close'].iloc[-1]

        # SMA hesapları
        sma50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
        sma200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else None

        # RSI hesabı (Wilder)
        delta = hist['Close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] else float('inf')
        rsi = 100 - (100 / (1 + rs))

        # Getiri hesapları
        ret_1m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-21]) - 1) * 100 if len(hist) >= 21 else None
        ret_3m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-63]) - 1) * 100 if len(hist) >= 63 else None
        # Haftalık hareket — talimattaki "sebebini araştır" eşiği (±%10) bu alana bakar.
        ret_1w = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-6]) - 1) * 100 if len(hist) >= 6 else None

        # Bilanço tarihi
        try:
            calendar = ticker.calendar
            earnings_date = calendar.get('Earnings Date', [None])[0] if calendar else None
        except Exception:
            earnings_date = None
        if earnings_date is None:
            eksik_veri.append(f"{sym}: bilanço tarihi alınamadı")

        # Haberler (son 5)
        try:
            news_titles = [t for t in (haber_basligi(n) for n in (ticker.news or [])[:5]) if t]
        except Exception:
            news_titles = []
        if not news_titles:
            eksik_veri.append(f"{sym}: haber başlığı alınamadı")

        def sayi(deger, alan, basamak=2):
            """NaN/Inf asla JSON'a yazılmaz: None döner ve eksik_veri'ye kaydedilir."""
            if deger is None or not math.isfinite(float(deger)):
                eksik_veri.append(f"{sym}: {alan} hesaplanamadı")
                return None
            return round(float(deger), basamak)

        results[sym] = {
            'last_price': sayi(last_price, 'fiyat'),
            'fiyat_tarihi': fiyat_tarihi,
            'fiyat_gun_adi': fiyat_gun_adi,
            'sma50': sayi(sma50, 'SMA50'),
            'sma200': sayi(sma200, 'SMA200'),
            'rsi': sayi(rsi, 'RSI', 1),
            'return_1w_pct': sayi(ret_1w, '1h getiri', 1),
            'return_1m_pct': sayi(ret_1m, '1a getiri', 1),
            'return_3m_pct': sayi(ret_3m, '3a getiri', 1),
            'earnings_date': str(earnings_date) if earnings_date else None,
            'earnings_gun_adi': gun_adi_of(earnings_date),
            'news_titles': news_titles
        }

        if results[sym]['last_price'] is None:
            print(f"UYARI {sym}: fiyat hesaplanamadı")
        else:
            print(f"✓ {sym}: ${last_price:.2f} ({fiyat_tarihi})")

    except Exception as e:
        print(f"HATA {sym}: {e}")
        eksik_veri.append(f"{sym}: {e}")

# Tarih bilgisi — karar turu gün adını kendi hesaplamasın diye buradan veriliyor.
bugun = datetime.now()
sonraki_cuma = bugun + timedelta(days=(4 - bugun.weekday()) % 7 or 7)
sonraki_tur = bugun + timedelta(days=(5 - bugun.weekday()) % 7 or 7)

results['_meta'] = {
    'tarih': bugun.strftime('%Y-%m-%d'),
    'gun_adi': GUNLER[bugun.weekday()],
    'sonraki_cuma': f"{sonraki_cuma.strftime('%Y-%m-%d')} (Cuma — haftalık kapanış)",
    'sonraki_tur': f"{sonraki_tur.strftime('%Y-%m-%d')} (Cumartesi — bir sonraki karar turu)",
    'sembol_sayisi': f"{len(results)}/{len(symbols)}",
    'eksik_veri': eksik_veri,
}

# Sonuçları kaydet
with open('veri_haftalik.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False, allow_nan=False)

print(f"\n{len(results) - 1}/{len(symbols)} sembol için veri toplandı")
if eksik_veri:
    print(f"EKSİK VERİ ({len(eksik_veri)} kayıt):")
    for e in eksik_veri:
        print(f"  - {e}")
print(f"Tarih: {bugun.strftime('%Y-%m-%d %H:%M:%S')} ({GUNLER[bugun.weekday()]})")
