# AI Portföy Deneyi — Tüzük

**Başlangıç:** 5 Ağustos 2026 · **Sanal sermaye:** 100.000 $ · **Süre:** 12 ay (hedef bitiş: 5 Ağustos 2027)

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

Kuralın yerini tek bir şart alır: **kararın gerekçesi yazılır.**
İşlem yapmamak da bir karardır ve o da yazılır.

## Değişmez ilkeler

Bunlar strateji kısıtı değildir; deneyin ölçülebilir ve dürüst kalmasını sağlar.

1. **Her karar günlüğe yazılır:** tez, giriş, çıkış planı ve *tezin yanlış olduğunu gösterecek
   işaret* (neyi görürsem fikrimi değiştiririm).
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
- **Nitel:** gerekçe kalitesi — sonradan bakıldığında tez tuttu mu, tutmadıysa AI bunu
  kabul etti mi yoksa gerekçeyi sonuca uydurdu mu.
- Tüm kararlar `KARAR_GUNLUGU.md`'de; portföy durumu `portfoy.json`'da.
