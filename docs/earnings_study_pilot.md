# Bilanço sonrası hareket: ilk veri ve ölçüm pilotu

Ölçüm tarihi: 2026-09-29T09:19:54.693838+00:00

**Durum: keşif amaçlı; strateji doğrulanmadı.** Bu çalışma bir alım sinyali veya portföy getirisi değildir.

## Kapsam

AEHR, ACMR, PDFS, PLAB, AOSL ve ICHR: erişim testi için elle seçilen, yarı iletken alanında yoğunlaşmış altı mevcut şirket. Olay tarihindeki küçük şirket sınıflaması doğrulanmadı. Borsadan çıkan şirketler dahil değil.

Toplam 47 bilanço olayı. Veri hatası: 0. Fiyat sağlayıcıları: {"ACMR": "FMP", "AEHR": "FMP", "AOSL": "FMP", "ICHR": "FMP", "IWM": "FMP", "PDFS": "FMP", "PLAB": "FMP"}.

FMP earnings alanları: symbol, date, epsActual, epsEstimated, revenueActual, revenueEstimated, lastUpdated. Kesin yayın saati ve tahminin bilanço öncesi sürümü yok. Canlı AEHR kontrolünde geçmiş bilanço lastUpdated değeri 2026-09-29: eski konsensüsün değişmediği kanıtlanamıyor.

AEHR için historical-market-capitalization erişimi ve 2025 Q3 earning-call-transcript erişimi ayrıca başarılı. Bu erişim kontrolü, bütün evrende tarihsel kapsamı veya noktasal zaman doğruluğunu kanıtlamaz.

## Ölçüm kuralları

- Son 700 takvim günündeki olaylar; giriş, olay tarihinden sonraki NYSE seansının kapanışı. Açıklama saati eksik olduğu için ilk erişilebilir fiyat iddiası yok.
- Bölünme/temettü düzeltilmiş seri; 20 ve 60 işlem günü. Gelecek planlanmış tarihler yerine yalnızca sonradan gerçekleşmiş bilançodan önceki son seans ayrıca ölçülür.
- Eksik seans, yinelenen olay veya şirket uyuşmazlığıyla ölçüm yapılmaz; tamamlanmayan ufuk pending kalır.
- Negatif EPS daha az negatif geldiğinde sürpriz pozitif olabilir. Sıfıra bölünen sürpriz yüzdesi kullanılmaz.
- IWM yalnızca geniş büyüklük karşılaştırmasıdır; sektör eşleştirmesi değildir.
- 0/25/100 baz puan toplam giriş-çıkış maliyeti duyarlılığı. Bunlar ölçülmüş maliyetler değildir.
- Azami düşüş, pozisyon süresindeki düzeltilmiş kapanışların zirveden düşüşüdür; gün içi kaybı kapsamaz.

## İlk sonuçlar: 60 işlem günü, maliyet öncesi

| Grup | Olay | Ortalama | Medyan | Pozitif sonuç | En kötü kapanış düşüşü |
|---|---:|---:|---:|---:|---:|
| EPS ve ciro beklentiyi aştı | 18 | %9.27 | %3.43 | %50.0 | %-61.05 |
| Yalnız EPS beklentiyi aştı | 9 | %43.75 | %14.52 | %77.8 | %-39.99 |
| EPS beklentiyi aşmadı | 14 | %34.15 | %37.56 | %71.4 | %-52.48 |

Grup büyüklükleri, tarihler ve şirket bileşimleri farklıdır; olaylar bağımsız değildir. Bu tablo istatistiksel üstünlük kanıtlamaz. Bu örneklem, birlikte EPS/ciro aşımının üstünlüğünü göstermiyor. Yüksek ortalama getiriler temsili olmayan sektör/şirket seçiminin etkisini taşıyabilir.

## Tekrar üretim

`earnings_study.py --output output/earnings-study/YENI_KLASOR` (FMP_API_KEY ortamda bulunmalı).

`earnings_study.py --replay output/earnings-study/20260929T091954Z/inputs.json --output output/earnings-study/YENI_TEKRAR_KLASOR`

Komutları proje Python ortamıyla çalıştırın. Ham veri output altında yerel tutulur; yeniden çalıştırma mevcut dizinin üzerine yazmaz. Ağsız tekrarın olayları ve özetleri ilk koşuyla birebir doğrulandı.

Girdi SHA256: `77defbc492750d7eeb0a9ba8d3d46e6fd92bdcea2ec53f57c7bbfd4f585bb401`

## Sonraki doğrulama kapıları

1. Olay tarihindeki evren, piyasa değeri, likidite ve borsadan çıkan şirket kapsamı kurulmalı.
2. Önceden saklanmış konsensüs ve gerçek açıklama zamanları doğrulanmalı. Bugünkü snapshot geçmiş için zaman doğruluğu sağlamaz.
3. Sektör/büyüklük eşleştirmesi ve bağımsız test dönemi önceden belirlenmeli.
4. Faaliyet dönüşümü ve bilanço çevresi haberleri için altı olaylık ikinci pilot eklendi (earnings_change_pilot.md). Bağımsız sektör doğrulaması ve ileriye dönük model doğrulaması hâlâ gerekli.
5. Periyodik canlı snapshot toplama ve Telegram hata bildirimleri devreye alınmadan sürekli takip başladı denmemeli. Bu pilot elle çalıştırılır; zamanlayıcıya bağlı değildir.

## Kaynak yöntemi

- FMP resmi veri alanları: https://site.financialmodelingprep.com/developer/docs
- PEAD zayıflaması: https://doi.org/10.1177/0148558X261439734
- Metin ve PEAD: https://doi.org/10.1017/S0022109022001181
- Sektör doğrulaması: https://doi.org/10.1111/1911-3846.12210
