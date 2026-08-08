# AI Portföy Deneyi 🤖📈

**Hipotez:** Kararın tamamı yapay zekâya bırakılmış — ama her hamlesini yazmak ve
sonucuna sahip çıkmak zorunda olan — bir portföy, 12 ayda piyasayı yenebilir mi?
Ölçülen şey kurallara uyum değil, serbest kararın hesap verebilirlikle birleşimi.

- **Başlangıç:** 5 Ağustos 2026 · 100.000 $ (sanal — kağıt üzerinde, gerçek para yok)
- **Evren:** ABD büyük teknoloji + yarı iletken/AI altyapısı
- **Kıyas:** SPY ve SMH (aynı gün alınmış 100.000 $ varsayımı)
- **Süre:** 12 ay

## Nasıl çalışıyor?

Her Cumartesi 06:00 UTC'de (Cuma kapanışı sonrası) GitHub Actions şu turu koşar:

| Adım | Kim | Ne yapar |
|---|---|---|
| 1. Ölçüm | `guncelle.py` | Fiyat çekme, değerleme, SPY/SMH kıyası, çıkış seviyesi uyarısı → [RAPOR.md](RAPOR.md) · **karar vermez** |
| 2. Karar | Claude (claude-code-action) | [HAFTALIK_TALIMAT.md](HAFTALIK_TALIMAT.md) uyarınca veri analizi, yazılı tez, al/sat → [KARAR_GUNLUGU.md](KARAR_GUNLUGU.md) |
| 3. Bildirim | Telegram + Issue | Haftalık özet Telegram'a; çıkış seviyesi altına düşen pozisyon varsa ⚠️ Issue |
| Tüzük | [DENEY_KURALLARI.md](DENEY_KURALLARI.md) | Karar kısıtı değil; kayıt dürüstlüğü ve ölçüm ilkeleri |

Otomasyon pozisyon kapatmaz. Çıkış seviyesinin altına düşen pozisyonu **işaretler**;
kapatma, seviyeyi güncelleme ya da gerekçeyle taşıma kararı AI'a aittir.

### Gerekli secrets (Settings → Secrets → Actions)

- `OPENROUTER_API_KEY` — Claude karar turu için (OpenRouter üzerinden) (yoksa adım atlanır, deney mekanik modda sürer)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — haftalık Telegram raporu (yoksa adım atlanır)

## Dosyalar

- `portfoy.json` — güncel pozisyonlar, nakit, işlem geçmişi (tek doğruluk kaynağı)
- `KARAR_GUNLUGU.md` — her kararın tarihli, gerekçeli kaydı
- `RAPOR.md` — son otomatik durum raporu
- `gecmis.csv` — haftalık değer serisi (portföy vs SPY vs SMH)
- `guncelle.py` — otomasyon scripti (yfinance, API anahtarı gerekmez)

> ⚠️ Bu bir deneydir, yatırım tavsiyesi değildir.
