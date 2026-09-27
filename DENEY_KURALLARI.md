# AI Portföy Deneyi — Tüzük

**Başlangıç:** 5 Ağustos 2026 · **Sanal sermaye:** 100.000 $ · **Süre:** 12 ay (hedef bitiş: 5 Ağustos 2027)

> **Sürüm 3 — 27 Eylül 2026.** Karar sıklığı haftalıktan olay güdümlüye geçti.
> Eskiden tek karar anı Cumartesi turuydu; hafta içi yazılmış yorumlar bayatlıyordu
> (Pazartesi 50 günlük ortalamanın altına sarkan bir fiyat için dosyada hâlâ
> "ortalamanın %+14.9 üzerinde" yazıyordu). Artık `dedektor.py` seans içinde 30
> dakikada bir tez geçerlilik koşullarını ölçüyor ve eşik aşılırsa AI aynı gün
> karar veriyor — işlem dahil. Kullanıcı kararı: tam otonom, onay kapısı yok.
> Gerekçe ve şema için README "Olay Güdümlü Yeniden Değerlendirme" bölümü.
>
> **Sürüm 2 — 8 Ağustos 2026.** Tüzük sadeleştirildi: ayrıntılı karar kuralları kaldırıldı,
> kararın tamamı yapay zekâya bırakıldı. Gerekçe ve önceki sürüm için KARAR_GUNLUGU.md
> denetim kaydına bakınız.

## Hipotez

Kararı yapay zekâ verir. Sınır, kuralların sayısı değil; her kararın **yazılı gerekçesi** ve
ölçülebilir sonucudur.

Ölçülen soru: *Serbest bırakılmış ama her hamlesini yazmak ve sonucuna sahip çıkmak zorunda
olan bir AI, 12 ayda piyasayı yenebilir mi?*

**Kullanıcının hedefi:** 1 yılda 3-5 kat. **AI'ın kaydı:** Bu hedef istatistiksel olarak aşırı
iddialıdır; buna oynamak yüksek konsantrasyon ve %30-50'lik ara düşüşleri kabul etmek demektir.
Deney bu gerilimi de ölçer. Gerçekçi başarı çıtası: 12 ayda S&P 500'ü belirgin farkla yenmek.

## Evren

ABD büyük teknoloji + yarı iletken/AI altyapısı. Spot hisse senedi; kaldıraç ve opsiyon YOK.
(Bu sınır bir strateji kısıtı değil — kıyaslamanın anlamlı kalması için var.)

## Karar yetkisi — tamamen AI'da

Aşağıdakilerin hepsi AI'ın takdirindedir. Üst sınır, alt sınır, zorunlu eşik yoktur:

- Pozisyon sayısı, tek hissedeki ağırlık, nakit oranı
- Giriş ve çıkış zamanlaması; ekleme, kırpma, kâr realizasyonu
- Stop/çıkış seviyeleri ve bunların ne zaman değiştirileceği
- Bilanço öncesi veya sonrası pozisyon taşıma
- Ne kadar yoğunlaşacağı, ne kadar bekleyeceği
- **Kararın ne zaman verileceği.** Karar anı Cumartesi turuyla sınırlı değildir;
  hafta içi seans içinde de karar verilebilir ve uygulanabilir (bkz. aşağıdaki
  "Karar anları").

Kuralın yerini tek bir şart alır: **kararın gerekçesi yazılır.**
İşlem yapmamak da bir karardır ve o da yazılır.

## Karar anları

İki tür karar turu vardır; ikisi de aynı hesap verme yükümlülüğüne tabidir.

1. **Haftalık tur** — Cumartesi 06:00 UTC. Tam kayıt (`HAFTALIK_TALIMAT.md` şablonu).
   Tezleri kuran ve `tezler.json`'ı yenileyen tur budur.
2. **Seans içi tur** — Pzt–Cum 13:30–20:00 UTC, 30 dakikada bir. Otomatik bir dedektör
   (`dedektor.py`) `tezler.json`'daki geçerlilik koşullarını deterministik ölçer.
   Eşik aşılırsa AI ya yalnızca ilgili iddiayı yeniden yazar (`iddia` seviyesi) ya da
   pozisyonun tüm tezini yeniden değerlendirip **işlem yapar** (`tez` seviyesi).

**Seans içi turun sınırları — strateji kısıtı değil, ölçüm ve veri bütünlüğü kısıtı:**

- **Fiyat AI'dan alınmaz.** Dolgu fiyatı dedektörün ölçtüğü seans içi bardır. AI'ın
  cümlesindeki bir sayı işleme dönüşmez.
- **Bir eşik iki ardışık kontrolde teyit edilmeden karar üretmez** (fiyat önceki
  kapanıştan %25'ten fazla saptıysa üç kontrol). Bozuk bir veri barı bir turluk
  gecikmeyle ayıklanır; gerçek bir çöküş 60 dakika içinde yine yakalanır.
- **Aritmetik doğrulanır:** nakit eksiye düşemez, elindekinden fazla adet satılamaz,
  aynı gün aynı yönde iki kez işlem yapılamaz. Bunlar kararı yargılamaz, yalnızca
  "bu sayılarla bu işlem yapılamaz" der.
- **Seans kapalıysa işlem yapılmaz**; karar gerekçesiyle kayda geçer ve Cumartesi
  turuna kalır.
- **Her seans içi karar günlüğe yazılır** (`S#N` kaydı), uygulanmayanlar dahil.

## Değişmez ilkeler

Bunlar strateji kısıtı değildir; deneyin ölçülebilir ve dürüst kalmasını sağlar.

1. **Her karar günlüğe yazılır:** tez, giriş, çıkış planı ve *tezin yanlış olduğunu gösterecek
   işaret* (neyi görürsem fikrimi değiştiririm). Sürüm 3'ten itibaren bu işaret ayrıca
   `tezler.json`'da **ölçülebilir bir koşul** olarak yazılır — bir tezin nasıl çürütüleceği
   yalnızca prose'da kalırsa hafta içi kimse kontrol edemez.
2. **Fikir değiştirmek serbest, sessizce değiştirmek değil.** Önceki turda söylediğinden
   sapıyorsan saptığını açıkça yaz. Denetlenen şey isabet değil, hesap verebilirliktir.
3. **Rakam uydurulmaz.** Fiyat, oran, temel veri yalnızca araçtan ve tarihiyle birlikte yazılır.
   Çekilemiyorsa yazılmaz — tez rakamsız kurulur.
4. **AI bu dosyayı ve `HAFTALIK_TALIMAT.md`'yi değiştiremez.** Değişiklik önerir, kullanıcı
   denetimde karara bağlar.
5. **Geçmişe dönük düzeltme yok.** Dolgular son kapanıştan varsayılır; slipaj ve komisyon
   ihmal edilir (kâğıt deney). Yazılmış bir tez sonradan güzelleştirilmez.
6. Bu deney yatırım tavsiyesi değildir; gerçek parayla birebir kopyalanmamalıdır.

## Ölçüm

- **Kıyas:** SPY (S&P 500) ve SMH (yarı iletken endeksi), aynı tarihte 100.000 $ alınmış varsayılır.
  Referans fiyatlar `portfoy.json` içinde kayıtlı.
- **Nicel:** toplam getiri, maksimum düşüş (haftalık bazda), isabet oranı, işlem sayısı.
  Sürüm 3'ten itibaren işlem sayısı haftalık ve seans içi olarak ayrı ayrı okunabilir:
  seans içi işlemler `islem_gecmisi`'nde `"kaynak": "seans_ici_otonom"` etiketlidir.
  Ölçülecek yeni soru: *seans içi karar, haftalık karardan daha mı isabetli?*
- **Nitel:** gerekçe kalitesi — sonradan bakıldığında tez tuttu mu, tutmadıysa AI bunu
  kabul etti mi yoksa gerekçeyi sonuca uydurdu mu.
- Tüm kararlar `KARAR_GUNLUGU.md`'de; portföy durumu `portfoy.json`'da.
