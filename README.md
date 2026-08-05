# AI Portföy Deneyi 🤖📈

**Hipotez:** Duygusuz, kurallara sadık bir AI karar vericisi; yazılı tezler ve katı risk
kurallarıyla agresif bir portföyü, insan davranışsal hatalarından arındırılmış şekilde
yönetebilir mi?

- **Başlangıç:** 5 Ağustos 2026 · 100.000 $ (sanal — kağıt üzerinde, gerçek para yok)
- **Evren:** ABD büyük teknoloji + yarı iletken/AI altyapısı
- **Kıyas:** SPY ve SMH (aynı gün alınmış 100.000 $ varsayımı)
- **Süre:** 12 ay

## Nasıl çalışıyor?

| Katman | Kim | Ne yapar |
|---|---|---|
| **Karar** | Claude (oturumda) | Veri analizi, yazılı tez, al/sat kararları → [KARAR_GUNLUGU.md](KARAR_GUNLUGU.md) |
| **Mekanik** | GitHub Actions (haftalık, Cmt 06:00 UTC) | Fiyat çekme, değerleme, SPY/SMH kıyası, stop kuralı uygulama → [RAPOR.md](RAPOR.md) |
| **Kurallar** | [DENEY_KURALLARI.md](DENEY_KURALLARI.md) | Kimsenin (AI dahil) çiğneyemediği tüzük |

Stop ihlalinde otomasyon pozisyonu kural gereği kapatır, işlemi günlüğe yazar ve
GitHub Issue açarak haber verir. Takdir gerektiren hiçbir karar otomasyonda değildir.

## Dosyalar

- `portfoy.json` — güncel pozisyonlar, nakit, işlem geçmişi (tek doğruluk kaynağı)
- `KARAR_GUNLUGU.md` — her kararın tarihli, gerekçeli kaydı
- `RAPOR.md` — son otomatik durum raporu
- `gecmis.csv` — haftalık değer serisi (portföy vs SPY vs SMH)
- `guncelle.py` — otomasyon scripti (yfinance, API anahtarı gerekmez)

> ⚠️ Bu bir deneydir, yatırım tavsiyesi değildir.
