# AI Portföy Deneyi 🤖📈

**Hipotez:** Duygusuz, kurallara sadık bir AI karar vericisi; yazılı tezler ve katı risk
kurallarıyla agresif bir portföyü, insan davranışsal hatalarından arındırılmış şekilde
yönetebilir mi?

- **Başlangıç:** 5 Ağustos 2026 · 100.000 $ (sanal — kağıt üzerinde, gerçek para yok)
- **Evren:** ABD büyük teknoloji + yarı iletken/AI altyapısı
- **Kıyas:** SPY ve SMH (aynı gün alınmış 100.000 $ varsayımı)
- **Süre:** 12 ay

## Nasıl çalışıyor?

Her Cumartesi 06:00 UTC'de (Cuma kapanışı sonrası) GitHub Actions şu turu koşar:

| Adım | Kim | Ne yapar |
|---|---|---|
| 1. Mekanik | `guncelle.py` | Fiyat çekme, değerleme, SPY/SMH kıyası, stop kuralı uygulama → [RAPOR.md](RAPOR.md) |
| 2. Karar | Claude (claude-code-action) | [HAFTALIK_TALIMAT.md](HAFTALIK_TALIMAT.md) uyarınca veri analizi, yazılı tez, al/sat → [KARAR_GUNLUGU.md](KARAR_GUNLUGU.md) |
| 3. Bildirim | Telegram + Issue | Haftalık özet Telegram'a; stop ihlali olduysa 🛑 Issue |
| Tüzük | [DENEY_KURALLARI.md](DENEY_KURALLARI.md) | Kimsenin (AI dahil) çiğneyemediği kurallar |

Stop ihlalinde otomasyon pozisyonu kural gereği kapatır ve işlemi günlüğe yazar.

### Gerekli secrets (Settings → Secrets → Actions)

- `ANTHROPIC_API_KEY` — Claude karar turu için (yoksa adım atlanır, deney mekanik modda sürer)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — haftalık Telegram raporu (yoksa adım atlanır)

## Dosyalar

- `portfoy.json` — güncel pozisyonlar, nakit, işlem geçmişi (tek doğruluk kaynağı)
- `KARAR_GUNLUGU.md` — her kararın tarihli, gerekçeli kaydı
- `RAPOR.md` — son otomatik durum raporu
- `gecmis.csv` — haftalık değer serisi (portföy vs SPY vs SMH)
- `guncelle.py` — otomasyon scripti (yfinance, API anahtarı gerekmez)

> ⚠️ Bu bir deneydir, yatırım tavsiyesi değildir.
