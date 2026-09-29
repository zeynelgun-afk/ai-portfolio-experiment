# Bilanço değişimiyle araştırma havuzuna aday ekleme: geriye dönük doğrulama

## Karar

Bu test, bilanço sonrası **inceleme kuyruğuna aday üretmenin** makul bir fikir olduğunu gösteriyor; ancak mevcut karar/watchlist havuzuna otomatik eklemeyi veya performans avantajını doğrulamıyor. Teknoloji alt kümesinde sonuç zayıf, örneklem çok küçük ve tüm deney evreni 200 milyon–5 milyar dolar şirketlerden seçildiği için mevcut büyük teknoloji/AI altyapısı tüzüğüne uygunluğu sağlamıyor. Canlı `state/watchlist.json` ve karar/işlem akışı değiştirilmedi.

## Sınanan kural

Dosyalama tarihi itibarıyla aynı mali çeyreğin bir önceki yıla göre değişimleri kullanıldı: gelir pozitif, brüt marj genişleyen, faaliyet nakit akışı artan. En az iki ölçülebilir gösterge varsa ve ölçülebilenlerin tümü pozitifse olay “inceleme adayı” sayıldı. Aynı şirket için 60 NYSE işlem seansı içinde gelen yeni sinyal yeni aday sayılmadı; var olan adayın güncellemesi kabul edildi. Giriş/alım varsayılmadı: sonuçlar dosyalama sonrasındaki ilk seans kapanışından 20/60 seanslık fiyat değişimi ve IWM fazlası olarak ölçüldü.

Bu kural yalnızca finansal değişim bacağını sınar. Haber, rehberlik, konferans görüşmesi, sektör hikâyesi ve akran şirket gelişmeleri geriye dönük, zaman damgalı etiketlenmiş değildi.

## Bulgular

| Örneklem | Tekrarsız ekleme | Benzersiz şirket | 20 seans medyan fazla getiri / pozitif oran | 60 seans medyan fazla getiri / pozitif oran | 60 seans medyan düşüş | En kötü 60 seans hisse getirisi |
|---|---:|---:|---:|---:|---:|---:|
| Tüm pilot sektörleri | 34 | 11 | -0,39 puan / %47,1 | +0,76 puan / %55,9 | -%16,37 | -%52,64 |
| Teknoloji sektörü vekili | 7 | 3 | -1,93 puan / %42,9 | -15,26 puan / %42,9 | -%25,53 | -%24,82 |

100 baz puan varsayımsal gidiş-dönüş maliyeti sonrası tüm sektörlerde 60 seans medyan hisse getirisi %3,85’tir. Bu, IWM’den daha iyi seçim yaptığımızı göstermez; teknoloji vekilinde maliyet sonrası 60 seans medyan hisse getirisi -%15,93’tür. İstatistiksel güven aralığı, işlem yapılabilir spread/etki ve büyük teknoloji şirketleri için geçerli örneklem yoktur. 3 teknoloji şirketinden 7 olayla strateji hakkında kesin hüküm verilemez.

## Sistem açısından önerilen yerleşim

Mevcut `state/watchlist.json` Scout’ın seçtiği 15–20 sembolü içeriyor ve haftalık/intraday araştırma ile karar akışına besleniyor. Bu nedenle yeni yöntemi oraya otomatik eklemek küçük bir etiket değişikliği değildir.

Önce ayrı, salt-okunur bir `earnings_research_inbox` denenebilir: aday kartında olay tarihi, dondurulmuş kaynak değerleri, göstergeler, açıklama/haber/rehberlik, sektör hareketi, karşı kanıtlar ve veri boşlukları tutulur. Kartın havuza girmesi portföy/watchlist üyeliği yaratmaz; haftalık raporda “incelemeye değer” olarak sunulur ve kullanıcı veya araştırma süreci yeterli kanıtı doğrularsa normal Scout/karar havuzuna taşınır. Aday oluşturma, güncelleme ve çıkarma ayrı olay kimlikleriyle kaydedilir; Telegram yalnızca yeni aday, önemli tez değişimi ve veri/işlem hatası için bildirim gönderir.

İleriye dönük testte her kartın olay anındaki finansal tablo değerleri, tahmin sürümü, haber metinleri ve yayın saatleri değiştirilemez biçimde saklanmalı. Önce 12 ay gölge modda havuza girme oranı, 20/60 seans sonrası IWM ve sektör fazlası, drawdown, şirket başına aday sayısı ve adayların araştırma ekibi tarafından doğrulanma oranı ölçülmeli. Haber/rehberlik/tema bacağı eklenmeden bilanço kuralının tamamını temsil ettiği varsayılmamalı.

## Tekrar üretme

```bash
python earnings_pool_validation.py \
  output/earnings-expanded/20260929-5y-20/replay-v5/report.json \
  --output output/earnings-expanded/20260929-5y-20/pool-validation.json
```

Çıktı: `output/earnings-expanded/20260929-5y-20/pool-validation.json`. Çalışma çevrimdışıdır; fiyatları veya watchlist'i değiştirmez.
