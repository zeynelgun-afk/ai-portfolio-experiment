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
- AI tema eşleştirmesi yalnızca verilen haber kimliklerine ve sektör adlarına
  dayanabilir; uydurulmuş veya kaynaksız eşleşmeler atılır.
- Adayları `state/theme_research_inbox.json` içinde yeni, devam eden veya artık
  doğrulanmayan olarak izler. Ana `state/watchlist.json` değişmez.
- Tema sıralamalarını ve yeni araştırma adaylarını mevcut haftalık Telegram raporuna
  ekler; hisse havuzu üyelik bildirimi ayrı ve yalnızca değişiklikte gönderilir.

ETF'ler FMP EOD ile alınır; uygun tarih/veri doğrulamasından geçmeyen seride mevcut
yfinance yedeği denenir. Eksik temalar gizlenmek yerine veri eksikliği olarak
kaydedilir. Çalışan ilk sürüm 24 ETF tarihçesi ve bir SPY karşılaştırması için tarama
başına yaklaşık 26 FMP isteği yapar. FMP [ETF holdings](https://site.financialmodelingprep.com/developer/docs/stable/holdings)
ve disclosure verileri tema bileşenlerini ve kurumsal portföy açıklamalarını
araştırmaya yardım edebilir, ancak tek başına anlık net fon akışı ölçümü değildir.
FRED faiz/makro serileri ve EIA enerji serileri daha sonra
ilgili temalara **bağlam/teyit** sağlayabilir; fiyat getirileriyle aynı puana
karıştırılmaz. EIA/FRED anahtarları şu an GitHub Actions repository secret'larında
bulunmadığı için enerji/makro teyidi henüz bu iş akışına bağlanmadı; ilk tema
sıralaması FMP verisiyle çalışır. FRED ekonomik gözlem serileri sunar; EIA da
elektrik ve diğer enerji veri serilerine erişim sağlar, bu nedenle bunlar fiyat
sıralamasından çok tema tezi için makro/arz-talep bağlamı ekler.

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

## Sonraki geliştirme: tema genişliği ve akış teyidi

Bir sonraki adım, ETF'nin tek başına getirisini temanın tamamı gibi göstermemek için
FMP ETF holdings verisinden tarihli/yenilenme zamanı belli bileşen listesini
çıkarmak ve bileşenlerin eşit ağırlıklı getiri/genişliğini ayrıca ölçmektir. İzleme
kaydı tema tanımı, bileşen sembolleri, sağlayıcı, ölçüm zamanı, ağırlıklandırma ve
veri boşluklarını saklamalı. Bileşen kaynağı güncel değilse genişlik skoru
hesaplanmamalı.

Akış verisi gerçekten erişilebilir ve tanımı doğrulanmış ayrı bir sağlayıcıdan
gelirse (ETF pay adedi × fiyat/AUM etkisini ayırabilen akış serisi), bu gösterge
fiyat momentumu ve breadth'ten ayrı raporlanmalı. Şimdilik veri kaynağı olduğu
gösterilmeyen dış Theme Tracker ekranı sisteme dahil değil; aynı amaca FMP'nin
tarih damgalı sektör, ETF fiyatı ve haber verileriyle yaklaşıyoruz.
