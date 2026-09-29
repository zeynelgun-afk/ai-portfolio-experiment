# Şirket değişimi + bilanço çevresindeki haberler: ilk pilot

29 Eylül 2026. **Keşif amaçlı; getiri avantajı veya nedensellik kanıtlanmadı.**

47 olaylık sayısal pilotun içinden, altı şirketin her biri için 60 işlem günü tamamlanan en son bilanço seçildi. Seçim getiri değerine göre yapılmadı. Her olayın önceki ve yeni toplantı metni eşleştirildi (12 metin). Bilanço tarihinden iki takvim günü öncesinden bilanço günü sonuna kadar 31 haber kaydı eklendi. Daha sonra yayımlanan haberler bu etikete katılmadı.

## Karşılaştırma

İki ayrı fiyat verisi görmeyen model değerlendirmesi yapıldı: (A) önceki/yeni toplantı metni; (B) aynı metinler + olay penceresindeki haberler. Model altı boyutu değerlendiriyor: talep/sipariş, ticarileşme, marj, nakit/finansman, aynı dönem ileriye dönük beklenti, rekabet konumu. Her bilinen yön her iki dönemden kaynak kimliği gerektiriyor. İngilizce istem, Türkçe açıklama üretiyor.

İkinci kaynak inceleme çağrısı ve hedefli elle kaynak kontrolü eklendi. Etiketler fiyatlara bağlanmadan önce dosyaya yazılır. Bununla birlikte önceden eğitilmiş modelin geleceği bilmesi engellenemez; elle düzeltmeler fiyatlar görüldükten sonra yapıldı. Bu bir kör doğrulama veya out-of-sample test değildir.

## Kaynakta kontrol edilen değişimler ve ardından fiyat

Fiyat sütunları bilanço tarihinden sonraki NYSE seans kapanışından başlar. Bölünme/temettü düzeltilmiş, maliyet öncesi getiri; açıklama anındaki sıçrama dahil değil.

| Şirket / bilanço | Kaynakta görülen değişim ve karşı kanıt | 20 seans | 60 seans | Sonraki bilanço öncesi |
|---|---|---:|---:|---:|
| ACMR / 2026-05-07 | Brüt marj önceki çeyrekte %41,0 iken %46,5; sevkiyatların yaklaşık %15’i önceki çeyrekten ertelenen teslimatlar. Bu nedenle büyümenin tamamı yeni talep sayılmamalı. | %34.62 | %33.50 | %31.96 |
| AEHR / 2026-04-07 | Çeyrek siparişi 37 milyon doların üzerinde; açıklama gününe kadarki ek siparişlerle etkin birikmiş sipariş 50 milyon doların üzerinde. 14 milyon dolarlık üretim siparişi ve silikon fotonik müşteri kazanımı anlatılıyor. ATM hisse ihracı karşı kanıt. | %53.15 | %14.52 | %7.69 |
| AOSL / 2026-05-06 | Non-GAAP brüt marj %22,2’den %21,7’ye geriliyor. AI/veri merkezi anlatımı mevcut operasyonel marj zayıflığını ortadan kaldırmıyor. | %12.21 | %-9.78 | %-6.94 |
| ICHR / 2026-05-04 | Brüt marj %12,8’e yükseliyor (+110 baz puan çeyreklik); faaliyetlerden nakit akışı eksi 2,9 milyon dolar. Marj ve nakit farklı yönlerde. | %6.91 | %11.07 | %11.07 |
| PDFS / 2026-05-07 | Brüt marj %77’den %76’ya gerilerken faaliyet marjı %24’ten %25’e yükseliyor. Birleşik marj boyutuna tek yön vermek uygun değil. | %9.05 | %-4.20 | %-4.20 |
| PLAB / 2026-05-28 | Brüt marj %35’ten %31’e, faaliyet marjı %24’ten %20’ye geriliyor. Farklı çeyreklerin yönlendirme seviyeleri beklenti indirimi gibi sayılmamalı. | %-3.31 | %-9.37 | %-9.37 |

Şirket açıklamaları yönetimin bildirimleridir; burada yapılan kaynak kontrolü iddianın metinde bulunduğunu doğrular, bağımsız ticari doğrulama değildir. Bulgular fiyat hareketinin nedeni olduğunu kanıtlamaz. Özellikle AEHR’de kısa vadeli yükselişin önemli kısmı 60 seans sonunda korunmamıştır.

## Haberlerin ek katkısı

Bu altı olayda haber eklenen ve eklenmeyen değerlendirmelerin genel grup etiketleri aynı kaldı. Bu küçük pilotta haberlerin ilave tahmin gücü gösterilmedi. Haberler aynı basın açıklamasını veya toplantıyı tekrar edebiliyor; URL/başlık/metin tekrarları filtreleniyor fakat bütün yeniden yazımlar otomatik yakalanamaz. Haber sayısı bağımsız kanıt sayısı değildir.

Bilanço sonrası yeni haberlerle karar güncelleme ayrı bir sonraki testtir: yeni etiketin giriş/ölçüm tarihi de ileri alınmalıdır. Sonradan öğrenilen haber ilk gün biliniyormuş gibi kullanılamaz.

## Bulunan değerlendirme hataları ve koruma

- AEHR’de çeyreklik marj iyileşmesi yıllık düşüşle karıştırıldı; önceki/yeni çeyrek karşılaştırması düzeltildi.
- AEHR’de aynı yıllık tahmin aralığının üstüne yönelim sayısal aralık artırımı sayılmadı.
- AOSL/PLAB için farklı çeyreklerin tahminleri aynı dönem beklenti revizyonu olarak kabul edilmedi.
- PDFS’de brüt marj ve faaliyet marjının ters yönleri unknown olarak ayrıldı.
- Yeni ürün duyurusu tek başına göreli rekabet üstünlüğü sayılmadı. ACMR’de hisse satışı nakdi faaliyet nakdiyle bir tutulmadı.
- Modelin kaynak kimliklerini doğru seçmesi anlamsal doğruluk kanıtı değil. Tam anlamsal kabul yapılmadığı için programın doğrulanmış summary alanı boş; model grupları yalnız annotation_summary altında. strategy_validated=false.

## Dosyalar ve tekrar üretim

- `earnings_study.py`: sayısal pilot ve ağsız tekrar.
- `earnings_change_study.py`: ardışık toplantı metinlerini toplama, ilk model değerlendirmesi.
- `earnings_news_study.py`: tarih/şirket filtresi ve haber eklenmiş değerlendirme.
- `earnings_change_review.py`: ilk etiketleri değiştirmeden ayrı ikinci inceleme.
- Yerel ham veriler: `output/earnings-study/20260929T091954Z/inputs.json`.
- Metin/ilk etiketler: `output/earnings-change/20260929-pilot/`.
- Haberler/ilk etiketler: `output/earnings-news/20260929-pilot/`.
- İkinci inceleme: her klasörün `reviewed-v2/` altı. İlk incelemenin JSON biçimi uyumsuzluğu kaydı `reviewed/` altında korunur.
- Hedefli düzeltmeler ve nihai keşif raporları: her klasörün `checked/report.json` dosyası; corrections alanında önce/sonra kaydı var.

Yeni çalışma örneği (API anahtarları ortamda):

```bash
python earnings_change_study.py --baseline output/earnings-study/20260929T091954Z/report.json --output output/earnings-change/YENI --annotate
python earnings_news_study.py --source-dir output/earnings-change/YENI --baseline output/earnings-study/20260929T091954Z/report.json --output output/earnings-news/YENI
python earnings_change_review.py --source-dir output/earnings-change/YENI --labels-dir output/earnings-news/YENI --baseline output/earnings-study/20260929T091954Z/report.json --output output/earnings-news/YENI-inceleme
```

Bu komutlar mevcut snapshot dizinlerinin üzerine yazmaz. İnceleme API maliyeti doğurur. Portföy, işlem kuralları, zamanlayıcı ve Telegram akışı değiştirilmedi. Sürekli ileriye dönük takip henüz kurulmadı.

## Devam için gerekli

Önce elle etiketlenmiş değerlendirme örnekleriyle dönem/ölçüt karışıklıkları için model kabul testi; ardından temsili ve olay tarihinde bilinen evren, sektör/büyüklük eşleştirmesi, geçmiş konsensüs sürümleri, haber erişim zamanı ve önceden ayrılmış test dönemi. Daha fazla çağrı yapmak tek başına bu açıkları kapatmaz.
