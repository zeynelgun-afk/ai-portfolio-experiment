# AI Portföy Deneyi 🤖📈

**Hipotez:** Kararın tamamı yapay zekâya bırakılmış — ama her hamlesini yazmak ve
sonucuna sahip çıkmak zorunda olan — bir portföy, 12 ayda piyasayı yenebilir mi?
Ölçülen şey kurallara uyum değil, serbest kararın hesap verebilirlikle birleşimi.

- **Başlangıç:** 5 Ağustos 2026 · 100.000 $ (sanal — kağıt üzerinde, gerçek para yok)
- **Evren:** ABD büyük teknoloji + yarı iletken/AI altyapısı
- **Kıyas:** SPY ve SMH (aynı gün alınmış 100.000 $ varsayımı)
- **Süre:** 12 ay

## Nasıl çalışıyor?

İki tür karar turu var. **Haftalık tur** tezleri kurar, **seans içi tur** onları
hafta içi canlı tutar.

**Haftalık tur** — her Cumartesi 06:00 UTC (Cuma kapanışı sonrası):

| Adım | Kim | Ne yapar |
|---|---|---|
| 1. Ölçüm | `guncelle.py` | Fiyat çekme, değerleme, SPY/SMH kıyası, çıkış seviyesi uyarısı → [RAPOR.md](RAPOR.md) · **karar vermez** |
| 2. Karar | Claude (claude-code-action) | [HAFTALIK_TALIMAT.md](HAFTALIK_TALIMAT.md) uyarınca veri analizi, yazılı tez, al/sat → [KARAR_GUNLUGU.md](KARAR_GUNLUGU.md) |
| 3. Tez şeması | Claude | Her tezi ölçülebilir geçerlilik koşullarına bağlar → [tezler.json](tezler.json) |
| 4. Bildirim | Telegram + Issue | Haftalık özet Telegram'a; çıkış seviyesi altına düşen pozisyon varsa ⚠️ Issue |
| Tüzük | [DENEY_KURALLARI.md](DENEY_KURALLARI.md) | Karar kısıtı değil; kayıt dürüstlüğü ve ölçüm ilkeleri |

**Seans içi tur** — Pzt–Cum 13:30–20:00 UTC, 30 dakikada bir. Aşağıdaki
"Olay Güdümlü Yeniden Değerlendirme" bölümü.

Haftalık turdaki `guncelle.py` pozisyon kapatmaz. Çıkış seviyesinin altına düşen
pozisyonu **işaretler**; kapatma, seviyeyi güncelleme ya da gerekçeyle taşıma kararı
AI'a aittir.

### Gerekli secrets (Settings → Secrets → Actions)

- `OPENROUTER_API_KEY` — Claude karar turu için (OpenRouter üzerinden) (yoksa adım atlanır, deney mekanik modda sürer)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — haftalık Telegram raporu (yoksa adım atlanır)
- `TELEGRAM_CHAT_ID_DM` — seans içi **tez seviyesi** bildirimi (grup değil, kişisel DM).
  Yoksa yalnızca o adım atlanır; dedektör ölçmeye devam eder.

### Ayarlanabilir değişkenler (Settings → Variables → Actions)

| Değişken | Varsayılan | Ne yapar |
|---|---|---|
| `OPENROUTER_MODEL_HIZLI` | `anthropic/claude-haiku-4.5` | Tek iddiayı yeniden yazan küçük model |
| `OPENROUTER_MODEL_DERIN` | `anthropic/claude-sonnet-4.5` | Tüm tezi yeniden değerlendiren derin model |
| `MAX_LLM_CAGRI_HAFTA` | `60` | Haftalık LLM çağrı bütçesi; aşılırsa yalnızca `tez` seviyesi çağrılar yapılır |

## Dosyalar

- `portfoy.json` — güncel pozisyonlar, nakit, işlem geçmişi (tek doğruluk kaynağı)
- `KARAR_GUNLUGU.md` — her kararın tarihli, gerekçeli kaydı (`#N` haftalık, `S#N` seans içi)
- `tezler.json` — her pozisyonun tezi, iddiaları ve **ölçülebilir geçerlilik koşulları**
- `RAPOR.md` — son otomatik durum raporu
- `gecmis.csv` — haftalık değer serisi (portföy vs SPY vs SMH)
- `guncelle.py` — haftalık ölçüm scripti (yfinance, API anahtarı gerekmez)
- `dedektor.py` — seans içi değişim dedektörü (deterministik, LLM yok)
- `yeniden_degerlendir.py` — tetiklenen iddiayı/tezi yeniden yazan LLM katmanı
- `islem_uygula.py` — seans içi kararı deterministik uygulayan katman
- `durum/` — dedektörün hafızası (histerezis, cooldown, işlem kilidi, bekleyen notlar)
- `tests/` — dedektör ve işlem katmanı testleri (`python -m unittest discover -s tests -t .`)

## Olay Güdümlü Yeniden Değerlendirme

**Çözdüğü sorun:** Cumartesi turunda yazılan yorumlar hafta içi bayatlıyordu. Pazartesi
fiyat 50 günlük ortalamanın altına sarktığında dosyada hâlâ *"ortalamanın %+14.9
üzerinde"* yazıyordu. Haftada bir düşünen bir sistem, haftada bir yanılmıyor — altı gün
boyunca yanılıyor.

**İlke:** *Veri sürekli akar, yorum yalnızca anlam değişince güncellenir.* Her 30
dakikada bir LLM'e "durum ne?" diye sormak hem pahalı hem gürültülü olurdu; onun yerine
"anlam değişti mi?" sorusunu deterministik Python yanıtlıyor, LLM yalnızca eşik aşılınca
devreye giriyor.

### Zincir

```
dedektor.py           tezler.json'daki koşulları ölç (LLM YOK)
   │                  çıkış kodu: 0 = değişiklik yok
   ├── kod 10 ──────▶ yeniden_degerlendir.py — yalnızca o iddia, küçük model
   └── kod 20 ──────▶ yeniden_degerlendir.py — tüm tez, derin model + karar
                          └──▶ islem_uygula.py — kararı deterministik uygula
                                   └──▶ portfoy.json + KARAR_GUNLUGU.md (S#N)
```

### Şiddet seviyeleri

`tezler.json`'daki her koşul bir şiddet taşır — bir tezi ne kadar sarstığı:

| Şiddet | Anlamı | Çıkış kodu | Ne olur |
|---|---|---|---|
| `uyari` | Sadece işaret | 0 | Kaydedilir, 21:15 özetinde görünür. Yorum değişmez. |
| `iddia` | Tek iddia sarsıldı | 10 | Yalnızca o iddia küçük modelle yeniden yazılır. İşlem yok. |
| `tez` | Tez sorgulanır | 20 | Derin model pozisyonun tümünü değerlendirir, **işlem yapabilir**. |

### Flapping önleme

Eşiğin iki yanında salınan bir fiyat sürekli sinyal üretmesin diye üç katman:

1. **Histerezis** — bir koşul ihlalde sayılmak için **2 ardışık kontrolde** ihlalde
   kalmalı. Fiyat önceki kapanıştan %25'ten fazla saptıysa (bozuk veri barı olabilir)
   3 kontrol gerekir.
2. **Geri dönüş bandı** — eşiğin %1'i. 850 altı tetikler; temizlenmesi için 858.5 üstü
   gerekir.
3. **Cooldown** — aynı iddia 4 saat içinde ikinci kez yeniden yazılmaz.

### Tam yenileme (bilinmeyen bilinmeyenler)

Eşiğe bağlanmamış bir şey bozulmuş olabilir. Günde bir kez, ABD kapanışından sonra
(**21:15 UTC**) tüm iddialar eşik tetiklenmese de küçük modelle toplu gözden geçirilir.
Haftalık bütçe (`MAX_LLM_CAGRI_HAFTA`, varsayılan 60) aşılırsa yalnızca `tez` seviyesi
çağrılar yapılır — tez seviyesi bir tezin tümüyle çökmesi demektir, bütçeye kurban
edilmez.

### Seans içi işlem — neden LLM portfoy.json'a yazmıyor

Karar AI'ın (tüzük sürüm 2), ama **uygulaması aritmetik.** `islem_uygula.py` kararı
aynen uygular; önce şunları doğrular:

- **Fiyat LLM'den alınmaz.** Dolgu fiyatı dedektörün ölçtüğü seans içi bardır.
- Fiyat kaynağı canlı değilse (günlük kapanışa düşülmüşse) işlem yapılmaz.
- Seans kapalıysa işlem yapılmaz; karar gerekçesiyle Cumartesi turuna kalır.
- Nakit eksiye düşemez, elindekinden fazla adet satılamaz.
- Aynı gün aynı yönde ikinci işlem yapılmaz (`durum/islem_kilidi.json`).

Bunların hiçbiri *"bu karar yanlış"* demez — yalnızca *"bu sayılarla bu işlem
yapılamaz"* der. **Uygulanmayan karar da nedeniyle birlikte günlüğe yazılır**; sessiz
düşüş yok.

### Bildirim

- **`tez` seviyesi / işlem** → Zeynel'in DM'ine anında (`TELEGRAM_CHAT_ID_DM`).
- **`iddia` seviyesi** → anında bildirim yok; 21:15 tam yenileme özetinde toplu.

### Elle koşma

```bash
python dedektor.py --dry-run                      # ölçer, hiçbir dosyaya yazmaz
python dedektor.py --sabit-veri tests/ornek.json  # ağ yok, sahte veriyle
python yeniden_degerlendir.py --kod 10 --dry-run  # LLM çağrısı yok, promptu basar
python islem_uygula.py --dry-run                  # ne yapacağını söyler, yapmaz
python -m unittest discover -s tests -t .         # 73 test
```

Actions → **Seans İçi Dedektör** → Run workflow ile de elle koşulabilir
(`tam_yenileme` kutusu tüm iddiaları gözden geçirir).

> ⚠️ Bu bir deneydir, yatırım tavsiyesi değildir.
