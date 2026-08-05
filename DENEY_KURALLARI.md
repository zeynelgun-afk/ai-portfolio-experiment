# AI Portföy Deneyi — Tüzük

**Başlangıç:** 5 Ağustos 2026 · **Sanal sermaye:** 100.000 $ · **Süre:** 12 ay (hedef bitiş: 5 Ağustos 2027)

## Hipotez
Duygusuz, kurallara sadık bir AI karar vericisi; yazılı tez, sabit risk kuralları ve disiplinli
gözden geçirme ile agresif bir portföyü insan davranışsal hatalarından (panik satışı, FOMO,
zarara sarılma) arındırılmış şekilde yönetebilir mi?

**Kullanıcının hedefi:** 1 yılda 3-5 kat. **AI'ın kaydı:** Bu hedef istatistiksel olarak aşırı
iddialıdır; buna oynamak yüksek konsantrasyon ve %30-50'lik ara düşüşleri kabul etmek demektir.
Deney bu gerilimi de ölçer. Gerçekçi başarı çıtası: 12 ayda S&P 500'ü belirgin farkla yenmek.

## Evren
ABD büyük teknoloji + yarı iletken/AI altyapısı (hisse senetleri; kaldıraç ve opsiyon YOK).

## Karar kuralları (AI kendisi belirledi — değiştirilemez, ancak günlüğe yazılı gerekçeyle revize edilebilir)
1. **Pozisyon limiti:** Tek hissede maks. %35. Toplam 4-7 pozisyon. Nakit %0-30 serbest.
2. **Her işlemin şartı:** Yazılı tez + giriş fiyatı + stop seviyesi + gözden geçirme tetikleyicisi.
   Gerekçesiz işlem yapılamaz.
3. **Stop disiplini:** Stoplar haftalık kapanış bazlıdır (gün içi takip yok). Haftalık kapanış
   stop altındaysa bir sonraki kontrolde pozisyon KAPATILIR — tez ne kadar güzel olursa olsun.
4. **Kovalamama kuralı:** Tek günde +%15'ten fazla yükselmiş hisseye o gün girilmez (PLTR kuralı).
5. **Bilanço kuralı:** Bilançoya 1 haftadan az kala yeni tam pozisyon açılmaz; mevcut pozisyon
   bilinçli olarak taşınabilir (günlüğe not düşülür).
6. **Ekleme kuralı:** Kazanan pozisyona eklenebilir; kaybeden pozisyona "ortalama düşürme"
   yalnızca tez bozulmamışsa ve en fazla 1 kez yapılabilir.
7. **Kontrol sıklığı:** Haftalık gözden geçirme (kullanıcı "portföyü güncelle" dediğinde) +
   olay bazlı (portföy hissesinin bilanço tarihi, sert sektör hareketi).
8. **Kâr realizasyonu:** Pozisyon %35'i aşarsa fazlası kırpılır (rebalans). İkiye katlanan
   pozisyonda maliyetin bir kısmı çıkarılabilir — günlüğe yazılır.

## Ölçüm
- Kıyas: SPY (S&P 500) ve SMH (yarı iletken endeksi), aynı tarihte 100.000 $ alınmış varsayılır.
  Referans fiyatlar (4 Ağu 2026 kapanış): portföy girişleriyle aynı gün baz alınır.
- Metrikler: toplam getiri, maks. düşüş (haftalık bazda), isabet oranı, işlem sayısı.
- Tüm kararlar KARAR_GUNLUGU.md'de; portföy durumu portfoy.json'da.

## Dürüstlük maddeleri
- Dolgular (fill) son kapanış/son fiyattan varsayılır; slipaj ve komisyon ihmal edilir (kağıt deney).
- AI geleceği bilmez; bu deney tahmin gücünü değil, DİSİPLİNİN katkısını ölçer.
- Bu deney yatırım tavsiyesi değildir; gerçek parayla birebir kopyalanmamalıdır.
