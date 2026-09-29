# Scout tema radarı ve hisse havuzu Telegram bildirimi

**Durum — 29 Eylül 2026:** İlk 23 sembollük araştırma havuzu, GitHub Actions'taki
Telegram bildirim iş akışı üzerinden iletildi. Sonraki havuz değişiklikleri Scout'ın
mevcut Cumartesi turunda bildirilecek. FMP tabanlı tema sıralaması eklendi; 29 Eylül'de
gerçek FMP verisiyle çalıştırıldı, 24/24 ETF vekili FMP'den geldi ve yfinance yedeği
gerekmedi. Kod testleri: 429 geçti.

## Tema Tracker yaklaşımı ve sisteme entegrasyonu

Evet, **hangi temaların araştırılacağını seçmek ve liderliğin sürüp sürmediğini
izlemek için** faydalı bir bağlam sunuyor. Görselde 1 haftalık ve 1 aylık pencerelerin
yan yana bulunması özellikle yararlı: örneğin yarı iletkenler iki pencerede de
güçlüyken genomik aylık pencerede öne çıkıyor; Bitcoin'in haftalık hareketi aylık
görünümünden daha kuvvetli. Bu ayrım kalıcılaşan eğilimle kısa süreli sıçramayı
ayırt etmeye yardımcı olabilir.

Bu görünümü görselden okumak yerine veri kaynağından üretmek daha güvenilir. Radar
şimdi FMP'nin [temettüye göre düzeltilmiş EOD fiyatları](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-dividend-adjusted)
ile şu ETF vekillerini ayrı bir panoda izliyor. Her tema bir sembolle temsil edilir;
örtüşme ve proxy'nin temayı eksik temsil etmesi mümkündür.

| Tema | FMP fiyat vekili |
|---|---|
| Bitcoin | IBIT |
| Yarı iletkenler | SMH |
| Genomik | ARKG |
| Kuantum bilişim | QTUM |
| Biyoteknoloji | XBI |
| Sağlık | XLV |
| Havayolları | JETS |
| Çin interneti | KWEB |
| Yapay zekâ | AIQ |
| Tıbbi cihazlar | IHI |
| Konut üreticileri | XHB |
| Bitcoin madencileri | WGMI |
| Robotik | BOTZ |
| Sanayi | XLI |
| Yazılım | IGV |
| Perakende | XRT |
| Sosyal medya | SOCL |
| Siber güvenlik | CIBR |
| Enerji | XLE |
| Uranyum | URA |
| Veri merkezleri | SRVR |
| Elektrik şebekesi | GRID |
| Bulut bilişim | SKYY |
| Savunma/havacılık | ITA |

Görseldeki yaklaşım gerçek fon/sermaye akışını kanıtlamıyor. Fiyat artışı para girişi
anlamına gelmez; tek bir ETF temayı kusursuz temsil etmez ve tema içindeki şirketler
aynı yönde gitmeyebilir. Bu nedenle ETF temaları **fiyat vekili** olarak etiketlenir;
hiçbir sıralama otomatik olarak karar havuzuna hisse eklemez.

## Çalışan tema radarı

`theme_radar.py`, haftalık Scout turundan ayrı bir araştırma kuyruğu oluşturur:

- ETF tema panosunda 5 işlem seansı ve 21 işlem seansı toplam getirileri ayrı ayrı
  sıralanır; her satır ETF sembolünü, veri tarihini ve mümkünse SPY fazlasını içerir.
  Haftalık getiri, aylık ortalama haftalık tempoyla da kıyaslanır; bu ivme farkı
  tahmin değildir.
- Son yedi gündeki tarihli genel haber başlıklarını ve kaynak bağlantılarını toplar.
- FMP'nin [günlük industry snapshot](https://site.financialmodelingprep.com/developer/docs/stable/industry-performance-snapshot)
  verisinden en güçlü 12 ve en zayıf 8 industry seçilir; bunların tarihsel performansı
  5/21/20/60 seans pencerelerinde ölçülür. [Tarihsel industry performansı](https://site.financialmodelingprep.com/developer/docs/stable/historical-industry-performance)
  üzerinden üretilen sınırlı örneklem tüm sektörlerin eksiksiz sıralaması değildir.
- Aday taraması için 20 ve 60 seanslık pencerelerde pozitif kalan en güçlü sektörleri seçer.
- Her önde gelen sektörde en büyük üç uygun ABD şirketini tarar. Adayın 20 ve 60
  seanslık toplam getirisi aynı tarihlerde ölçülen SPY getirisini aşmalıdır.
- Haber sağlayıcısının verdiği metin 1.200 karakterle sınırlı bir excerpt'tir.
  Radar artık haftalık en fazla 12 kaynak sayfasını, HTTPS ve herkese açık adres
  denetimiyle indirip JSON-LD `articleBody` veya makale alanındaki paragraflardan
  çıkarır. En az 1.200 karakter ve dört paragraf yoksa içerik açıkça excerpt-only/
  erişilemedi olarak etiketlenir. Gövde sadece analiz süresince bellekte tutulur;
  kalıcı inbox'ta URL, tarih, okuma durumu, kelime sayısı ve seçilen kanıt alıntısı
  saklanır. Bu erişim paywall'ları aşmaz; her makalenin tamamının erişilebilir
  olduğu iddia edilmez.
- Tam gövdesi çıkarılan haberlerde AI, şirket/ürün/komponent ve tedarik zinciri
  rolünü birebir haber alıntısıyla aday olarak çıkarabilir. Ticker ve şirket kimliği
  FMP profiliyle eşleştirilir; FMP'nin SEC dosya aramasındaki son 10-K/20-F/40-F
  raporu içeriği taranır ve asıl SEC dosya URL'si korunur. Yalnızca şirket raporunda
  ürün/komponent rolünü açıkça destekleyen, rapordan birebir alıntısı doğrulanan
  iddia ayrı araştırma havuzuna eklenir. Kısmi, çelişkili veya teyitsiz iddialar
  aday olmaz; haber iddiası tek başına şirket beyanı ya da ekonomik fayda kanıtı
  değildir.
- Bu ürün/komponent yolu sektör büyüklüğü ve fiyat filtresinden bağımsız olarak
  tedarik zinciri ipuçlarını araştırma kuyruğuna ekler. Fiyat teyidi varsa ayrıca
  gösterilir; yoksa aday yine yalnızca araştırma adayı olarak kalır. Ana
  `state/watchlist.json` ve alım-satım kararı değişmez.
- Adayları `state/theme_research_inbox.json` içinde yeni, devam eden veya artık
  doğrulanmayan olarak izler. Ana `state/watchlist.json` değişmez.
- Tema sıralamalarını ve yeni araştırma adaylarını mevcut haftalık Telegram raporuna
  ekler; hisse havuzu üyelik bildirimi ayrı ve yalnızca değişiklikte gönderilir.

ETF'ler FMP EOD ile alınır; uygun tarih/veri doğrulamasından geçmeyen seride mevcut
yfinance yedeği denenir. Eksik temalar gizlenmek yerine veri eksikliği olarak
kaydedilir. Tema fiyat panosu 24 ETF tarihçesi ve SPY karşılaştırması için yaklaşık
25 FMP isteği yapar; liderlere göre buna en fazla 10 holdings isteği ve bir toplu
fiyat isteği eklenir. Haber gövdesi okuyucu haftada en fazla 12 URL dener; tedarik
zinciri doğrulaması en fazla beş şirketi FMP SEC filing search ve yıllık rapor JSON
uçlarıyla kontrol eder. FMP [ETF holdings](https://site.financialmodelingprep.com/developer/docs/stable/holdings)
ve disclosure verileri tema bileşenlerini ve kurumsal portföy açıklamalarını
araştırmaya yardım edebilir, ancak tek başına anlık net fon akışı ölçümü değildir.
### Bileşen genişliği ve makro bağlamı

Tema sıralamasına, hem 1 haftalık hem 1 aylık ilk beş ETF'nin açıklanmış en yüksek
ağırlıklı en fazla 10 bileşeni için günlük yükselen/düşen oranı eklendi. Holdings
sembolleri ve ağırlıkları FMP [ETF holdings](https://site.financialmodelingprep.com/developer/docs/stable/holdings),
bileşenlerin güncel günlük değişimi ise tek bir FMP [batch quote](https://site.financialmodelingprep.com/developer/docs/stable/batch-quote)
isteğiyle alınır. Holdings tarih damgası 35 günden eskiyse o ETF'nin genişliği
hesaplanmaz; fiyat kotasyonu kapsamı %70'in altındaysa oran gösterilmez. Raporda
örneklem büyüklüğü ve holdings tarihi görünür. Bu ölçüm ETF'nin tüm bileşenlerini
kapsamaz, günlük kesitsel genişliktir ve uzun vadeli genişlik serisi değildir.

FRED'in [gözlem API'si](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)
10 yıllık Hazine faizi (DGS10) ve efektif federal fon faizi (FEDFUNDS) için son
gözlemi ve uygun olduğunda beş gözlem önceye göre değişimi sağlar. EIA'nın [API v2](https://www.eia.gov/opendata/documentation.php)
elektrik perakende satışları verisinde eyaletlerin `ALL` sektör toplamı birleştirilerek
son aylık ABD toplamı ve mümkünse yıllık/aylık değişimi çıkarılır. Eyalet bileşenleri
kullanılır; olası ulusal toplama satırı çifte sayımı önlemek için dışarıda bırakılır.
Her seri kendi gözlem tarihini taşır.
Telegram'da bunlar **makro bağlam (puanlamaya katılmaz)** olarak gösterilir; tema
getirisine, aday seçimine veya işlem kararına eklenmez.

GitHub Actions `weekly.yml` içine FRED ve EIA ortamları bağlandı; `FRED_API_KEY` ve
`EIA_API_KEY` repo secrets'larına eklendi. Haftalık araştırmada otomatik toplanır;
eksik/bozuk sağlayıcı verisi turu durdurmaz, eksik bağlam olarak kaydedilir.
Kullanılacak secrets: `FRED_API_KEY` ve `EIA_API_KEY`.

### Canlı FMP örnek anlık görüntüsü

Ölçüm: 28 Eylül 2026 kapanışı. Bu tarihli snapshot'ta 1 hafta (5 seans)
liderleri Genomics/ARKG **+2,97%**, Healthcare/XLV **+1,33%** ve
Semiconductors/SMH **+0,67%** oldu. 1 ay (21 seans) sıralaması Genomics/ARKG
**+6,98%**, Semiconductors/SMH **+4,71%** ve Bitcoin/IBIT **+4,24%** gösterdi.
Aynı dönem SPY getirileri sırasıyla **-%1,02** ve **-%0,47** idi. Bu, iki vadeli
sıralamanın üretilebildiğini doğrular; strateji getirisi, gelecek performans veya
doğrudan fon akışı hakkında kanıt değildir.

Sektör/hisse performansı para akışı ölçümü değildir. Haber ile şirket arasındaki
tema bağlantısı da bağımsız doğrulama değil, kaynak kimlikleri sınırlandırılmış AI
yorumudur. Sağlayıcı veya eşleştirme hataları aday kabulünü durdurur ve Telegram
hata bildirimi üretir. Bu keşif deneyi henüz performans avantajı kanıtlamaz.

## Hisse havuzu bildirimi

Scout ilk çalıştırmada havuzun tamamını, üyelik değiştiğinde ise eklenen ve çıkan
sembollerle birlikte yeni tam havuzu Telegram'a yollar. Liste değişmediyse tekrar
bildirim göndermez. `state/telegram_watchlist_state.json` yalnızca başarılı teslimat
sonrasında güncellenir; böylece başarısız bir Telegram isteği değişikliği sessizce
“gönderildi” olarak işaretlemez. Araştırma havuzu tek başına alım kararı değildir.

Scout 15–20 şirket seçse de mevcut portföydeki pozisyonlar havuzda tutulur. Bu
nedenle Telegram'daki toplam sembol sayısı 20'yi aşabilir. İlk havuz bildirimi
29 Eylül 2026'da gerçek GitHub Telegram eylemiyle gönderildi ve gönderim durumu
`state/telegram_watchlist_state.json` içine kaydedildi.

## Sonraki geliştirme: geniş kapsam ve akış teyidi

Gelecek deneylerde FMP'nin izin ve maliyet sınırları doğrulanarak tüm disclosed
holdings kapsamı, ağırlıklı genişlik ve birkaç haftalık kalıcılık ölçülebilir. Mevcut
ilk 10 örneklem bu geniş kapsamlı ölçümlerin yerine geçmez.

Akış verisi gerçekten erişilebilir ve tanımı doğrulanmış ayrı bir sağlayıcıdan
gelirse (ETF pay adedi × fiyat/AUM etkisini ayırabilen akış serisi), bu gösterge
fiyat momentumu ve breadth'ten ayrı raporlanmalı. Şimdilik veri kaynağı olduğu
gösterilmeyen dış Theme Tracker ekranı sisteme dahil değil; aynı amaca FMP'nin
tarih damgalı sektör, ETF fiyatı ve haber verileriyle yaklaşıyoruz.
