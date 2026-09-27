# Karar Günlüğü — AI Portföy Deneyi

Her giriş: tarih, karar, tez, riskler, stop, gözden geçirme tetikleyicisi.

**İki kayıt tipi var:**

- `## #N — <tarih> · HAFTALIK TUR` — Cumartesi 06:00 UTC karar turu. Tam kayıt
  (A–F bölümleri, `HAFTALIK_TALIMAT.md` şablonu). Tezleri kuran tur budur.
- `## S#N — <tarih> <saat> UTC · SEANS İÇİ KARAR` — hafta içi olay güdümlü tur.
  `dedektor.py` bir tez geçerlilik koşulunun eşiğini aşıldığını ölçtüğünde
  (2 ardışık kontrolde teyitli) derin model pozisyonun tezini yeniden değerlendirir;
  karar `islem_uygula.py` tarafından deterministik uygulanır. Kısa kayıt: tetikleyici,
  dolgu, tez değerlendirmesi, gerekçe, çarpıtma işareti. Uygulanmayan kararlar da
  nedeniyle birlikte buraya yazılır — sessiz düşüş yok.

Seans içi kararlar `S#` numarasıyla ayrı sayılır; haftalık tur numaralandırması
(`#N`) bozulmaz. Her seans içi işlem `portfoy.json` → `islem_gecmisi`'nde
`"kaynak": "seans_ici_otonom"` etiketiyle görünür.

---

## #1 — 5 Ağustos 2026 · İLK PORTFÖY KURULUMU

**Piyasa bağlamı:** AI altyapı rallisi sürüyor; yarı iletkenler Temmuz sonunda sert düzeltme
yaşadı, dün (4 Ağu) güçlü tepki günüydü (SMH benzeri sepette +%6-13 hareketler). S&P 500 rekor
tazeledi. Bellek süper döngüsü (HBM/DRAM/NAND) temanın en sıcak cephesi.

**Tarama sonucu (14 aday):** ORCL ve SMCI elendi (fiyat 50 ve 200 günlük ortalamaların altında,
trend kırık). PLTR elendi (dün +%29,5 — kovalamama kuralı). MSFT/GOOGL/NVDA elendi (kalite yüksek
ama 3-5x hedefi için beta yetersiz; NVDA ileride tekrar değerlendirilebilir). TSM/MRVL/VRT izleme
listesinde (50 günlük altında, dönüş teyidi bekleniyor).

### AL: MU — %30 (30.000 $, 33,6072 adet @ 892,67 $)
**Tez:** Bellek süper döngüsünün ana oyuncusu. Son çeyrek: gelir 41,5 mlr $ (yıllık +%345),
brüt marj %84,6, EPS 25,04 $. TTM F/K ~20, ileri F/K ~5-6. Analist konsensüsü Buy (57 Al/11 Tut),
medyan hedef 1.512 $. Teknik: zirveden %29 düzeltmiş, 738-770 $ desteği iki kez tuttu, RSI 48.
Düzeltme içinde güçlü trend — asimetri lehimize.
**Risk:** Döngü dönerse marjlar çöker (tarihsel olarak %60-70 düşüşler görülmüştür). SK Hynix
HBM rekabeti. Haftalık ±%20 oynaklık normal.
**Stop:** Haftalık kapanış < 730 $. **Tetikleyici:** 22 Eylül bilançosu — öncesinde gözden geçir.

### AL: AMD — %20 (20.000 $, 38,5668 adet @ 518,58 $)
**Tez:** AI hızlandırıcı pazarında NVDA'ya tek gerçek alternatif; MI serisi ivmesi. Teknik olarak
en sağlıklı görünüm: fiyat > 50g (513) > 200g (313), zirveye %11 mesafe. Dün +%7 ile tepkiye katıldı.
**Risk:** NVDA'nın rekabet baskısı; yüksek beklenti çarpanı.
**Stop:** Haftalık kapanış < 440 $.

### AL: SNDK — %15 (15.000 $, 10,507 adet @ 1.427,62 $)
**Tez:** AI depolama/NAND cephesinin saf oyuncusu; portföyün en yüksek risk/getiri bacağı.
Zirveden %39 düzeltmiş, dün +%10,8 dönüş sinyali; 200g ortalama (849) çok aşağıda — ana trend ayakta.
Yıl içi 40 $ → 2.354 $ aralığı gücün (ve oynaklığın) kanıtı.
**Risk:** NAND, HBM'den çok daha döngüseldir; düzeltme derinleşebilir. En geniş stop bu yüzden.
**Stop:** Haftalık kapanış < 1.100 $.

### AL: ANET — %15 (15.000 $, 78,736 adet @ 190,51 $)
**Tez:** AI veri merkezi ağ donanımının lideri; hisse dün 52 hafta zirvesini KIRDI (190,5 > eski
zirve) — momentum girişi. Fiyat > 50g (167) > 200g (146).
**Risk:** Zirve kırılımı sahte çıkabilir (bull trap).
**Stop:** Haftalık kapanış < 160 $.

### AL: AVGO — %10 (10.000 $, 23,9143 adet @ 418,16 $)
**Tez:** Özel AI çipleri (XPU) + ağ; portföyün "denge" bacağı. Fiyat > 50g > 200g, zirveye %16.
**Risk:** Beta düşük — 3-5x hedefine katkısı sınırlı, rolü düşüşleri yumuşatmak.
**Stop:** Haftalık kapanış < 350 $.

### NAKİT — %10 (10.000 $)
Sert düzeltmede kullanılacak kuru barut. MRVL/TSM/VRT dönüş teyidi verirse aday.

**Portföy karakteri:** %90 yatırımda, 5 pozisyon, tamamı AI altyapı teması — bilinçli konsantrasyon.
Bu portföyün tek büyük riski temanın kendisi: AI harcama döngüsü kırılırsa hepsi birlikte düşer.
Agresif hedefin bedeli bu.

**Sonraki gözden geçirme:** ~12 Ağustos 2026 (haftalık) veya kullanıcı istediğinde.

---

## #2 — 5 Ağustos 2026 · HAFTALIK TUR (İLK GÜN KONTROLÜ)

**Piyasa bağlamı:** Portföy dün (5 Ağustos) kuruldu. Veriler 4 Ağustos kapanış bazlı;
piyasa henüz açık değil (UTC 06:29). AMD ve ANET bilançoları dün gerçekleşti, SNDK bilançosu bugün.

**Teknik durum — Mevcut pozisyonlar:**
- **MU (892.67 $):** Fiyat < SMA50 (969) ancak >> SMA200 (525), RSI 49. 1ay -9,4%, 3ay +72,6%. 
  Stop 730 $ (%+22,3 mesafe). Bilanço 23 Eylül. Güvenli bölge.
- **AMD (518.58 $):** Fiyat > SMA50 (514) >> SMA200 (315), RSI 48. 1ay -6,1%, 3ay +46,3%. 
  Stop 440 $ (%+17,9 mesafe). Bilanço dün (4 Ağu). Güvenli bölge.
- **SNDK (1427.62 $):** Fiyat < SMA50 (1705) >> SMA200 (855), RSI 44. 1ay -18,2%, 3ay +30,2%. 
  Stop 1100 $ (%+29,8 mesafe). Bilanço BUGÜN (5 Ağu) — sonuç henüz belli değil. Güvenli bölge.
- **ANET (190.51 $):** Fiyat >> SMA50 (168) >> SMA200 (146), RSI 65. 1ay +9,9%, 3ay +10,3%. 
  Stop 160 $ (%+19,1 mesafe). Bilanço dün (4 Ağu). En güçlü görünüm.
- **AVGO (418.16 $):** Fiyat > SMA50 (395) > SMA200 (365), RSI 59. 1ay +11,8%, 3ay +0,3%. 
  Stop 350 $ (%+19,5 mesafe). Bilanço 2 Eylül. Sağlıklı momentum.

**İzleme listesi notları:**
- **NVDA (211.94 $):** Fiyat > 50g > 200g, RSI 50, 1ay +8,4%. Sağlıklı trend — daha yüksek 
  beta için sonraki turlarda değerlendirilebilir.
- **MSFT (492.81 $):** RSI 81 (AŞIRI ALIM), 1ay +27,4%. Tehlikeli bölge — girilmez.
- **PLTR (162.66 $):** RSI 69 (aşırı alım yakın), 1ay +22,7%. Agresif momentum ama çok sıcak.
- **TSM/MRVL:** SMA50'nin altında, dönüş teyidi bekleniyor (ilk planda belirtildiği gibi).
- **VRT (269.93 $):** RSI 39, 3ay -17,8%. Zayıf — izleme listesinden çıkartılabilir.

**Stop kontrolü:** Hiçbir pozisyon stop seviyesinin yakınında değil. En dar mesafe AMD'de 
%+17,9 (stop 440 $, fiyat 518,58 $). Tüm pozisyonlar güvenli bölgede.

### KARAR: İŞLEM YOK

**Gerekçe:** 
1. Portföy daha yeni kuruldu (< 24 saat). Haftalık kontrol döngüsü için çok erken; 
   pozisyonların en az 1 hafta gelişimini görmek disiplinli yaklaşım gerektirir.
2. SNDK bilançosu bugün ama sonuçlar henüz açıklanmadı. Piyasa tepkisini görmeden işlem yapmak 
   varsayım üzerine hareket etmek demektir (tüzüğe aykırı).
3. AMD ve ANET bilançolarının dün olduğu biliniyor ama piyasa henüz açık değil; fiyat etkisi 
   bugünün seansında izlenecek.
4. Stop ihlali yok, hiçbir pozisyon acil müdahale gerektirmiyor.
5. Nakit %10 (10.000 $) — fırsat için yeterli barut var, acele etmeye gerek yok.

**Risk notu:** SNDK bilançosu bugün — volatilite beklenmeli. Pozisyon %15 ağırlıkta ve stop 
%+29,8 mesafede; bilanço olumsuz çıksa bile stop mesafesi rahatsız edici bir düşüşü absorbe eder. 
Ancak bir sonraki kontrolde (haftalık bazda) bilanço etkisi değerlendirilmeli.

**İzleme listesi aksiyonu:**
- **VRT:** 3 ay getirisi negatif, RSI zayıf. Sonraki turda çıkartılmasına karar verilebilir.
- **NVDA:** Sonraki kontrolde daha yüksek beta için portföye ekleme adayı (nakit varsa).

**Sonraki gözden geçirme:** 12 Ağustos 2026 (haftalık tam tur) + SNDK/AMD/ANET bilanço etkilerinin 
değerlendirilmesi.

---

## #3 — 8 Ağustos 2026 · HAFTALIK TUR

**Piyasa bağlamı:** AI altyapı temasında 3 günlük konsolidasyon. Portföy %-4.04 kaybetti 
(SPY'dan %-4.3, SMH'den %-5.3 geride). Yarı iletkenler zayıf seyrediyor, bellek süper döngüsü 
temasında düzeltme derinleşiyor. Makro: belirsizlik yüksek, sektör volatilitesi devam ediyor.

**Teknik durum — Mevcut pozisyonlar (7 Ağustos kapanış):**

- **MU (892.67 → 877.57, %-1.7):** Fiyat < 50g (971) >> 200g yok, RSI 50.9 (nötr). 1ay -10.4%, 
  3ay +17.5%. Stop 730 (%+20.2 mesafe). Bilanço 23 Eylül. Trend zayıflıyor ancak stop güvenli. 
  Haftalık 50g desteği kırıldı — momentum gücünü kaybediyor.

- **AMD (518.58 → 483.36, %-6.8):** Fiyat < 50g (514), RSI 46.9. 1ay -13.4%, 3ay +6.2%. 
  Stop 440 (%+9.9 mesafe) — **EN DAR STOP MESAFESĐ**. Bilanço 3 Kasım. 50g desteği hafifçe kırıldı; 
  bir sonraki haftalık kapanış kritik (Cuma 11 Ağu). Stop ihlali riski yükseliyor.

- **SNDK (1427.62 → 1212.21, %-15.1):** Fiyat << 50g (1688, %-28 altında), RSI 44.3 (zayıf). 
  1ay **%-36.7**, 3ay %-22.4 — **PORTFÖYÜN EN KÖTÜ PERFORMANSI**. Stop 1100 (%+10.2 mesafe). 
  Bilanço 6 Kasım. Momentum tamamen kırık; 50g direncini tamamen kaybetti. NAND döngüsü HBM'den 
  çok daha volatil, düzeltme derinleşmeye devam edebilir. Stop mesafesi dar; bir hafta daha 
  beklemek kayıpları stop seviyesine taşıyabilir.

- **ANET (190.51 → 188.67, %-1.0):** Fiyat > 50g (171) >> 200g yok, RSI 63.1 (güçlü). 1ay +0.9%, 
  3ay +33.1%. Stop 160 (%+17.9 mesafe). Bilanço 3 Kasım. **PORTFÖYÜN EN GÜÇLÜ TEKĐK GÖRÜNÜMÜ** — 
  50g desteğini koruyor, momentum sağlam.

- **AVGO (418.16 → 427.76, %+2.3):** Fiyat > 50g (395) > 200g yok, RSI **73.6 (AŞIRI ALIM)**. 
  1ay +6.9%, 3ay -0.4%. Stop 350 (%+22.2 mesafe). Bilanço 2 Eylül (25 gün sonra). **TEK KAZANAN 
  POZĐSYON** ancak RSI aşırı alım bölgesinde; kısa vadede düzeltme riski var.

**Stop kontrolü:** Hiçbir pozisyon henüz stop ihlali yapmadı. En riskli: AMD (%+9.9) ve 
SNDK (%+10.2). AMD'nin bu Cuma kapanışı (11 Ağustos) kritik seviye — 440$ altına düşerse 
pozisyon tüzük gereği KAPATILIR.

**İzleme listesi öne çıkanlar:**
- **NVDA (223.96):** 50g > fiyat (206), RSI 65.6. 1ay +6.2%, güçlü momentum. Bilanço 26 Ağustos 
  (18 gün sonra — bilanço kuralı sınırında). Değerlendirilebilir ama acele yok.
- **PLTR (172.01):** Fiyat >> 50g (133), RSI 70, 1ay +35.7%. ÇOK SICAK — kovalamama kuralı geçerli.
- **MSFT (499.99):** RSI **81.4 (ÇOK AŞIRI ALIM)**, 1ay +29.8%. Tehlikeli, girilmez.
- **TSM (420.04):** 50g civarında (426), RSI 57.2. Dönüş teyidi bekleniyor (önceki planda belirtildi).
- **VRT (272.40):** 50g altında (301), RSI 44, 1-3ay negatif. Zayıf trend — izleme listesinden 
  çıkartılabilir.

### KARAR 1: SAT — SNDK (Proaktif Zarar Kesimi)

**İşlem:** 10.507 adet SNDK @ 1.212,21 $ → **+12.737 $ nakit**

**Tez (kapanış):** SNDK'nın giriş tezi kırıldı. "AI depolama/NAND cephesi" teması sürse de 
NAND döngüsünün HBM'den çok daha volatil olduğu ve düzeltmenin derinleşebileceği açıkça ortaya 
çıktı. 3 günde %-15 kayıp; son 1 ayda %-36.7 — portföyün en kötü performansı. Fiyat 50g'nin 
%-28 altında; momentum tamamen bozuk, dönüş sinyali yok (RSI 44, zayıf). Stop 1100$ henüz 
ihlal edilmedi ama mesafe sadece %+10.2 — bir hafta daha düşüş devam ederse stop tetiklenecek 
ve kayıp daha da büyüyecek (-%-23 olacak).

**Risk yönetimi prensibi:** Stop disiplini "haftalık kapanışta ihlal varsa kapat" der ama bu 
tezin bozulması halinde **proaktif çıkışı** engellemez. SNDK tezi açıkça kırık; stop ihlalini 
beklemek kayıpları mekanik olarak büyütür. Daha güçlü fırsatlar için nakit yaratmak disiplinli 
hamle. Agresif hedefin (3-5x) sağlıklı risk yönetimi gerektirdiği ilk portföy kurulumunda 
belirtilmişti — bu o disiplinin ilk uygulaması.

**Zarar:** -2.263 $ (%-15.1). **Yeni portföy ağırlıkları:** MU %30.7, AMD %19.4, ANET %15.5, 
AVGO %10.7, NAKİT %22.7 (22.737 $).

**Riskler:** Eğer SNDK buradan dönerse (örn. NAND talebi patlarsa) erken satmış oluruz. Ancak 
mevcut teknik ve momentum hiçbir dönüş sinyali göstermiyor; en ihtimalli senaryo düşüşün 
devamı. Zararı sınırlamak, daha iyi asimetri yakalamaktan öncelikli.

### KARAR 2: TUT — MU, AMD, ANET, AVGO

**MU:** Trend zayıfladı (50g altında) ama stop mesafesi (%+20.2) rahat. 23 Eylül bilançosuna 
kadar fiyat aksiyonunu izle; stop ihlali yoksa tut. Tez hala geçerli (bellek süper döngüsü), 
sadece zamanlama erken olmuş olabilir.

**AMD:** **KRİTİK SEVĐYE** — stop 440 $, mesafe %+9.9. Bu Cuma kapanışı (11 Ağustos) 440 altındaysa 
**KAPATILACAK** (tüzük gereği). Eğer 440 üzerinde kalırsa tut; AI hızlandırıcı tezi sağlam, 
sadece sektör konsolidasyonu. Bir sonraki kontrolde (12 Ağustos veya hafta başı) stop ihlali 
olup olmadığı değerlendirilecek.

**ANET:** Portföyün en sağlıklı pozisyonu. 50g desteğini koruyor, momentum güçlü (RSI 63). 
Minimal kayıpla (%-1) güç gösterisi yapıyor. Tut.

**AVGO:** RSI 73.6 aşırı alım bölgesinde ve bilanço 25 gün sonra. Düzeltme riski var ancak 
henüz stop tehlikesi yok (%+22.2 mesafe) ve tez bozulmadı (özel AI çipleri + ağ). Tüzük 
"ikiye katlanan pozisyonda maliyetin bir kısmı çıkarılabilir" diyor — AVGO henüz %+2.3, iki 
katına gelmedi. Kârı realize etmek ihtiyari; şimdilik **tut**, bilanço öncesinde (Ağustos sonu) 
tekrar değerlendir.

### KARAR 3: YENİ POZĐSYON YOK

**Nakit:** 22.737 $ (%22.7 portföy). Tüzük %0-30 nakit serbest bırakıyor — mevcut seviye sınırda 
ama yasal.

**Neden yeni pozisyon yok?**
1. **NVDA:** Güçlü (fiyat > 50g, RSI 65.6, 1ay +6.2%) ama bilanço 26 Ağustos (18 gün sonra). 
   Tüzük: "Bilançoya 1 haftadan az kala yeni tam pozisyon açılmaz" — yani 19 Ağustos'tan 
   sonra girilmez. Şimdi girilebilir ama acele yok; önce mevcut pozisyonların stop durumunu 
   (AMD) netleştirmek daha disiplinli.

2. **PLTR:** ÇOK SICAK (RSI 70, 1ay +35.7%). Kovalamama kuralı hala geçerli.

3. **MSFT:** Aşırı alım (RSI 81.4). Düzeltme beklenmeli.

4. **TSM/MRVL:** 50g civarında/altında, dönüş teyidi bekleniyor. Henüz net sinyal yok.

5. **VRT:** Zayıf momentum (1-3ay negatif). İzleme listesinden çıkarılabilir.

**Strateji:** Nakit barut olarak korunacak. AMD'nin Cuma stop kontrolü sonrası (11 Ağustos) 
daha net resim olacak. Eğer AMD kapanırsa nakit ~%42'ye çıkar; eğer tutarsa mevcut %22.7 nakit 
ile daha sağlam giriş fırsatı beklenecek (örn. TSM'de dönüş, NVDA'da pull-back, ya da yeni 
tarama). Acele etmek yerine disiplinli bekleme.

### PORTFÖY KARAKTERĐ (SNDK Sonrası)

**Pozisyonlar:** 4 hisse (MU, AMD, ANET, AVGO) — hepsi AI altyapı teması.  
**Nakit:** %22.7 (22.737 $)  
**Risk profili:** SNDK kesimi ile en volatil ayak çıkarıldı; portföy biraz daha dengeli ama 
hala agresif (tema konsantrasyonu devam ediyor). AMD'nin stop riski en büyük belirsizlik.

**Performans (başlangıçtan beri):** %-4.04 (SNDK zararıyla birlikte). SPY %-4.3, SMH %-5.3 
geride. Kötü başlangıç ama henüz 3 gün geçti — uzun vadeli disiplinin test edildiği dönem.

**En büyük dersler şimdiye kadar:**
1. NAND HBM'den çok daha volatil — SNDK'nın stop mesafesinin (+%-30) bile yetmediği ortaya çıktı.
2. Düzeltme sonrası "tepki günü" girişleri (5 Ağustos) henüz erken olmuş olabilir — konsolidasyon 
   devam etti.
3. Stop disiplinini beklemek yerine **tez bozukluğunda proaktif çıkış** da disiplinin parçası.

**Sonraki gözden geçirme:** 11 Ağustos Cuma (AMD stop kontrolü — kritik!) ve 12 Ağustos 
(haftalık tam tur). Eğer AMD kapanırsa nakit artışıyla yeni pozisyon stratejisi belirlenecek.

---

## #4 — 15 Ağustos 2026 · HAFTALIK TUR

**Piyasa bağlamı:** Yarı iletkenler toparlanma trendine girdi. Risk iştahı arttı, AI altyapı 
teması yeniden güçlenmeye başladı. Portföy %+0.28 kazandı (SPY'dan %-0.37, SMH'den %-1.82 
geride). 10 günlük konsolidasyon sonrası momentum MU ve AMD'de geri geldi.

### A. Veri durumu

12/12 sembol için veri eksiksiz çekildi. Tüm pozisyonlarda fiyat, 50/200g SMA, RSI, getiri 
verileri ve bilanço tarihleri mevcut. Eksik alan yok.

**Haber taraması:** 12 sembol için 5'er başlık tarandı (toplam 60 başlık). Dikkate değer:
- **MU:** "Micron Stock Edges Back Toward $1,000. How Far It Could Go." — Bellek süper döngüsü 
  ivme kazanıyor, analist hedefleri yükseliyor.
- **SNDK:** "Sandisk stock surges as Wall Street cheers flash memory maker's bullish outlook" + 
  "SanDisk CEO reveals what's next after explosive 3,150% stock rally" — CEO'nun iyimser 
  açıklamaları NAND talebindeki toparlanmayı teyit etti. **Kritik not:** SNDK'yı 8 Ağustos'ta 
  1212.21 $'dan sattık, şimdi 1641.11 $ (+%35.4). Erken satış oldu.
- **AVGO:** "AI Infrastructure Stocks: Billions of Reasons to Stay Bullish" ama hisse zayıflıyor 
  (%-8.1 haftalık). Sektör geneli yükselirken AVGO konsolidasyon yapıyor.
- **Druckenmiller haber:** AMD ve Amazon pozisyonlarını artırdı, bazı yarı iletkenleri azalttı 
  (hedge fon akışı AI hızlandırıcılara kayıyor).

### B. Hareketin sebebi

**MU (892.67 → 971.66, +%10.7):** Bellek süper döngüsü ivmesi. Analist notları 1.000 $ 
seviyesine yaklaşımı destekliyor; HBM talebi güçlü. Risk iştahı artışı ile yarı iletkenler 
genelinde toparlanma dalgası — MU momentum lideri. Sektör rotasyonu (MSFT/GOOGL gibi mega-cap'ler 
konsolide ederken yarı iletkenler tepki gösteriyor).

**SNDK (1212.21 → 1641.11, +%35.4):** CEO'nun iyimser rehberlik açıklamaları. NAND talebinde 
toparlanma — SNDK'nın 3.150% yıllık ralli hikayesi Wall Street tarafından yeniden fiyatlanıyor. 
8 Ağustos'ta "momentum kırık, 50g'nin %-28 altında, tez bozuk" diyerek sattık — **fakat NAND 
döngüsü tahmin edilenden çok daha hızlı döndü, teknik toparlanma tetiklendi.** Bu, NAND'ın HBM'den 
daha volatil olduğunu doğruladı ama bu sefer oynaklık lehimize değil aleyhimize işledi.

### C. Tez sağlık kontrolü

**MU (971.66 $) — Bellek süper döngüsü / HBM liderliği → GEÇERLİ**  
50g'yi (960.65) geri kazandı, fiyat > 50g > 200g (552.44). Momentum güçleniyor (RSI 56.3, 
1ay +14.5%, 3ay +34.1%). Geçen tur "50g altında, trend zayıflıyor" denmişti — bu tur trendin 
geri döndüğünü görüyoruz. Bilanço 23 Eylül (39 gün sonra). Stop 730 $ (%+33.1 mesafe, çok rahat).

**AMD (514.39 $) — AI hızlandırıcı / NVDA alternatifi → GEÇERLİ**  
50g'yi (510.4) geri kazandı, stop krizi atlatıldı. Geçen tur "Cuma 440 altındaysa kapatılacak, 
en kritik seviye" denmişti — 440 üzerinde kaldı, pozisyon kurtuldu. Fiyat > 50g > 200g (324.33), 
momentum stabil (RSI 53.7, 1ay +3.8%, 3ay +21.3%). Druckenmiller'ın AMD pozisyonunu artırması 
(13F dosyası) tezi destekliyor. Stop 440 $ (%+16.9 mesafe, güvenli bölgeye döndü).

**ANET (198.82 $) — AI veri merkezi ağ donanımı lideri → GEÇERLİ**  
Portföyün en istikrarlı performansı. Fiyat >> 50g (173.89) >> 200g (148.26), momentum güçlü 
(RSI 59.7, 1ay +17.9%, 3ay +40.0%). 52 hafta zirvesini geçip kontrol etti, bull trap riski 
gerçekleşmedi. Stop 160 $ (%+24.3 mesafe).

**AVGO (392.99 $) — Özel AI çipleri / ağ cephesi → ZAYIFLIYOR**  
Geçen tur tek kazanan pozisyondu (%+2.3, RSI 73.6 aşırı alım). Bu tur %-6.0 düştü, RSI 46.5'e 
geriledi (aşırı alımdan normale döndü ama momentum kaybı var). 1 hafta %-8.1, 3 ay %-7.4 — 
sektör geneli yükselirken AVGO konsolidasyon yapıyor. Fiyat 50g'nin (390.33) hemen üzerinde 
(+2.66 $, çok ince). Bilanço 2 Eylül (18 gün sonra — bilanço kuralı sınırında). Stop 350 $ 
(%+12.3 mesafe, henüz tehlike yok). **Tez henüz bozulmadı ama momentum zayıfladı; bir sonraki 
turda 50g'yi kaybederse veya stop %+10'un altına inerse tekrar değerlendirilebilir.**

### D. Kararlar

#### KARAR 1: TUT — Tüm pozisyonlar (MU, AMD, ANET, AVGO)

**Tez:** Tüm pozisyonlar stop seviyelerinin çok üzerinde ve temel tezler geçerli. MU ve AMD 
50g'yi geri kazandı (güçlenme sinyali), ANET momentum lideri, AVGO zayıflıyor ama henüz stop 
riski yok. AI altyapı teması toparlanma trendinde — konsolidasyon bitmiş görünüyor.

**Risk:** AVGO'nun momentum kaybı devam ederse 50g'yi (390.33) kaybedebilir. Bilanço 18 gün 
sonra — volatilite artabilir. Ancak stop mesafesi (%+12.3) şimdilik rahat.

**Çıkış planı:** Stop seviyeleri aynen korunuyor (MU 730, AMD 440, ANET 160, AVGO 350). Haftalık 
kapanış bu seviyelerin altındaysa mekanik satış. AVGO'nun 50g'yi (390.33) kaybedip kaybetmediği 
bir sonraki turda izlenecek — kaybederse pozisyon kırpma değerlendirilebilir.

**Tezin yanlış olduğunu gösterecek işaret:**  
- MU: Bilanço öncesinde (23 Eylül) 50g'yi tekrar kaybeder ve stop'a yaklaşırsa (800'ün altı).  
- AMD: 50g'yi (510) kaybeder ve 3 gün üst üste altında kalırsa — NVDA'ya karşı pazar payı kaybı 
  sinyali olabilir.  
- ANET: Momentum kırılır, 50g'yi (173.89) kaybeder — bu durumda zirve kırılımı sahte çıkmış 
  (bull trap) demektir.  
- AVGO: Stop mesafesi %+10'un altına inerse (370 $ civarı) veya bilanço öncesinde (2 Eylül) 
  50g'yi kaybederse.

#### KARAR 2: YENİ POZĐSYON YOK

**Nakit:** 22.737 $ (%22.7 portföy). Tüzük nakit oranına sınır koymadı — mevcut seviye disiplinli.

**Neden yeni pozisyon yok?**

1. **NVDA (225.16 $):** Güçlü görünüm (fiyat > 50g > 200g, RSI 63, 1ay +11%, bilanço 26 Ağustos). 
   **ANCAK:** Bilanço 11 gün sonra. Geçen turda (#3) şu not düşülmüştü: *"Tüzük: 'Bilançoya 1 
   haftadan az kala yeni tam pozisyon açılmaz' — yani 19 Ağustos'tan sonra girilmez."* Şimdi 
   15 Ağustos — 4 gün sonra (19 Ağustos'ta) bilanço penceresi kapanıyor. **NVDA girişi için son 
   3-4 gün var ama acele etmek doğru değil.** AMD ve MU'nun momentum toparlandığını gördük; bir 
   tur daha bekleyip düzeltme fırsatı yakalamak veya bilanço sonrası netlik beklemek daha sağlıklı.

2. **TSM (426.35 $):** 50g civarında (425.06, +1.29 $). Geçen tur "dönüş teyidi bekleniyor" 
   denmişti. 50g'ye çok ince bir kırılım var ama net değil (RSI 54.3, nötr). Bir tur daha bekleme 
   — 50g'nin üzerinde 2-3 gün kapanış görürsek dönüş teyit olur.

3. **MRVL (222.02 $):** Hala 50g'nin (238.07) altında (%-6.7). Dönüş sinyali yok. Bilanço 27 
   Ağustos (12 gün sonra) — bilanço kuralı sınırında. Atlama.

4. **PLTR (174.04 $):** Hala çok sıcak (RSI 68.1, 1ay +31.5%). Kovalamama kuralı geçerli.

5. **VRT (293.84 $):** 50g civarında (296.74, %-1 altında). 3 ay %-20.8 — zayıf trend. İzleme 
   listesinden çıkarılabilir.

**Strateji:** Nakit barut olarak korunuyor. Mevcut 4 pozisyon sağlam, acele ekleme gerekmiyor. 
Bir sonraki tur (22 Ağustos): NVDA bilançosu geçmiş olacak (26 Ağustos), TSM'de dönüş teyidi 
netleşecek. Şimdi sabırlı bekleme zamanı.

### E. Tema riski

**Portföy:** 4 pozisyon (MU, AMD, ANET, AVGO) — hepsi AI altyapı teması. %100 konsantrasyon.  
**Nakit:** %22.7 — tema kırılırsa tampon.

**Aynı anda düşme riski:** AI harcama döngüsü kırılırsa (örn. mega-cap'ler capex kıssalar, AI 
yatırım balonunun patlaması sinyali) tüm pozisyonlar birlikte düşer. Bu risk başlangıçta 
bilinçli kabul edildi — agresif hedefin (3-5x) bedeli. Ancak şu an tema güçlenmeye başladı; 
risk seviyesi geçen turdan daha düşük.

**Nakit yeterli mi?** %22.7 nakit, %-30 bir tema düzeltmesinde (77.282 $ portföy × 0.3 = 23.184 $ 
yastık) pozisyonları korumaya YETERLİ. Stop seviyeleri tema kırılımında tetiklenmeden önce nakit 
tamponu devreye girer. Mevcut nakit seviyesi disiplinli.

**Çeşitlendirme değerlendirmesi:** Tema riski düşürmek için AI altyapı dışında pozisyon 
açılabilir (örn. mega-cap'ler MSFT/GOOGL), ancak bu beta'yı düşürür ve 3-5x hedefine katkı 
azalır. Tüzük buna izin veriyor ama şimdilik mevcut strateji korunuyor — tema güçlenme trendinde.

### F. Hesap verme

**1. Geçen tur ne söylemiştim, bu tur ne yaptım?**

**Geçen tur (#3, 8 Ağustos):**
- **AMD:** "Cuma (11 Ağustos) 440 altındaysa KAPATILACAK (tüzük gereği)" → AMD 440 üzerinde 
  kaldı, pozisyon tutuldu, 50g'yi geri kazandı. **Sapma yok — söylediğim gibi oldu.**
- **MU, ANET, AVGO:** TUT dedim → Tuttum. **Sapma yok.**
- **YENİ POZĐSYON YOK:** "NVDA değerlendirilebilir ama acele yok, AMD stop dirumunu netleştirmek 
  önce" dedim → Yeni pozisyon açmadım. **Sapma yok.**
- **SNDK:** 1212.21 $'dan sattım, "tez bozuk, momentum kırık, stop mesafesi dar (+%10.2), 
  proaktif zarar kesimi" → **SNDK şimdi 1641.11 $ (+%35.4).**

**SAPMA VAR — SNDK erken satışı:**  
SNDK'yı "tez bozuk, NAND döngüsü HBM'den çok daha volatil, düzeltme derinleşebilir" diyerek 
sattım. Tez bozukluğu gerekçesi doğruydu (50g'nin %-28 altında, momentum kırık, 1ay %-36.7). 
ANCAK NAND döngüsü tahmin edilenden **çok daha hızlı döndü** — CEO'nun iyimser açıklamaları 
ve Wall Street desteği ile SNDK 1 haftada +%35.4 yaptı. **Yanıldığım yer:** NAND'ın döngü 
hızını hafife aldım. "Stop mesafesi dar (+%10.2), bir hafta daha beklemek kayıpları büyütür" 
diye erken çıktım — fakat piyasa dönüşü stop tetiklenmeden geldi.

**Sonradan gerekçeye uydurmuyorum:** Satış kararı o gün için doğru verilerle alınmıştı 
(momentum kırık, 50g çok altında, stop dar). Ancak NAND'ın volatilitesi iki yönlü — düşüşte 
hızlı ama toparlanmada da hızlı. Bu dersi öğrendim: yüksek volatilite olan döngüsel 
pozizyonlarda stop mesafesi daha geniş tutulmalı veya teknik dönüş sinyali (örn. 50g'ye geri 
dönüş) beklenebilir. %-15 kayıpta proaktif çıkış yapacaksam, bir sonraki kontrolde tekrar 
giriş fırsatı için sembolü izleme listesinde tutmalıydım — SNDK'yı listeden çıkarmadım ama 
aktif takip etmedim.

**2. Geçen turdaki tezin yanlış çıktığı yer:**

SNDK tezi: "NAND döngüsü HBM'den çok daha volatil, düzeltme derinleşebilir." → EVET volatil 
ama YUKARİ yönde de çok hızlı döndü. Tezin eksik yanı: NAND döngüsünün **dönüş hızını** 
hesaba katmadım. Şirket fundamentali (CEO rehberliği) hızlı değişebildiği için teknik 
toparlanma stop tetiklenmeden gelebilir. **Dersi sonraki turlara taşıyorum.**

**3. Bu turda verdiğim kararın beni yanıltabileceği yer:**

**NVDA'ya girmeme kararı:** "4 gün sonra bilanço penceresi kapanıyor ama acele etmiyorum, 
bir tur daha bekleyeceğim" dedim. Eğer NVDA bilançosu çok güçlü çıkar ve hisse +%20 yaparsa, 
pencereyi kaçırmış olacağım. Ancak bilanço riski iki yönlü — olumsuz çıkarsa mevcut 
pozisyonları korumak daha doğru olacak. **Risk kabul ediyorum: NVDA'nın bilançosunu 
beklemek, fırsatı kaçırmak demek olabilir. Ama disiplin bunu gerektiriyor — acele giriş 
yerine netlik beklemek.**

**AVGO'yu tutma kararı:** "Zayıflıyor ama henüz stop riski yok" dedim. Eğer AVGO 50g'yi 
(390.33) kaybeder ve bilanço öncesinde stop'a yaklaşırsa (360'ın altı), kırpmayı geç kalmış 
olacağım. Bir sonraki turda 50g'yi kaybetmişse pozisyon kırpma değerlendireceğim — ama şimdilik 
tutmak disiplinli.

**Sonraki gözden geçirme:** 22 Ağustos 2026 (Cumartesi — bir sonraki haftalık tur). AVGO'nun 
50g durumu, NVDA bilançosu sonrası (26 Ağustos) piyasa tepkisi, TSM'de dönüş teyidi izlenecek.

---

## #5 — 22 Ağustos 2026 · HAFTALIK TUR

**Piyasa bağlamı:** Yarı iletkenler haftalık bazda konsolidasyon. Portföy %-2.86 (SPY %-0.73, 
SMH %-2.66). AI altyapı teması dalgalı seyirde; mega-cap'ler (MSFT/GOOGL) istikrarlı, yarı 
iletkenler düzeltme yapıyor.

### A. Veri durumu

12/12 sembol için veri eksiksiz çekildi (22 Ağustos 2026 kapanış bazlı). Tüm pozisyonlarda 
fiyat, 50/200g SMA, RSI, getiri ve bilanço tarihleri mevcut. Eksik alan yok.

**Haber taraması:** 12 sembol için toplam 60 başlık tarandı. Dikkate değer:

- **MU:** "Micron's AI boom rolls on with $10 billion Iowa data center" — 10 yıllık 10 mlr $ 
  AR-GE yatırımı açıklandı (2027'de başlıyor). "Micron Fell 7%. Is This an Opportunity to Buy?" — 
  haftalık düzeltme sonrası fırsat yazıları. Bellek süper döngüsü teması sürüyor.

- **AMD:** "AMD Investors Must Be Ready For Major News On Aug. 26" — yaklaşan NVDA bilançosu 
  AI hızlandırıcı sektörü için test olacak. "The Best Semiconductor Stock to Buy Isn't AMD or 
  Qualcomm: It's Nvidia" — rekabet baskısı söylemi devam ediyor.

- **AVGO:** "Broadcom Is Down 6.2% After Google Expands AI Chip Ties With Marvell" — Google'ın 
  MRVL ile ortaklığı genişletmesi AVGO'ya olumsuz yansıdı (özel AI çipi rekabeti). Hisse zayıflıyor.

- **MRVL:** "Google Is Getting Paid in Marvell Stock Warrants for Buying Marvell's Chips" — 
  Google ortaklığı güçleniyor, hisse +6.8% haftalık. 50g'yi kırdı.

- **SNDK:** "SanDisk Makes a Quiet Move Into AI's Next Boom" — NAND'dan AI depolamaya genişleme 
  hikayesi. Hisse 1596.08 $ (8 Ağustos'ta 1212.21 $'dan sattık, +%31.7 kazanç kaçırdık).

### B. Hareketin sebebi

Hiçbir pozisyon haftalık bazda ±%10'u geçmedi. Ancak AVGO'nun 1 haftalık %-6.2 performansı 
(portföydeki en kötü) ve 50g'yi kaybetmesi kritik:

**AVGO (418.16 → 368.45, portföy bazında %-11.9 toplam):** Google-MRVL ortaklığının genişlemesi, 
özel AI çipi pazarında rekabetin arttığı sinyali. AVGO "AI XPU" teması için tercih edilen 
tedarikçi konumunu MRVL'e kaptırma riski. Stop mesafesi daraldı (%+12.3 → %+5.3), bilanço 11 gün 
sonra (2 Eylül). ***Geçen tur (#4, 15 Ağustos) şöyle denilmişti:*** *"AVGO → ZAYIFLIYOR... Tez 
henüz bozulmadı ama momentum zayıfladı; bir sonraki turda 50g'yi kaybederse veya stop %+10'un 
altına inerse tekrar değerlendirilebilir."* → Her iki koşul da gerçekleşti.

### C. Tez sağlık kontrolü

**MU (966.78 $) — Bellek süper döngüsü / HBM liderliği → GEÇERLİ**  
Fiyat > 50g (964.54, +2.24) > 200g (570.95), RSI 54.3 (sağlıklı). 1 hafta %-0.5, 1 ay +5.0%, 
3 ay +28.8%. Stop 730 $ (%+32.4 mesafe, çok rahat). Bilanço 23 Eylül (32 gün sonra). 10 mlr $ 
AR-GE yatırımı açıklaması tezi destekliyor. 50g desteğini koruyor, momentum stabil.

**AMD (473.25 $) — AI hızlandırıcı / NVDA alternatifi → ZAYIFLIYOR**  
Fiyat < 50g (510.23, -36.98 / %-7.25), > 200g (329.86). RSI 45.8 (zayıf). 1 hafta %-8.0, 
1 ay %-9.3%, 3 ay +1.2%. Stop 440 $ (%+7.6 mesafe — DAR!). Bilanço 3 Kasım (73 gün sonra). 
Geçen tur 50g'yi geri kazanmıştı (514.39), bu tur tekrar kaybetti. NVDA bilançosu 26 Ağustos — 
eğer NVDA rehberliği çok güçlü çıkarsa AMD'ye rekabet baskısı artar. ***Tez henüz bozulmadı ama 
50g kaybı momentum zayıflığı sinyali. Stop mesafesi dar; bir sonraki tur kritik.***

**ANET (188.65 $) — AI veri merkezi ağ donanımı lideri → GEÇERLİ**  
Fiyat > 50g (177.36, +11.29) >> 200g (149.06). RSI 51.7 (nötr). 1 hafta %-5.1, 1 ay +8.4%, 
3 ay +22.5%. Stop 160 $ (%+17.9 mesafe). Bilanço 3 Kasım. Haftalık düzeltmeye rağmen 50g desteğini 
koruyor. Portföyün en istikrarlı pozisyonu.

**AVGO (368.45 $) — Özel AI çipleri / ağ cephesi → BOZULDU**  
Fiyat < 50g (388.43, -19.98 / %-5.14), ≈ 200g (368.3, +0.15). RSI 38.7 (zayıf). 1 hafta %-6.2, 
1 ay %-3.5%, 3 ay %-10.9%. Stop 350 $ (%+5.3 mesafe — ÇOK DAR!). Bilanço 2 Eylül (11 gün sonra). 
***Geçen tur uyarısı: "50g'yi kaybederse veya stop %+10'un altına inerse değerlendir" — Her iki 
koşul da gerçekleşti.*** Google-MRVL ortaklığı AVGO'nun özel AI çipi temasını zayıflattı. Momentum 
kırık, bilanço öncesinde volatilite riski yüksek. Tez bozuldu.

### D. Kararlar

#### KARAR 1: KIRP — AVGO (Pozisyon Yarıya İndirildi)

**İşlem:** 11.96 adet AVGO @ 368.45 $ SAT → **+4.406 $ nakit** (yarım pozisyon kaldı: 11.96 adet)

**Tez (kırpma gerekçesi):** Geçen tur (#4) açıkça uyarılmıştı: *"50g'yi kaybederse veya 
stop %+10'un altına inerse tekrar değerlendirilebilir."* Her iki koşul da gerçekleşti:
- 50g'yi kaybetti (388.43 → fiyat 368.45, %-5.14 altında)
- Stop mesafesi %+5.3'e daraldı (%+10'un çok altında)

**Risk yönetimi prensibi:** Tez bozuldu ama pozisyonu tamamen kapatmak yerine yarıya indiriyorum:
1. **Olumsuz senaryo ağırlığı yüksek:** Google-MRVL ortaklığı AVGO'nun özel AI çipi pazarındaki 
   konumunu tehdit ediyor. Bilanço 11 gün sonra; eğer rehberlik zayıfsa stop tetiklenebilir. 
   Tam kapat yerine kırparak maruziyeti düşürüyorum.
2. **Olumlu senaryo hala mümkün:** AVGO 200g desteğinde (368.45 vs 368.3). Bilanço güçlü çıkıp 
   50g'yi geri kazanabilir. Yarısını tutarak bu ihtimali koruyorum.
3. **Disiplin:** Geçen tur uyarı verildi, koşullar gerçekleşti, harekete geçildi. Sessiz sapma yok.

**Pozisyon güncelleme:**
- Önceki: 23.9143 adet @ 418.16 $ maliyet (10.000 $ giriş)
- Satılan: 11.96 adet @ 368.45 $ (4.406 $ nakit)
- Kalan: 11.95 adet @ 418.16 $ maliyet (5.000 $ giriş maliyeti)
- **Yeni ağırlık:** ~%5 (önceki %9.1'den yarıya indi)

**Zarar:** Satılan 11.96 adet için: (368.45 - 418.16) × 11.96 ≈ -594 $ (%-11.9 kayıp, yarım 
pozisyon için). Kalan 11.95 adetin maliyeti yine 418.16 $ — stop 350 $ korunuyor (%+5.3 mesafe).

**Çıkış planı (kalan yarı pozisyon için):** Stop 350 $ aynen — haftalık kapanış altındaysa 
tamamen kapat. Bilanço 2 Eylül — eğer 50g'yi (388.43) geri kazanamazsa ve stop'a yaklaşırsa 
(360'ın altı) bilanço öncesinde kapatmayı değerlendir. Eğer 50g'yi geri kazanır ve bilanço güçlü 
çıkarsa pozisyon geri büyütülebilir.

**Tezin yanlış olduğunu gösterecek işaret:** Bilanço (2 Eylül) rehberliği zayıfsa ve stop 350'ye 
yaklaşırsa — tam kapatma. Eğer bilanço güçlü çıkar, 50g'yi geri kazanır ve RSI 50'nin üzerine 
çıkarsa — tez onarılabilir, pozisyon geri büyütülebilir.

#### KARAR 2: TUT — MU, ANET

**MU:** Tez geçerli, 50g üzerinde, stop mesafesi çok rahat (%+32.4). 10 mlr $ AR-GE yatırımı 
açıklaması bellek temasını destekliyor. Bilanço 32 gün sonra (23 Eylül) — pozisyon taşımak 
disiplinli. Stop 730 $ korunuyor.

**ANET:** En istikrarlı pozisyon. 50g desteğini koruyor, momentum sağlam. Haftalık %-5.1 düzeltme 
normal volatilite aralığında. Stop 160 $ korunuyor (%+17.9 mesafe).

**Çıkış planı:** Stop seviyeleri aynen (MU 730, ANET 160). Haftalık kapanış altındaysa mekanik satış.

**Tezin yanlış olduğunu gösterecek işaret:**  
- MU: Bilanço öncesinde (23 Eylül) 50g'yi kaybeder ve stop'a yaklaşırsa (800'ün altı).  
- ANET: 50g'yi (177.36) kaybeder ve 3 gün üst üste altında kalırsa — momentum kırılma sinyali.

#### KARAR 3: İZLE — AMD (Bir Tur Daha Bekleme)

**AMD:** 50g'yi kaybetti (510.23 → fiyat 473.25, %-7.25 altında) ve stop mesafesi dar (%+7.6). 
***Ancak henüz stop ihlali yok ve NVDA bilançosu 26 Ağustos'ta gelecek — bu, AI hızlandırıcı 
sektörü için kritik test.***

**Karar:** Bir tur daha izle. NVDA bilançosu sonrası (26 Ağustos) AMD'nin nasıl tepki vereceğini 
gör. Eğer NVDA rehberliği çok güçlü çıkar ve AMD stop'a yaklaşırsa (450'nin altı), ara tur 
değerlendirmesi yapılabilir. Eğer AMD stop'u korursa 29 Ağustos'taki bir sonraki tura kadar tut.

**Risk:** Stop mesafesi dar (%+7.6). Eğer AMD haftalık bazda %-7 daha düşerse (≈440 $) stop 
tetiklenir. NVDA bilançosu olumsuz çıkar ve sektör satışı olursa AMD de çekilebilir.

**Neden şimdi kırpmıyorum:** AVGO'yu kırptım çünkü geçen tur uyarı verilmişti ve her iki koşul 
gerçekleşti. AMD için uyarı yoktu; 50g kaybı bu tur ortaya çıktı. Disiplin: aynı turda iki 
pozisyonu birden kırpmak portföyü aşırı nakde iter (%27.5 nakit olur). AMD'ye bir tur daha bekleme 
hakkı tanıyorum — ama stop kesin.

**Çıkış planı:** Stop 440 $ — haftalık kapanış altındaysa kapat. NVDA bilançosu sonrası (26 Ağustos) 
eğer AMD 450'nin altına düşerse ara değerlendirme.

**Tezin yanlış olduğunu gösterecek işaret:** NVDA bilançosu çok güçlü çıkar, rehberlik AI 
hızlandırıcı pazarının NVDA'da yoğunlaştığını gösterirse — AMD'nin "NVDA alternatifi" tezi zayıflar.

#### KARAR 4: YENİ POZĐSYON YOK

**Nakit:** AVGO kırpımı sonrası 22.737 + 4.406 = **27.143 $ (%27.5 portföy)**.

**Neden yeni pozisyon yok?**

1. **NVDA (214.72 $):** Bilanço 26 Ağustos (4 gün sonra). ***Geçen tur (#4, 15 Ağustos) şöyle 
   denilmişti:*** *"Bilanço 11 gün sonra... 19 Ağustos'tan sonra girilmez."* → Bilanço penceresi 
   19 Ağustos'ta kapandı. Şimdi 22 Ağustos — artık girilmez (bilanço kuralı). Bilanço sonrası 
   (29 Ağustos'taki bir sonraki turda) değerlendirilebilir.

2. **MRVL (237.04 $):** 50g'yi kırdı (233.82 → fiyat 237.04, +%1.38 üzerinde), güçlü momentum 
   (1 hafta +6.8%, 1 ay +22.0%, RSI 55.8). Google ortaklığı haberleri pozitif. ***Ancak bilanço 
   27 Ağustos (5 gün sonra).*** Bilanço kuralı: "1 haftadan az kala yeni tam pozisyon açılmaz" — 
   5 gün sınırda. Bilanço sonrası (29 Ağustos'taki bir sonraki turda) değerlendirilebilir. 
   Acele giriş yapmak yerine bilançoyu beklemek daha disiplinli.

3. **TSM (418.95 $):** Hala 50g altında (424.52, %-1.31 altında). Geçen tur "dönüş teyidi 
   bekleniyor" denilmişti — henüz net sinyal yok. RSI 50.4 (nötr), 1 hafta %-1.7. Bir tur daha bekleme.

4. **PLTR (179.94 $):** RSI 69.4 (aşırı alım yakın), 1 ay +46.4%. Hala çok sıcak. Kovalamama 
   kuralı geçerli.

5. **VRT (261.95 $):** 50g çok altında (293.89, %-10.86 altında), RSI 42.2 (zayıf), 1 hafta 
   %-10.9, 3 ay %-20.0. Momentum kırık — izleme listesinden çıkarılabilir.

**Strateji:** Nakit %27.5'e yükseldi. NVDA ve MRVL bilançoları 26-27 Ağustos'ta — sonraki turda 
(29 Ağustos) her ikisi de netleşmiş olacak. AMD'nin NVDA bilançosu sonrası tepkisi izlenecek. 
Şimdi sabırlı bekleme zamanı — acele giriş yerine netlik beklemek.

### E. Tema riski

**Portföy:** 3.5 pozisyon (MU %33.4, AMD %18.8, ANET %15.3, AVGO %5 — yarım pozisyon) — hepsi 
AI altyapı teması. %72.5 yatırımda, %27.5 nakit.

**Aynı anda düşme riski:** AI harcama döngüsü kırılırsa (örn. NVDA bilançosu çok zayıf çıkar, 
mega-cap'ler capex kıssalar) tüm pozisyonlar birlikte düşer. Bu risk başlangıçta bilinçli kabul 
edildi. ***Ancak bu tur AVGO'yu kırparak tema konsantrasyonunu azalttım — özel AI çipi cephesinden 
kısmen çıktım, maruziyeti düşürdüm.***

**Nakit: koruma yastığı DEĞİL, alım gücü.** %27.5 nakit portföyü korumaz (kaldıraçsız sanal 
portföy); düşüşte kullanılacak barut. ***Ne için bekliyorum:*** (1) NVDA bilançosu sonrası sektör 
tepkisi — eğer AI hızlandırıcılar sert düşerse AMD veya TSM'de giriş fırsatı. (2) MRVL bilançosu 
sonrası — eğer Google ortaklığı teyit edilirse ve 50g üzerinde kalırsa yeni pozisyon. (3) Mevcut 
pozisyonlarda (MU/ANET) düzeltme varsa ekleme. Nakit pasif tutulmayacak; fırsat bekliyor.

**Çeşitlendirme:** AI altyapı dışında pozisyon açmak tema riskini düşürür ama beta'yı da düşürür 
(3-5x hedefine katkı azalır). Tüzük buna izin veriyor ama şimdilik AI teması ana strateji. 
Nakit artışı zaten tema riskini bir miktar dengeledi.

### F. Hesap verme

**1. Geçen tur ne söylemiştim, bu tur ne yaptım?**

**Geçen tur (#4, 15 Ağustos):**
- **MU, AMD, ANET, AVGO TUT:** Tuttum — ama AVGO'yu yarıya indirdim. **SAPMA VAR (açıklama aşağıda).**
- **YENİ POZĐSYON YOK:** "NVDA değerlendirilebilir ama acele yok" → Yeni pozisyon açmadım. **Sapma yok.**
- **AVGO uyarısı:** *"AVGO → ZAYIFLIYOR... bir sonraki turda 50g'yi kaybederse veya stop %+10'un 
  altına inerse tekrar değerlendirilebilir."* → Her iki koşul gerçekleşti, pozisyon kırptım. 
  **Sapma yok — söylediğim gibi oldu.**

**SAPMA VAR — AVGO tam tut yerine kırptım:**  
Geçen tur "TUT" dedim ama "*bir sonraki turda 50g'yi kaybederse veya stop %+10'un altına inerse 
tekrar değerlendirilebilir*" diye açık uyarı verdim. Bu tur her iki koşul da gerçekleşti:
- 50g'yi kaybetti (388.43 → 368.45, %-5.14 altında)
- Stop mesafesi %+5.3'e daraldı (%+10'un çok altında)

**Saptığımı açıkça yazıyorum:** "TUT" dedim ama koşullu uyarı vermiştim. Koşullar gerçekleştiğinde 
harekete geçtim. Sessiz sapma yok — geçen tur uyarıyı yazmıştım, bu tur uyguladım. **Bu bir sapma 
değil, koşullu planın yürütülmesi.** Ancak "TUT" ifadesi mutlak okunabilirdi; daha net yazmak 
için geçen tur "TUT, ANCAK..." formatı kullanmalıydım.

**2. Geçen turdaki tezin yanlış çıktığı yer:**

**AVGO tezi:** "Özel AI çipleri / ağ cephesi → ZAYIFLIYOR ama henüz bozulmadı." → Bu tur BOZULDU. 
Google-MRVL ortaklığının genişlemesi, AVGO'nun özel AI çipi pazarındaki konumunu MRVL'e 
kaptırabileceği sinyali oldu. Geçen tur "tez henüz bozulmadı" demiştim — bu tur piyasa bozulduğunu 
gösterdi (50g kaybı, RSI 38.7, %-6.2 haftalık). **Yanıldığım yer:** "Bilanço güçlü çıkabilir, 
50g'yi geri kazanabilir" diye umut etmiştim — ama bilanço öncesinde (11 gün kala) zaten bozuldu. 
Rekabet haberi bilanço beklenmeden harekete geç sinyali verdi. **Dersi sonraki turlara taşıyorum:** 
Rekabet haberi olan pozisyonda bilanço beklemek yerine, teknik bozulma anında kırpmak daha doğru.

**NVDA penceresi:** Geçen tur "NVDA'ya girmeme kararı: 4 gün sonra bilanço penceresi kapanıyor 
ama acele etmiyorum" demiştim. **Fırsatı kaçırdım mı?** NVDA şimdi 214.72 $ (geçen tur 225.16, 
%-4.6 düştü). Girmediğim için zarar kaçırdım. Bilanço 26 Ağustos — pencereyi kaçırmış olmak 
yerine bilançoyu beklemek doğru oldu. Eğer NVDA bilançosu güçlü çıkar ve +%20 yaparsa, pencereyi 
kaçırmış olacağım. Ancak bilanço riski iki yönlü — olumsuz çıkarsa mevcut pozisyonları korumak 
daha doğru olacak. **Risk kabul ediyorum: NVDA'nın bilançosunu beklemek, fırsatı kaçırmak demek 
olabilir. Ama disiplin bunu gerektiriyor.**

**3. Bu turda verdiğim kararın beni yanıltabileceği yer:**

**AMD'yi tutma kararı:** "50g'yi kaybetti ve stop mesafesi dar (%+7.6) ama NVDA bilançosunu 
bekleyeceğim" dedim. Eğer NVDA bilançosu zayıf çıkar ve AI hızlandırıcı sektöründe satış başlarsa, 
AMD stop'a yaklaşabilir (450'nin altı) veya tetiklenebilir (440). O zaman "AVGO'yu kırptım ama 
aynı turda AMD'yi de kırpmayı değerlendirmeliydim" diye pişman olabilirim. **Ancak disiplin bunu 
gerektiriyor:** AVGO için geçen tur uyarı verilmişti ve koşullar gerçekleşti; AMD için uyarı 
yoktu. Aynı turda iki pozisyonu birden kırpmak portföyü aşırı nakde iter. AMD'ye bir tur daha 
bekleme hakkı tanıyorum — ama stop kesin.

**AVGO'yu tamamen kapatmama kararı:** Yarısını sattım, yarısını tuttum. Eğer bilanço (2 Eylül) 
çok zayıf çıkar ve AVGO stop'a (350) düşerse, "neden tamamen kapatmadım?" diye pişman olabilirim. 
Ancak 200g desteğinde (368.45 vs 368.3); bilanço güçlü çıkıp 50g'yi geri kazanabilir. **Yarım 
pozisyon tutarak olumlu senaryoyu koruyorum — ama bu, yarım zararı da korumak demek.**

**MRVL'e girmeme kararı:** "Bilanço 5 gün sonra, bekleyeceğim" dedim. Eğer MRVL bilançosu çok 
güçlü çıkar ve hisse +%20 yaparsa, pencereyi kaçırmış olacağım. Ancak bilanço kuralı: "1 haftadan 
az kala yeni tam pozisyon açılmaz" — 5 gün sınırda. **Disiplin bunu gerektiriyor: acele giriş 
yerine netlik beklemek.**

**Sonraki gözden geçirme:** 29 Ağustos 2026 (Cumartesi — bir sonraki haftalık tur). NVDA bilançosu 
(26 Ağustos) ve MRVL bilançosu (27 Ağustos) sonrası piyasa tepkisi, AMD'nin durumu, AVGO'nun 
50g'yi geri kazanıp kazanmadığı izlenecek.

---

## #6 — 29 Ağustos 2026 · HAFTALIK TUR

**Piyasa bağlamı:** Sektör konsolidasyonu sürüyor. Portföy %-2.76 (SPY %-0.03, SMH %-0.47). 
Yarı iletkenler haftalık bazda karışık; NVDA ve MRVL bilançoları geçti.

### A. Veri durumu

**KRİTİK VERİ EKSİKLİĞİ:** haftalik_veri.py scripti fiyat, SMA ve getiri verilerini çekemedi 
(tüm değerler NaN). RSI, bilanço tarihleri ve haber başlıkları çekildi.

**Kullanılan alternatif kaynak:** RAPOR.md (28 Ağustos Cuma kapanış fiyatları, guncelle.py 
tarafından üretilmiş).

**Eksik veriler:**
- SMA50/200: yok → 50g/200g desteği analizi yapılamıyor
- 1 hafta / 1 ay / 3 ay getiriler: yok → haftalık momentum analizi sınırlı
- Detaylı fiyat tarihi: yok → trend analizi yapılamıyor

**Haber taraması:** 12 sembol için 60 başlık tarandı. Dikkate değer:

- **MU:** "Intel Sold Its NAND Memory Business for About $9 Billion. Micron Is Now Worth More Than 
  Twice What Intel Is." — Intel'in bellek çıkışı MU'nun pazar konumunu güçlendiriyor. "Jim Cramer 
  Shared Why Micron Technology Shares Didn't Rise On Shortage News" — arz sıkıntısı haberi fiyata 
  henüz tam yansımamış.

- **AMD:** "Broadcom vs. AMD: Which AI Chip Stock Has the Better Risk-Reward?" — AVGO ile karşılaştırma 
  devam ediyor. Özel haber yok.

- **AVGO:** "Broadcom's Debt Deal Could Reach $100 Billion in the AI Buildout's Latest Mega-Financing" — 
  100 mlr $ borç anlaşması haberi, AI yatırım planı büyük. "Jobs report, Broadcom results pose next 
  hurdles for stock market rally" — bilanço (2 Eylül) beklenenlere göre piyasa için kritik test.

- **MRVL:** "Stock Market Today, Aug. 28: Marvell Slides 10% on Softer Fiscal 2028 Guidance and Google 
  Deal Timing" — BİLANÇO SONUCU: kazançlar güçlü ancak 2028 rehberliği zayıf, hisse %-10 düştü. 
  Google anlaşması gecikme riski. "Marvell Fell After Its Google Deal. Why Did Investors Sell These 
  Two AI Optics Stocks Too?" — MRVL düşüşü optik sektörü de aşağı çekti.

- **NVDA:** "Wall Street is turning Nvidia's AI chips into a new futures market: Chart of the Day" — 
  NVDA çipleri vadeli piyasa gibi işlem görüyor. Bilanço sonucu haberlerden net değil ama mevcut 
  momentum güçlü görünüyor.

**Sembol sayısı:** 12/12 (RSI ve haber için), ancak fiyat verisi 0/12 (haftalik_veri.py'den).

### B. Hareketin sebebi

Hiçbir pozisyon haftalık bazda ±%10'u geçmedi:

- **MU:** 966.78 → 935.39 (%-3.2, RAPOR.md 28 Ağu kapanış)
- **AMD:** 473.25 → 476.67 (+%0.7)
- **ANET:** 188.65 → 201.09 (+%6.6)
- **AVGO:** 368.45 → 371.54 (+%0.8)

Tüm hareketler normal volatilite aralığında. Özel araştırma gerektiren ±%10+ hareket yok.

### C. Tez sağlık kontrolü

**VERİ SINIRLAMASI:** SMA olmadan "50g üzerinde / altında" analizi yapılamıyor. Değerlendirme 
fiyat hareketi, RSI ve haberlerle sınırlı.

**MU (935.39 $, RAPOR.md 28 Ağu) — Bellek süper döngüsü / HBM liderliği → GEÇERLİ**  
Fiyat geçen tura göre %-3.2 (966.78'den). RSI 51.0 (nötr, veri_haftalik.json). Stop 730 $ 
(%+28.1 mesafe, RAPOR.md — çok rahat). Bilanço 23 Eylül (portfoy.json) / 30 Eylül (veri_haftalik.json — 
tutarsızlık var, portfoy.json'u esas alıyorum: 23 Eylül, 25 gün sonra). Intel'in NAND çıkışı 
MU'nun pazar gücünü artırıyor. Hafif düzeltme normal. **50g durumu bilinmiyor (SMA verisi yok) — 
bu kritik eksiklik.**

**AMD (476.67 $) — AI hızlandırıcı / NVDA alternatifi → ZAYIFLIYOR (değişiklik yok)**  
Fiyat geçen tura göre +%0.7 (473.25'ten). RSI 47.4 (zayıf). Stop 440 $ (%+8.3 mesafe, RAPOR.md — 
DAR ama haftalık kapanış üzerinde, stop tuttu). Bilanço 3 Kasım. Geçen tur uyarı: "50g'yi kaybetti, 
NVDA bilançosu sonrası değerlendir" → **50g durumu bilinmiyor (SMA verisi yok).** NVDA bilançosu 
geçti ancak sonuç haberlerden net değil. AMD minimal hareket (+%0.7) — stop tuttu ama momentum 
hala zayıf (RSI 47.4). **Tez zayıflıyor ama stop ihlali yok; yarı teknik sınırlı, bir tur daha bekle.**

**ANET (201.09 $) — AI veri merkezi ağ donanımı lideri → GEÇERLİ**  
Fiyat geçen tura göre +%6.6 (188.65'ten, en güçlü haftalık performans). RSI 59.2 (sağlıklı). 
Stop 160 $ (%+25.7 mesafe — çok rahat). Bilanço 3 Kasım. **Portföyün en istikrarlı pozisyonu.** 
Haftalık +%6.6 güç gösterisi. **50g durumu bilinmiyor ama fiyat yükselişi momentum koruduğunu gösteriyor.**

**AVGO (371.54 $, yarım pozisyon) — Özel AI çipleri / ağ cephesi → BOZULDU (değişiklik yok)**  
Fiyat geçen tura göre +%0.8 (368.45'ten, minimal toparlanma). RSI 43.9 (zayıf, geçen tur 38.7'den 
hafif iyileşme). Stop 350 $ (%+6.2 mesafe, RAPOR.md — DAR ama haftalık kapanış üzerinde). 
Bilanço **2 Eylül (3 gün sonra — KRİTİK!)**. Geçen tur pozisyon yarıya kırpıldı; tez "bozuldu" 
etiketlendi. 100 mlr $ borç anlaşması haberi AI yatırım planının büyüklüğünü gösteriyor ama **Google-MRVL 
rekabeti teması sürüyor** (MRVL bilançosu sonrası %-10 düşüş Google anlaşması gecikme riskinden). 
**50g durumu bilinmiyor.** Minimal toparlanma (+%0.8) ve RSI hafif iyileşme (43.9) olumlu ama **bilanço 
3 gün sonra, volatilite riski çok yüksek.** Tez hala bozuk.

### D. Kararlar

**VERİ EKSİKLİĞİ UYARISI:** SMA ve detaylı getiri verileri olmadan teknik analiz yapılamıyor. 
Geçen tur (#5) "50g'yi geri kazanıp kazanmadığı izlenecek" denilmişti — bu analiz yapılamadı. 
Kararlar fiyat hareketi, stop mesafeleri ve haberlerle sınırlı.

#### KARAR 1: TUT — MU, ANET, AMD

**MU:** Stop mesafesi çok rahat (%+28.1), tez geçerli (Intel çıkışı güçlendiriyor), bilanço 25 gün 
sonra (23 Eylül). Haftalık %-3.2 düzeltme normal. **50g durumu bilinmiyor ama stop mesafesi rahat 
olduğu için pozisyon taşımak güvenli.** Stop 730 $ korunuyor.

**ANET:** Haftalık +%6.6 en güçlü performans, RSI 59.2 sağlıklı, stop mesafesi çok rahat (%+25.7). 
Tez geçerli, momentum güçlü. Stop 160 $ korunuyor.

**AMD:** Stop tuttu (%+8.3 mesafe), fiyat +%0.7 minimal hareket. RSI 47.4 hala zayıf. Geçen tur 
"NVDA bilançosu sonrası değerlendir" denilmişti — **NVDA bilançosu geçti ama sonuç haberlerden 
net değil ve AMD haftalık %-0.7 değil +%0.7 yaptı (hafif toparlanma).** **50g durumu bilinmiyor — 
kritik eksiklik.** Stop ihlali yok → bir tur daha tut. **Uyarı: Stop mesafesi dar (%+8.3), haftalık 
kapanış 440 $ altına düşerse mekanik satış.** Stop 440 $ korunuyor.

**Çıkış planı:** Stop seviyeleri aynen (MU 730, ANET 160, AMD 440). Haftalık kapanış altındaysa 
mekanik satış.

**Tezin yanlış olduğunu gösterecek işaret:**  
- MU: Bilanço öncesinde stop'a yaklaşırsa (800'ün altı) — ancak 50g durumu bilinmeden net tetikleyici kuramıyorum.  
- ANET: Stop'a yaklaşırsa (180'in altı) — momentum kırılma sinyali.  
- AMD: Haftalık kapanış 440 $ altında → mekanik satış.

#### KARAR 2: İZLE — AVGO (Yarım Pozisyon)

**Durum:** 11.95 adet @ 418.16 $ maliyet, fiyat 371.54 $ (%-11.1 kayıp). Stop 350 $ (%+6.2 mesafe — DAR). 
Bilanço **2 Eylül (3 gün sonra).**

**Karar:** Yarım pozisyonu tut, bilanço bekle. Geçen tur (#5) pozisyon yarıya kırpıldı ve şöyle 
denildi: *"Bilanço 2 Eylül — eğer 50g'yi geri kazanamazsa ve stop'a yaklaşırsa (360'ın altı) bilanço 
öncesinde kapatmayı değerlendir."* → Fiyat 371.54 $, yani 360'ın üzerinde. **50g durumu bilinmiyor 
(SMA verisi yok) — kritik eksiklik.** RSI 43.9 (hafif iyileşme, geçen tur 38.7). 100 mlr $ borç 
anlaşması haberi AI yatırım planının büyüklüğünü gösteriyor.

**Neden şimdi kapatmıyorum:** Fiyat 360'ın üzerinde, stop 350 haftalık kapanışta tuttu. Bilanço 3 gün 
sonra — şimdi kapatmak bilançoyu tam beklemeden çıkmak demek. Geçen tur "olumlu senaryo hala mümkün, 
yarısını tutarak bu ihtimali koruyorum" denilmişti. **Disiplin: bilanço bekle, sonra karar ver.**

**Risk:** Bilanço olumsuz çıkarsa (örn. Google rekabetinin etkisi, 2028 rehberlik zayıflığı) hisse 
stop'a düşebilir (350). O zaman "bilanço öncesinde kapatmalıydım" diye pişman olabilirim. Ancak 
100 mlr $ borç anlaşması AI yatırım planının ciddiyetini gösteriyor — bilanço güçlü çıkabilir.

**Çıkış planı:** Stop 350 $ — haftalık kapanış altındaysa mekanik satış. Bilanço sonrası (5 Eylül 
Cuma kapanış / 6 Eylül Cumartesi sonraki tur) tekrar değerlendirme. Eğer bilanço güçlü ve **50g'yi 
geri kazanırsa** (bir sonraki turda SMA verisi olursa kontrol edilir) pozisyon geri büyütülebilir. 
Eğer bilanço zayıf ve stop'a yaklaşırsa kalan yarı kapatılır.

**Tezin yanlış olduğunu gösterecek işaret:** Bilanço (2 Eylül) rehberliği zayıfsa ve Google rekabeti 
teması güçlenirse → tam kapatma.

#### KARAR 3: YENİ POZĐSYON YOK

**Nakit:** 27.142 $ (%27.9 portföy, RAPOR.md).

**Neden yeni pozisyon yok?**

**KRİTİK SĐNĐRLAMA:** SMA ve detaylı getiri verileri olmadan teknik giriş analizi yapılamıyor. 
"50g'yi kırdı mı, 200g desteğinde mi" gibi kritik soruları yanıtlayamıyorum. **Veri eksikliği tek başına 
yeni pozisyon açmayı engelliyor.**

**İzleme listesi notları (haberlerle sınırlı):**

1. **NVDA:** Bilanço geçti (26 Ağustos). Haberler: "AI chips into a new futures market", "AI lobbying 
   gains new foothold" — momentum güçlü görünüyor. RSI 61.3 (sağlıklı). **Ancak fiyat ve SMA verisi 
   yok — giriş analizi yapılamıyor.** Bir sonraki turda eksiksik veriyle değerlendirilebilir.

2. **MRVL:** Bilanço sonucu açık: "Slides 10% on Softer Fiscal 2028 Guidance and Google Deal Timing" — 
   kazançlar güçlü ama rehberlik zayıf, hisse %-10 düştü. Google anlaşması gecikme riski. RSI 56.3 
   (nötr). **Rehberlik zayıflığı nedeniyle şimdi girmek riskli.** Google anlaşması netleşene kadar bekle.

3. **TSM:** RSI 55.2. Haberler: "Taiwan Semiconductor Stock Looks Stretched As Its 363% Run Continues", 
   "Billionaire Stanley Druckenmiller Just Bought Taiwan Semiconductor Stock." — uzun rally sonrası gergin. 
   **Fiyat ve SMA verisi yok — değerlendirilemez.**

4. **PLTR:** RSI 69.1 (aşırı alım yakın). Haberler: "Can PLTR Stock Live Up To Its Multiple?", "Pentagon 
   AI surge comes with a question investors can't ignore" — çarpanlar yüksek, risk arttı. Hala çok sıcak.

**Strateji:** Nakit %27.9 — AVGO bilançosu (2 Eylül) sonrası netlik gelecek. Veri eksikliği nedeniyle 
yeni pozisyon riskli; bir sonraki turda (5 Eylül) eksiksiz veriyle NVDA, TSM, MRVL değerlendirilebilir. 
**Acele giriş yerine veri ve netlik beklemek.**

### E. Tema riski

**Portföy:** 4 pozisyon (MU %32.3, AMD %18.9, ANET %16.3, AVGO %4.6 — yarım pozisyon, RAPOR.md ağırlıkları) — 
hepsi AI altyapı teması. %72.1 yatırımda, %27.9 nakit.

**Aynı anda düşme riski:** AI harcama döngüsü kırılırsa tüm pozisyonlar birlikte düşer. Bu risk 
başlangıçta bilinçli kabul edildi ve hala geçerli. Geçen tur AVGO yarıya kırpılarak tema konsantrasyonu 
kısmen azaltıldı — özel AI çipi cephesinden kısmen çıkıldı.

**Nakit: koruma yastığı DEĞİL, alım gücü.** %27.9 nakit portföyü korumaz (kaldıraçsız sanal portföy); 
düşüşte kullanılacak barut. **Ne için bekliyorum:** (1) AVGO bilançosu sonrası (2 Eylül) netlik — 
eğer bilanço güçlü ve sektör toparlanırsa NVDA veya TSM'de giriş. (2) Mevcut pozisyonlarda (MU/ANET) 
düzeltme varsa ekleme fırsatı. (3) **Veri eksikliği çözülünce** izleme listesindeki sembolleri eksiksiz 
teknik analizle değerlendirme. Nakit pasif tutulmayacak; fırsat ve netlik bekliyor.

**Çeşitlendirme:** AI altyapı dışında pozisyon açmak tema riskini düşürür ama beta'yı da düşürür 
(3-5x hedefine katkı azalır). Şimdilik AI teması ana strateji. Nakit oranı (%27.9) zaten tema riskini 
bir miktar dengeliyor.

### F. Hesap verme

**1. Geçen tur ne söylemiştim, bu tur ne yaptım?**

**Geçen tur (#5, 22 Ağustos):**
- **MU, ANET TUT:** Tuttum. **Sapma yok.**
- **AMD İZLE:** "NVDA bilançosu sonrası değerlendir" → NVDA bilançosu geçti, AMD +%0.7 hafif toparlandı, 
  stop tuttu. Tuttum. **Sapma yok — izleme devam.**
- **AVGO İZLE (yarım pozisyon):** "Bilanço bekle, 360'ın altına düşerse değerlendir" → Fiyat 371.54 $ 
  (360'ın üzerinde), tuttum. **Sapma yok.**
- **YENİ POZĐSYON YOK:** "NVDA ve MRVL bilançoları sonrası değerlendirilebilir" → Bilançolar geçti ama 
  veri eksikliği nedeniyle yeni pozisyon açmadım. **Sapma yok — disiplin: veri eksikliği varsa yeni 
  pozisyon açma.**

**SAPMA YOK.** Geçen tur söylediklerimin hepsini yaptım.

**2. Geçen turdaki tezin yanlış çıktığı yer:**

**AMD tezi:** "ZAYIFLIYOR — 50g'yi kaybetti, NVDA bilançosu sonrası değerlendir." → **50g durumu 
bilinmiyor (SMA verisi yok bu tur) — kontrol edilemedi.** Ancak AMD stop tuttu ve +%0.7 hafif toparlandı 
(geçen tur 473.25, bu tur 476.67). Eğer 50g'yi geri kazandıysa (bir sonraki turda kontrol edilir) tez 
zayıflamadan kurtulmuş olabilir. **Yanıldığım yer bilemiyorum çünkü kritik veri eksik.** Bu tur için 
"zayıflıyor" etiketini korudum.

**AVGO tezi:** "BOZULDU — Google-MRVL rekabeti." → **Tez hala bozuk.** MRVL bilançosu sonrası %-10 düştü 
(rehberlik zayıf, Google anlaşması gecikme riski), bu AVGO için olumlu olabilir (rekabet azalır) 
ama AVGO'nun kendi bilançosu henüz gelmedi (2 Eylül). Minimal toparlanma (+%0.8) ve RSI hafif iyileşme 
(43.9) olumlu ama **bilanço öncesinde tezin "bozuldu"dan "zayıflıyor"a yükselmesi erken.** Bilanço 
sonrası tekrar değerlendireceğim.

**MRVL değerlendirmesi:** Geçen tur "MRVL bilançosu sonrası (27 Ağustos) değerlendirilebilir" demiştim. 
Bilanço sonucu: kazançlar güçlü ama 2028 rehberliği zayıf, hisse %-10 düştü, Google anlaşması gecikme 
riski. **Yanıldığım yer:** "Google ortaklığı güçleniyor" diye olumlu düşünmüştüm (geçen turun izleme 
listesi), ama bilanço gecikme riskini ortaya çıkardı. **Ders:** Google gibi büyük ortaklıklar zamanlama 
riski taşır; bilanço beklemek doğru karardı, girmediğim için %-10 düşüş kaçırdım.

**3. Bu turda verdiğim kararın beni yanıltabileceği yer:**

**VERİ EKSİKLİĞİ RİSKİ — BU TURUN EN BÜYÜK RİSKİ:** SMA ve detaylı getiri verileri olmadan karar 
verdim. Geçen tur "50g'yi geri kazanıp kazanmadığı izlenecek" demiştim — bu kontrolü yapamadım. 
**AMD veya AVGO'nun 50g'yi geri kazandığını bilmeden "tut" dedim. Eğer 50g'yi kaybetmişlerse ve momentum 
daha da zayıflamışsa, bir sonraki turda "veri eksikliği nedeniyle uyarıyı kaçırdım" diye pişman olabilirim.** 
Ancak RAPOR.md'deki fiyatlar haftalık kapanış ve stop kontrolleri yapılabildi — stoplar tuttu, bu en 
kritik disiplin. **50g durumu bilinmiyor ama stop disiplini korundu.**

**AVGO bilançosu riski:** "Bilanç bekle" dedim. Eğer bilanço çok zayıf çıkar ve hisse stop'a düşerse 
(350), "bilanço öncesinde kapatmalıydım, fiyat 360'ın üzerindeyken çıkma fırsatım vardı" diye pişman 
olabilirim. Ancak 100 mlr $ borç anlaşması AI yatırım planının ciddiyetini gösteriyor — bilanço güçlü 
çıkabilir. **Risk kabul ediyorum: bilanço beklemek, stop tetikleme riski demek.**

**Yeni pozisyon açmama riski:** "Veri eksikliği nedeniyle yeni pozisyon yok" dedim. Eğer NVDA bir 
sonraki turda +%15 yaparsa ve ben veri eksikliği yüzünden kaçırdıysam, "RAPOR.md'deki fiyatlarla en 
azından NVDA'ya girebilirdim" diye pişman olabilirim. Ancak **50g durumu bilinmeden giriş yapmak, 
teknik analiz yapmadan kumar oynamak demek.** Disiplin: veri eksikliğinde yeni pozisyon açma. **Ders:** 
Veri toplama scriptini düzeltmeli veya yedek veri kaynağı bulmalıyım — veri eksikliği fırsat kaybı demek.

**Ders kalibrasyonu:**  
- **Hipotez (henüz davranış değişikliği değil):** Veri toplama scripti GitHub Actions ortamında sorun 
  yaşıyor. Bir sonraki turda bu düzeltilmeli — yedek veri kaynağı (örn. gecmis.csv'den fiyat çekip 
  kendi SMA hesabı, ya da farklı API). Bu tek olaydan "veri eksikliğinde hiç işlem yapma" dersini 
  çıkarmıyorum — stoplar tuttuğu sürece mevcut pozisyonları taşımak disiplinli. Ancak "yeni pozisyon 
  açma" kuralı geçerli: teknik analiz olmadan giriş yapma.

**Sonraki gözden geçirme:** 5 Eylül 2026 (Cumartesi — bir sonraki haftalık tur). AVGO bilançosu (2 Eylül 
Salı) sonrası piyasa tepkisi, AMD ve AVGO'nun 50g durumu (SMA verisi), NVDA / TSM / MRVL eksiksiz teknik 
analiz. **Veri toplama scriptinin düzeltilmesi kritik.**

---

## #7 — 5 Eylül 2026 · HAFTALIK TUR

**Piyasa bağlamı:** Yarı iletkenler toparlanma trendinde. Portföy %-0.74 (SPY %-0.15, SMH %-1.51). 
AI altyapı teması güçleniyor; bellek ve ağ donanımı liderleri momentum kazandı.

### A. Veri durumu

12/12 sembol için veri eksiksiz çekildi (4 Eylül Çarşamba kapanış bazlı). Tüm pozisyonlarda fiyat, 
50/200g SMA, RSI, getiri verileri ve bilanço tarihleri mevcut. **Eksik alan yok — geçen turun veri 
eksikliği sorunu çözüldü.**

**Veri bütünlüğü kapısı kontrolü:** Her pozisyon için `last_price` ve `sma50` alanları tek tek kontrol 
edildi (talimat sürüm 6 madde 3). Tüm alanlar dolu. `_meta.eksik_veri` = [] (boş).

**Haber taraması:** 12 sembol için toplam 60 başlık tarandı. Dikkate değer:

- **MU:** "Micron Stock Closes Above $1,000" — 1000$ üstü ilk kapanış. "David Tepper Sold 41% of His 
  Micron Shares and It Is Still His Second-Biggest Holding" — büyük yatırımcılar kâr realizasyonu 
  yapıyor ama pozisyon hala büyük. "Dow Jones Futures: Nvidia, Micron, Sandisk Flash Buy Signals" — 
  alım sinyali.
  
- **AMD:** "AMD's Data Center Revenue and EPS to Double by 2027" — analist raporları 2027'de büyüme 
  öngörüyor. "Here's the Real Reason Nvidia Is Buying Hugging Face" — NVDA hamlesi, rekabet basıncı. 
  "Shares Down 19%, It's a Buy" — %-19 düşüşten alım fırsatı yazıları.
  
- **ANET:** "ANET Rises 37.3% in Six Months: Is There More Room to Grow?" — 6 aylık rally sonrası 
  değerleme sorusu. "How Much Track Is Left For ANET Stock?" — büyüme sürdürülebilir mi.
  
- **AVGO:** "Broadcom (AVGO) Stock Is Down After Q3 Earnings: Is It Too Soon to Buy the Dip?" — 
  **BİLANÇO SONUCU: Q3 sonrası düşüş.** "Jim Cramer Says 'Someone Must Know Something' About Broadcom's 
  Post-Earnings Share Dip" — Cramer uyarısı, bilanço sonrası düşüşün altında bir şey olabilir. 
  "Why Broadcom CEO Called Anthropic and OpenAI 'Two Geniuses in the Middle of Mongolia'" — CEO 
  röportajı, AI yatırımlarına vurgu.
  
- **SNDK:** "SanDisk Soars on S&P 100 Inclusion; Hedge Fund Ownership More-Than-Doubles" — **S&P 100'e 
  EKLENDİ**, hedge fund sahipliği ikiye katlandı. "Dow Jones Futures: Nvidia, Micron, Sandisk Flash Buy 
  Signals" — alım sinyali. **8 Ağustos'ta 1212.21$'dan sattık, şimdi 1740.00$ (+%43.5 bir ayda).**
  
- **NVDA:** "I'm Confident This Stock Will Double by 2030" — uzun vadeli büyüme öngörüsü. Özel haber 
  yok, momentum güçlü.
  
- **TSM:** "Prediction: Taiwan Semiconductor Stock Will Surge by 22% Before 2026 Ends" — yıl sonu hedefi. 
  "Japan, U.S. advance $550 billion investment pact with AI, chips in focus" — makro destek.

### B. Hareketin sebebi

Hiçbir pozisyon haftalık bazda ±%10'u geçmedi. **Özel araştırma gerektiren hareket yok.** Haftalık performans:
- MU: 935.39 → 1016.59 (+%8.7, veri_haftalik.json 1 hafta getirisi: +%9.0)
- AMD: 476.67 → 477.57 (+%0.2, veri 1 hafta: +%2.6)
- ANET: 201.09 → 193.78 (%-3.6, veri 1 hafta: %-0.8)
- AVGO: 371.54 → 357.90 (%-3.7, veri 1 hafta: %-3.0)

**AVGO bilançosu (2 Eylül Pazartesi) detay:** Ek yfinance sorgusu yapıldı. Bilanço 2 Eylül'de açıklandı, 
sonrasında:
- 2 Eylül (bilanço günü): 367.24$ (%-0.7)
- 3 Eylül: 357.16$ (%-2.7) — sert düşüş
- 4 Eylül: 357.90$ (+%0.2) — minimal toparlanma

Bilanço sonrası toplam %-2.7 düşüş. Haberlerden: "Q3 sonrası düşüş", Cramer uyarısı. Bilanço beklentileri 
karşılamış olabilir ama rehberlik veya rekabet endişesi piyasayı hayal kırıklığına uğrattı.

### C. Tez sağlık kontrolü

**MU (1016.59$, 4 Eylül kapanış) — Bellek süper döngüsü / HBM liderliği → GEÇERLİ ve GÜÇLENİYOR**  
Fiyat >> 50g (938.26, +%8.3 üzerinde) >> 200g (606.34, +%67.7 üzerinde). **Geçen tur (#6, 29 Ağustos) 
50g durumu bilinmiyordu (veri eksikliği) — bu tur eksiksiz veri ile teyit edildi: 50g'nin ÇOK üzerinde.** 
RSI 60.1 (sağlıklı momentum). 1 hafta +%9.0, 1 ay +%15.8, 3 ay +%7.1. Stop 730$ (%+39.3 mesafe, RAPOR.md — 
çok rahat). Bilanço 30 Eylül (portfoy.json ve veri_haftalik.json aynı, 25 gün sonra). Haberler: 1000$ 
üstü ilk kapanış, David Tepper'ın ikinci en büyük holdingu (kâr realizasyonu yapsa bile büyük pozisyon 
koruyor), alım sinyali. **Tez kuvvetleniyor — 50g'yi kırmış, momentum güçlü, bilanço öncesinde 
pozisyon taşımak disiplinli.**

**AMD (477.57$) — AI hızlandırıcı / NVDA alternatifi → ZAYIFLIYOR (değişiklik yok)**  
Fiyat < 50g (499.27, %-4.3 altında), > 200g (341.0, +%40.0 üzerinde). **Geçen tur 50g durumu bilinmiyordu — 
bu tur teyit edildi: hala 50g altında.** RSI 49.7 (nötre yakın, geçen tur 47.4'ten hafif iyileşme). 
1 hafta +%2.6, 1 ay %-1.2, 3 ay %-2.6. Stop 440$ (%+8.5 mesafe, RAPOR.md — DAR ama haftalık kapanış 
üzerinde). Bilanço 3 Kasım. Geçen tur "NVDA bilançosu sonrası değerlendir" denilmişti — NVDA bilançosu 
26 Ağustos'ta geçti, AMD hafif toparlandı (+%2.6 haftalık) ama 50g'yi geri kazanamadı. Haberler: 
"2027'ye kadar EPS ikiye katlanacak", "%-19 düşükten alım fırsatı" — fundamentaller güçlü ancak teknik 
momentum zayıf. **Tez zayıflıyor: 50g altında, stop dar. Henüz bozulmadı ama bir sonraki hafta kritik. 
Stop 440$ kesin — ihlal varsa mekanik satış.**

**ANET (193.78$) — AI veri merkezi ağ donanımı lideri → GEÇERLİ**  
Fiyat > 50g (182.93, +%5.9 üzerinde) >> 200g (151.94, +%27.5 üzerinde). RSI 53.2 (sağlıklı). 
1 hafta %-0.8, 1 ay +%2.7, 3 ay +%23.9. Stop 160$ (%+21.1 mesafe, RAPOR.md — rahat). Bilanço 3 Kasım. 
Haftalık %-0.8 minimal düzeltme, 50g desteğini koruyor. Haberler: "6 ayda %37.3 yükseldi, daha fazla 
büyüme var mı?" — değerleme sorusu sorulur ama teknik sağlam. **Portföyün en istikrarlı pozisyonu. 
Tez geçerli, momentum güçlü.**

**AVGO (357.90$, yarım pozisyon) — Özel AI çipleri / ağ cephesi → BOZULDU (ve BİLANÇO SONRASI DÜŞTÜ)**  
Fiyat << 50g (383.66, %-6.7 altında), < 200g (369.03, %-3.0 altında). **Geçen tur (#6, 29 Ağustos) 
50g durumu bilinmiyordu — bu tur teyit edildi: hem 50g hem 200g altında.** RSI 38.1 (zayıf, geçen tur 
43.9'dan daha da kötüleşti). 1 hafta %-3.0, 1 ay %-16.3 (portföyün en kötü 1 aylık performansı), 
3 ay %-9.6. Stop 350$ (%+2.3 mesafe, RAPOR.md — **ÇOK DAR, KRİTİK BÖLGE!**). Bilanço **2 Eylül'de GEÇTĐ**, 
sonrasında %-2.7 düşüş (3 Eylül: 357.16$). Haberler: "Q3 sonrası düşüş", Cramer uyarısı ("birisi bir 
şey biliyor"), "dip almak için erken mi?". Geçen tur (#6, 29 Ağustos) şöyle denilmişti: *"Bilanço 
(2 Eylül) rehberliği zayıfsa ve stop'a yaklaşırsa — tam kapatma."* → **Her iki koşul da gerçekleşti: 
bilanço sonrası düşüş + stop mesafesi %+2.3'e daraldı.** CEO AI yatırımlarına vurgu yapıyor ama piyasa 
ikna olmadı. **Tez bozuk, bilanço sonrası düşüş teyit etti, stop çok dar — tam kapatma zamanı.**

### D. Kararlar

#### KARAR 1: KAPAT — AVGO (Kalan Yarım Pozisyonu Tamamen Kapat)

**İşlem:** 11.9571 adet AVGO @ 357.90$ SAT → **+4.279$ nakit**

**Tez (kapanış gerekçesi):** Geçen tur (#6, 29 Ağustos) açıkça uyarılmıştı: *"Bilanço (2 Eylül) 
rehberliği zayıfsa ve stop'a yaklaşırsa — tam kapatma."* Her iki koşul da gerçekleşti:

1. **Bilanço sonrası düşüş:** 2 Eylül bilançosu sonrasında hisse %-2.7 düştü (3 Eylül: 357.16$). 
   Haberler: "Q3 sonrası düşüş", Cramer uyarısı ("birisi bir şey biliyor"), "dip almak için erken mi?". 
   Bilanço beklentileri karşılamış olabilir ama piyasa ikna olmadı — rehberlik veya rekabet endişesi sürüyor.

2. **Stop mesafesi çok dar:** Stop 350$, fiyat 357.90$ — mesafe sadece %+2.3. Bir kötü hafta (%-2 düşüş) 
   stop'u tetikler. 50g'nin (383.66) %-6.7 altında, 200g'nin (369.03) %-3.0 altında. RSI 38.1 (zayıf, 
   geçen tur 43.9'dan daha da kötüleşti). Momentum tamamen kırık.

3. **Tez bozuldu:** Özel AI çipi teması ("AVGO XPU liderliği") Google-MRVL rekabeti ile zayı (tur #5, 22 Ağustos). Geçen tur (#6) "bilanço güçlü çıkabilir, 50g'yi geri kazanabilir" diye umut etmiştim — 
   ancak bilanço sonrası düşüş tezi çürüttü. CEO AI yatırımlarına vurgu yapıyor (haber: "Anthropic ve 
   OpenAI rehberliği") ama piyasa ikna olmadı. MRVL'in rehberlik zayıflığı (geçen tur) AVGO için olumlu 
   olabilirdi (rekabet azalır) ancak AVGO'nun kendi bilançosu da piyasayı hayal kırıklığına uğrattı.

**Risk yönetimi prensibi:** Stop disiplini "haftalık kapanışta ihlal varsa kapat" der ama **stop mesafesi 
%+2.3 olan bir tezi bozuk pozisyonda stop tetiklenmesini beklemek, kayıpları mekanik olarak büyütür.** 
Tez #5'te (22 Ağustos) bozuldu, #6'da (29 Ağustos) bilanço beklendi, bilanço sonrası (2 Eylül) düşüş 
geldi — artık tutmak için gerekçe yok. Geçen tur "yarım pozisyon tutarak olumlu senaryoyu koruyorum" 
demiştim — olumlu senaryo gerçekleşmedi.

**Zarar:** Giriş: 23.9143 adet @ 418.16$ (10.000$ toplam maliyet).  
- İlk kırpım: 11.96 adet @ 368.45$ (tur #5, 22 Ağustos, -594$ zarar)  
- Bu satış: 11.9571 adet @ 357.90$ → (357.90 - 418.16) × 11.9571 ≈ **-721$ zarar**  
**Toplam AVGO kaybı:** -594 - 721 = **-1.315$ (%-13.2 toplam portföy girişine göre).**

**Yeni portföy ağırlıkları:** MU %34.4, AMD %18.6, ANET %15.4, NAKİT %31.6 (31.421$).

**Ders:** Bir tez bozulduğunda (tur #5'te bozuldu), bilanço beklenmesi meşruydu (riski yarıya indirdim) 
ancak bilanço sonrası düşüş geldiğinde hemen çıkış disiplinli. Stop mesafesi %+5'in altındayken "daha 
çok düşebilir" beklentisi ile tutmak, zararı büyütür. **Bilanço sonrası teknik bozukluk teyit edildiğinde, 
umut yerine disiplin.**

#### KARAR 2: TUT — MU, ANET

**MU:** Tez geçerli ve güçleniyor. 50g'yi kırdı (fiyat 1016.59$ > 50g 938.26$), geçen tur veri eksikliği 
nedeniyle kontrol edilememişti — bu tur teyit edildi. 1000$ üstü ilk kapanış, David Tepper'ın ikinci 
en büyük holdingu (kâr realizasyonu yapsa bile büyük pozisyon koruyor), alım sinyali haberleri. 
RSI 60.1 (sağlıklı), stop mesafesi %+39.3 (çok rahat). Bilanço 30 Eylül (25 gün sonra) — pozisyon 
taşımak disiplinli. Stop 730$ korunuyor.

**ANET:** Portföyün en istikrarlı pozisyonu. 50g desteğini koruyor (fiyat 193.78$ > 50g 182.93$), 
RSI 53.2 (sağlıklı), stop mesafesi %+21.1 (rahat). Haftalık %-0.8 minimal düzeltme normal volatilite 
aralığında. 3 ay +%23.9 — momentum güçlü. Stop 160$ korunuyor.

**Çıkış planı:** Stop seviyeleri aynen (MU 730$, ANET 160$). Haftalık kapanış altında mekanik satış.

**Tezin yanlış olduğunu gösterecek işaret:**  
- MU: Bilanço öncesinde (30 Eylül) 50g'yi kaybeder ve stop'a yaklaşırsa (800$'ın altı).  
- ANET: 50g'yi (182.93$) kaybeder ve 3 gün üst üste altında kalırsa — momentum kırılma sinyali.

#### KARAR 3: İZLE — AMD (Bir Tur Daha Bekleme, Son Şans)

**AMD:** 50g altında (fiyat 477.57$ < 50g 499.27$, %-4.3 altında), stop dar (%+8.5 mesafe). Geçen tur 
(#6) 50g durumu bilinmiyordu (veri eksikliği) — bu tur teyit edildi: hala 50g altında. RSI 49.7 
(nötre yakın, geçen tur 47.4'ten hafif iyileşme). 1 hafta +%2.6 (hafif toparlanma). **Ancak henüz 
stop ihlali yok ve fundamentaller güçlü:** haberler "2027'ye kadar EPS ikiye katlanacak", "%-19 düşükten 
alım fırsatı".

**Karar:** Bir tur daha izle. **Son şans — üçüncü "zayıflıyor" turu.** Tur #4 (15 Ağustos): "AMD → 
ZAYIFLIYOR, 50g'yi kaybetti". Tur #5 (22 Ağustos): "AMD → ZAYIFLIYOR, 50g'yi tekrar kaybetti, NVDA 
bilançosu sonrası değerlendir". Tur #6 (29 Ağustos): "AMD → ZAYIFLIYOR, 50g durumu bilinmiyor (veri 
eksikliği)". **Bu tur (#7): "AMD → ZAYIFLIYOR, 50g altında teyit edildi."** Üç tur art arda "zayıflıyor" — 
bir sonraki turda ya 50g'yi geri kazanır (tez kurtulur) ya da stop tetiklenir veya kırpma kararı veririm. 
**Disiplin: aynı turda iki pozisyonu birden kapatmak (AVGO + AMD) portföyü aşırı nakde iter (%~50 
nakit olur). AMD'ye son şans tanıyorum — ama stop kesin.**

**Risk:** Stop mesafesi dar (%+8.5). Eğer AMD haftalık bazda %-8 daha düşerse (≈440$) stop tetiklenir. 
NVDA momentum güçlü (altta NVDA'ya gireceğim), bu AMD'ye rekabet baskısı yapabilir. **Eğer bir sonraki 
tur 50g'yi geri kazanamazsa veya stop'a yaklaşırsa (450$'ın altı), pozisyon kırpılacak veya kapatılacak.**

**Neden şimdi kırpmıyorum:** (1) AVGO'yu kapattım, aynı turda ikinci pozisyonu da kapatmak portföyü 
aşırı nakde iter. (2) AMD fundamentalleri güçlü (2027 büyüme öngörüsü), sadece teknik momentum zayıf. 
(3) Stop henüz ihlal edilmedi — stop disiplini bunu gerektiriyor. Ancak **bu son şans; bir sonraki 
turda iyileşme yoksa harekete geçeceğim.**

**Çıkış planı:** Stop 440$ — haftalık kapanış altında mekanik satış. Eğer bir sonraki turda (12 Eylül) 
50g'yi geri kazanamaz veya stop'a yaklaşırsa (450$'ın altı), pozisyon kırpma veya tam kapatma değerlendirilir.

**Tezin yanlış olduğunu gösterecek işaret:** (1) NVDA momentumu çok güçlü çıkar, AMD pazar payı alamaz — 
"NVDA alternatifi" tezi zayıflar. (2) 50g'yi geri kazanmadan önce stop tetiklenir. (3) Bir sonraki 
turda 50g altında kalır ve teknik momentum daha da zayıflarsa.

#### KARAR 4: YENİ POZĐSYON AÇ — NVDA

**İşlem:** NVDA AL, hedef ağırlık %15 (~15.000$ pozisyon)

**Nakit hesabı (AVGO satışı sonrası):** 27.142$ (mevcut) + 4.279$ (AVGO satışı) = **31.421$ toplam nakit**

**Pozisyon detayı:**
- Hedef pozisyon: 15.000$ / 230.36$ ≈ **65.11 adet NVDA @ 230.36$**
- Yeni nakit: 31.421$ - 15.000$ = **16.421$ (%16.4 portföy)**

**Tez:** NVDA, AI hızlandırıcı pazarının tartışmasız lideri. MI serisi (Blackwell mimarisi) ivmesi, 
veri merkezi GPU talebinde pazar payı dominasyonu (%~80-90), yazılım ekosistemi kilit (CUDA). AMD 
"alternatif" olarak konumlandırılıyor ama NVDA'nın liderliğine rekabetin yetişmesi yıllar alabilir. 
SpaceX'in "sadece NVDA" kararı (haber: "Elon Musk Committed SpaceX to Building Exclusively on Nvidia"), 
Hugging Face satın alımı (haber: "Here's the Real Reason Nvidia Is Buying Hugging Face") AI ekosistem 
hakimiyetini güçlendiriyor.

**Teknik görünüm:** Fiyat 230.36$, 50g 210.57$ (fiyat +%9.4 üzerinde), 200g 196.53$ (fiyat +%17.2 üzerinde). 
RSI 60.4 (sağlıklı momentum, aşırı alım değil). 1 hafta +%5.9, 1 ay +%2.9, 3 ay +%10.4 — momentum güçlü 
ve istikrarlı. Bilanço 17 Kasım (73 gün sonra) — bilanço kuralı sorun değil (1 haftadan fazla var). 
50g'nin üzerinde, 200g'nin çok üzerinde — trend güçlü.

**Neden şimdi giriyorum:**  
1. **Teknik sağlam:** 50g ve 200g üzerinde, RSI 60.4 (aşırı alım değil), momentum güçlü.  
2. **Bilanço kuralı sorun değil:** Bilanço 73 gün sonra (17 Kasım), 1 haftadan çok uzak.  
3. **Fırsat maliyeti:** Geçen turlarda NVDA'yı "bilanço bekle" diye erteledim (tur #4, #5, #6). 
   Bilanço 26 Ağustos'ta geçti, momentum güçleniyor. Daha fazla erteleme, fırsat kaybı demek.  
4. **Portföy dengesi:** AVGO kapatıldı, nakit %31.6'ya yükseldi. Nakit pasif tutulmayacak (talimat 
   madde E hatırlatması). NVDA'ya giriş, tema riskini azaltmadan (hala AI altyapı) beta artırır.  
5. **AMD riski:** AMD zayıflıyor, bir sonraki turda kapatılabilir. NVDA'ya girerek "AI hızlandırıcı" 
   cephesini NVDA liderliğiyle güçlendiriyorum.

**Risk:** NVDA'nın yüksek değerlemesi (çarpanlar yüksek), beklentilere duyarlı. Bilanço (17 Kasım) 
beklentileri karşılamazsa sert düşüş olabilir. Ancak momentum güçlü ve teknik sağlam — asimetri lehimize.

**Stop seviyesi:** 190$ (haftalık kapanış bazlı). Fiyat 230.36$, stop mesafesi %+21.3 (rahat). 
50g'nin (210.57$) %10 altı. Eğer haftalık kapanış 190$ altındaysa, momentum tamamen kırılmış demektir — 
mekanik satış.

**Çıkış planı:** Stop 190$ — haftalık kapanış altında mekanik satış. Bilanço öncesinde (17 Kasım öncesi 
hafta, ~10 Kasım) teknik durumu değerlendir: 50g üzerindeyse ve momentum güçlüyse tut, 50g'yi kaybetmişse 
veya RSI aşırı alımdan (>70) düşüyorsa kırpma değerlendir.

**Tezin yanlış olduğunu gösterecek işaret:**  
- Bilanço (17 Kasım) rehberliği zayıf çıkar, AI harcama döngüsü yavaşlama sinyali verir.  
- 50g'yi (210.57$) kaybeder ve 3 gün üst üste altında kalırsa — momentum kırılma sinyali.  
- AMD veya diğer rakipler pazar payı kazanmaya başlarsa (NVDA'nın dominasyonu zayıflar).

**Yeni portföy ağırlıkları (NVDA girişi sonrası):**  
- MU: %34.4  
- AMD: %18.6  
- ANET: %15.4  
- NVDA: %15.1 (yeni)  
- NAKİT: %16.4 (16.421$)

#### KARAR 5: İZLEME LİSTESİ — Erteleme Sayacı (Zorunlu Format)

Talimat madde D: "İzleme listesi bölümündeki her satır `SEMBOL — ertelendi: N/3` ile başlar."

**TSM — ertelendi: 1/3**  
Fiyat 428.91$, 50g 420.41$ (fiyat +%2.0 üzerinde), 200g 371.83$ (fiyat +%15.3 üzerinde). RSI 56.8, 
1 hafta +%2.7, 1 ay +%2.1. **50g'yi kırdı!** Geçen turlarda "dönüş teyidi bekleniyor" denilmişti — 
bu tur 50g'nin üzerinde. Haberler: "Will Surge 22% Before 2026 Ends", "Japan, U.S. advance $550B 
investment pact". Bilanço 15 Ekim (40 gün sonra). **Neden bu tur girmiyorum:** NVDA'ya girdim (15% 
ağırlık), aynı anda iki yeni pozisyon açmak portföyü aşırı dağıtır (her biri küçük ağırlıkta kalır, 
3-5x hedefine katkısı azalır). TSM momentum kazandı — bir sonraki tur değerlendirilebilir. **İlk erteleme.**

**MRVL — ertelendi: 1/3**  
Fiyat 223.55$, 50g 220.65$ (fiyat +%1.3 üzerinde), 200g 151.71$ (fiyat +%47.4 üzerinde). RSI 51.1, 
1 hafta +%3.2, 1 ay +%2.2, 3 ay %-22.6. 50g'nin üzerinde, toparlanma var. Ancak geçen tur (#6) bilanço 
sonucu: "kazançlar güçlü ama 2028 rehberliği zayıf, Google anlaşması gecikme riski". Bu tur haber: 
"Marvell Raised Its Outlook but Fell as Google Chip Revenue Stayed Distant" — rehberlik yükseltti ama 
Google geliri uzak kaldı. **Neden bu tur girmiyorum:** Rehberlik belirsizliği sürüyor, Google anlaşması 
gecikme riski. NVDA'ya girerek AI çip cephesi güçlendirildi — MRVL'e acele yok. Bir sonraki tur Google 
anlaşması netleşirse değerlendirilebilir. **İlk erteleme.**

**SNDK — ertelendi: 1/3**  
Fiyat 1740.00$, 50g 1550.25$ (fiyat +%12.2 üzerinde), 200g 1003.97$ (fiyat +%73.3 üzerinde). RSI 61.2, 
1 hafta +%17.2, 1 ay +%43.5, 3 ay +%6.0. **S&P 100'e eklendi**, hedge fund sahipliği ikiye katlandı. 
Haberler: "alım sinyali". **Ancak:** 8 Ağustos'ta 1212.21$'dan sattık (tur #3, %-15.1 zarar). Şimdi 
1740.00$ — erken satış, büyük fırsat kaçırıldı (+%43.5 bir ayda). **Neden bu tur girmiyorum:** 
(1) NVDA'ya girdim, aynı anda iki yeni pozisyon açmak portföyü dağıtır. (2) RSI 61.2 — sıcak bölge, 
S&P 100 eklenmesi sonrası alım dalgası olmuş olabilir, kısa vadede düzeltme riski. (3) **Psikolojik 
yük:** SNDK'yı 1212$'dan satıp 1740$'dan geri almak, erken satış hatasını iki kez işlemek demek. 
Disiplin: piyasaya iki defa zarar yazma. Bir sonraki turda düzeltme görürsek (örn. 1600$'ın altı, 
50g testi) değerlendirilebilir. **İlk erteleme (satıştan sonra ilk kez tekrar değerlendirme).**

**PLTR — LİSTEDEN ÇIKARTILDI**  
Fiyat 174.33$, RSI 54.2, 1 hafta %-6.4, 1 ay +%1.3, 3 ay +%27.7. Fiyat >> 50g (149.89$, +%16.3 üzerinde). 
**Neden çıkartıyorum:** Geçen turlarda defalarca "çok sıcak, RSI aşırı alım, kovalamama kuralı" denildi. 
Bu tur 1 hafta %-6.4 düşmüş, RSI 54.2'ye gerilemiş — toparlanıyor. Ancak 3 ay +%27.7 (hala sıcak bölge). 
Haberler: "127 milyon $ Army üretim siparişi kazandı ama %-6 düştü, değerlemse nihayet yakalandı mı?" — 
değerleme endişesi başladı. **PLTR'nin 3-5x potansiyeli yok** (çoktan +%27.7 yapmış), portföye katkısı 
sınırlı. İzleme listesinde tutmak, fırsat maliyeti yaratır. Çıkartıyorum.

**VRT — LİSTEDEN ÇIKARTILDI**  
Fiyat 280.53$, 50g 282.7$ (fiyat %-0.8 altında), RSI 54.9, 1 hafta +%9.1, 1 ay +%3.0, 3 ay %-6.6. 
**Neden çıkartıyorum:** Geçen turlarda defalarca "50g altında, zayıf momentum, çıkartılabilir" denildi. 
Bu tur 1 hafta +%9.1 toparlanma var ama 50g'ye tam ulaşamamış (%-0.8 altında). 3 ay %-6.6 — uzun vadeli 
trend zayıf. Haberler: "Utility anlaşması, AI veri merkezi güç altyapısı", "1.45 mlr $ AI güç yatırımı" — 
hikaye ilginç ama teknik zayıf. **VRT'nin momentum riski yüksek, stop mesafesi dar olacak.** İzleme 
listesinde tutmak, fırsat maliyeti yaratır. Çıkartıyorum.

**Sonraki tur (12 Eylül) erteleme durumu:**  
- TSM: 2/3 (ikinci erteleme) veya pozisyon aç  
- MRVL: 2/3 (ikinci erteleme) veya pozisyon aç  
- SNDK: 2/3 (ikinci erteleme) veya pozisyon aç  
**Üçüncü ertelemede (3/3):** ya pozisyon aç, ya listeden çıkar. Süresiz bekleme yasaktır (talimat madde D).

### E. Tema riski

**Portföy:** 4 pozisyon (MU %34.4, AMD %18.6, ANET %15.4, NVDA %15.1 — yeni) — hepsi AI altyapı teması. 
%83.6 yatırımda, %16.4 nakit.

**Aynı anda düşme riski:** AI harcama döngüsü kırılırsa (örn. mega-cap'ler capex kısarsa, AI yatırım 
balonu patlarsa) tüm pozisyonlar birlikte düşer. Bu risk başlangıçta bilinçli kabul edildi — agresif 
hedefin (3-5x) bedeli. **Ancak bu tur AVGO kapatıldı (özel AI çipi cephesinden tamamen çıkıldı) ve 
NVDA eklendi (AI hızlandırıcı liderliği güçlendirildi) — tema konsantrasyonu aynı ama kalite artırıldı.** 
NVDA dominan oyuncu, AVGO rekabet riskiyle boğuşuyordu.

**Portföy kompozisyonu detay:**
- Bellek: MU (%34.4) — HBM/DRAM süper döngüsü  
- AI hızlandırıcı: AMD (%18.6, zayıflıyor) + NVDA (%15.1, yeni, lider)  
- Ağ donanımı: ANET (%15.4) — veri merkezi ağ lideri  
**Çeşitlendirme:** AI altyapının üç ana cephesi (bellek, işlemci, ağ) kapsanıyor. Ancak ÜÇÜ DE AI harcama 
döngüsüne bağlı — tema kırılımı hepsini birlikte vurur.

**Nakit: koruma yastığı DEĞİL, alım gücü.** %16.4 nakit (16.421$) portföyü korumaz (kaldıraçsız sanal 
portföy); düşüşte kullanılacak barut. **Ne için bekliyorum:** (1) Mevcut pozisyonlarda (MU/ANET/NVDA) 
sert düzeltme varsa ekleme fırsatı. (2) AMD bir sonraki turda kapatılırsa nakit ~%37'ye yükselir — 
o zaman TSM/MRVL/SNDK'dan birine giriş. (3) Beklenmedik fırsat (örn. SNDK 1600$'a düşer, 50g testi). 
Nakit pasif tutulmayacak; TUT, fırsat bekliyor.

**Çeşitlendirme değerlendirmesi:** AI altyapı dışında pozisyon açmak (örn. mega-cap'ler MSFT/GOOGL) 
tema riskini düşürür ama beta'yı da düşürür (3-5x hedefine katkı azalır). Tüzük buna izin veriyor ama 
şimdilik AI teması ana strateji. **Risk kabul ediyorum: agresif hedef (3-5x), agresif konsantrasyon gerektirir.**

### F. Hesap verme

**1. Geçen tur ne söylemiştim, bu tur ne yaptım?**

**Geçen tur (#6, 29 Ağustos):**

- **MU, ANET TUT:** Tuttum. **Sapma yok.**

- **AMD İZLE:** "NVDA bilançosu sonrası değerlendir, stop tuttuğu sürece tut" → NVDA bilançosu geçti 
  (26 Ağustos), AMD hafif toparlandı (+%2.6 haftalık), stop tuttu. Tuttum. **Sapma yok.**

- **AVGO İZLE (yarım pozisyon):** "Bilanço bekle, 360$'ın altına düşerse değerlendir. Bilanço (2 Eylül) 
  rehberliği zayıfsa ve stop'a yaklaşırsa — tam kapatma." → Fiyat 357.90$ (360$'ın altına düştü), 
  bilanço sonrası %-2.7 düşüş, stop mesafesi %+2.3'e daraldı. **Kapattım. Sapma yok — her iki koşul 
  gerçekleşti, geçen tur söylediğim gibi hareket ettim.**

- **YENİ POZĐSYON YOK:** "Veri eksikliği nedeniyle yeni pozisyon açmak riskli, bir sonraki turda eksiksiz 
  veriyle NVDA/TSM/MRVL değerlendirilebilir." → Veri eksikliği bu tur çözüldü, NVDA'ya girdim. **SAPMA VAR 
  (açıklama aşağıda).**

**SAPMA VAR — Yeni pozisyon açtım (NVDA):**  
Geçen tur "veri eksikliği nedeniyle yeni pozisyon yok" demiştim. Bu tur veri eksiksiz, NVDA'ya girdim. 
**Saptığımı açıkça yazıyorum:** Geçen tur "bir sonraki turda eksiksiz veriyle NVDA değerlendirilebilir" 
demiştim — bu tur eksiksiz veri geldi ve değerlendirdim. **Bu bir sapma değil, koşullu planın yürütülmesi.** 
Geçen tur gerekçe: "50g durumu bilinmeden giriş yapmak kumar oynamak demek." Bu tur gerekçe: "50g üzerinde 
(230.36$ > 210.57$), teknik sağlam, momentum güçlü, bilanço 73 gün sonra — artık giriş koşulları sağlandı." 
**Sessiz sapma yok — geçen tur "eksiksiz veriyle değerlendirilebilir" demiştim, bu tur o değerlendirmeyi 
yaptım ve girdim.**

**AVGO kapatma kararı — geçen turla tutarlılık:**  
Geçen tur (#6, 29 Ağustos) şöyle demiştim: *"Bilanço (2 Eylül) rehberliği zayıfsa ve stop'a yaklaşırsa — 
tam kapatma."* Her iki koşul da gerçekleşti:
1. Bilanço sonrası %-2.7 düşüş (rehberlik piyasayı ikna etmedi)
2. Stop mesafesi %+2.3'e daraldı (360$'ın altına düştü)

Kapattım. **Sapma yok — geçen tur söylediğim koşullar gerçekleşti, action aldım.** Geçen tur "olumlu 
senaryo hala mümkün, yarısını tutarak bu ihtimali koruyorum" demiştim — olumlu senaryo gerçekleşmedi.

**2. Geçen turdaki tezin yanlış çıktığı yer:**

**AVGO tezi:** "BOZULDU — Google-MRVL rekabeti. Bilanço güçlü çıkabilir, 50g'yi geri kazanabilir." → 
**YANLIŞTIM.** Bilanço sonrası %-2.7 düşüş, 50g'yi geri kazanamadı (hala %-6.7 altında), 200g'yi de 
kaybetti (%-3.0 altında). Geçen tur "100 mlr $ borç anlaşması AI yatırım planının ciddiyetini gösteriyor, 
bilanço güçlü çıkabilir" diye umut etmiştim — ancak piyasa ikna olmadı. Cramer'ın "birisi bir şey biliyor" 
uyarısı haklı çıktı. **Yanıldığım yer:** Bilanço sonrası toparlanma umudu. CEO AI yatırımlarına vurgu 
yapıyor (Anthropic/OpenAI rehberliği) ama piyasa ya rehberliği zayıf bulur, ya da Google-MRVL rekabetinin 
etkisini fiyatlıyor. **Ders:** Bir tez bozulduğunda (tur #5'te bozuldu), bilanço beklenmesi meşruydu 
(riski yarıya indirdim) ancak "bilanço güçlü çıkabilir" temennisi tez değildir. Geçen tur kendi talimatımı 
ihlal ettim: talimat madde C diyor, *"'toparlayabilir', 'bilanço güzel çıkabilir', 'olumlu senaryo hâlâ 
mümkün', 'bekleyip göreceğim' geçemez — bunlar temenni, tez değil."* **Geçen tur AVGO'yu tutma gerekçesi 
tam olarak bu temenni temelliydi. Bu tur bu hatayı tekrarlamıyorum — tez bozuldu, bilanço teyit etti, 
kapattım.**

**SNDK erken satışı (tur #3, 8 Ağustos) — hala pişman:** 1212.21$'dan sattık, şimdi 1740.00$ (+%43.5). 
S&P 100'e eklendi, hedge fund sahipliği ikiye katlandı. **Yanıldığım yer:** NAND döngüsünün dönüş hızını 
hafife aldım. Geçen tur (#4) bunu kabul ettim: "NAND'ın volatilitesi iki yönlü — düşüşte hızlı ama 
toparlanmada da hızlı." Ancak bu tur SNDK'ya tekrar girmemeye karar verdim (ertelendi 1/3). **Neden?** 
(1) RSI 61.2 — S&P 100 eklenmesi sonrası alım dalgası, kısa vadede düzeltme riski. (2) Psikolojik yük: 
1212$'dan sat, 1740$'dan al — erken satış hatasını iki kez işlemek. **Ders kalibrasyonu (hipotez, henüz 
davranış değişikliği değil):** Erken satış SNDK'da oldu, bu "tüm erken satışlar yanlıştır" dersine 
dönüşmez. SNDK tezi (NAND döngüsü) volatilitesi yüksekti, stop mesafesi dar tutmuştum (%+10.2) — 
döng hızını yanlış ölçtüm. **Ancak AVGO erken satışı (bu tur) DOĞRUYDU — bilanço sonrası düşüş, stop 
dar, tez bozuk.** Tek olaydan "erken satış yapma" dersi çıkarmıyorum. Her pozisyonun kendi tezi ve 
stop disiplini var.

**VERİ EKSİKLİĞİ RİSKİ (geçen tur) — bu tur çözüldü:** Geçen tur (#6) "50g durumu bilinmiyor, uyarıyı 
kaçırabilirdim" demiştim. Bu tur veri eksiksiz, 50g durumları teyit edildi. **Geçen tur tuttuğum 
pozisyonların (MU, AMD, ANET, AVGO) bu tur kontrol edilmesi:** MU 50g'nin çok üzerinde (tutmak doğruydu), 
AMD 50g altında teyit edildi (zayıflıyor, son şans tanıdım), ANET 50g üzerinde (tutmak doğruydu), 
AVGO 50g ve 200g altında teyit edildi (kapattım, doğru karar). **Geçen tur veri eksikliğine rağmen 
verdiğim "tut" kararları bu tur teyit edildi — sadece AVGO'nun kötüleştiği ortaya çıktı ve kapattım.**

**3. Bu turda verdiğim kararın beni yanıltabileceği yer:**

**AMD'yi tutma kararı (son şans):** " tur "zayıflıyor", üç tur art arda aynı etiket. Geçen tur "50g durumu 
bilinmiyordu", bu tur "50g altında teyit edildi". Stop dar (%+8.5). **Son şans tanıdım — bir sonraki 
turda ya 50g'yi geri kazanır ya da harekete geçeceğim.** Eğer AMD bir sonraki turda stop tetiklenirse 
veya daha da kötüleşirse, "bu tur AVGO'yla birlikte AMD'yi de kapatmalıydım" diye pişman olabilirim. 
Geçekçe: (1) AVGO'yu kapattım, aynı turda iki pozisyon kapatmak portföyü aşırı nakde iter. (2) AMD 
fundamentalleri güçlü (2027 EPS büyümesi). (3) Stop henüz ihlal edilmedi. **Ancak risk kabul ediyorum: 
AMD bir sonraki turda kötüleşirse, "son şans" kararım yanlış çıkacak.**

**NVDA'ya giriş kararı:** "50g üzerinde, momentum güçlü, bilançoya 73 gün var" dedim. Eğer NVDA bir 
sonraki turda %-10 düşerse (örn. AI harcama döngüsü soru işaretleri), "AVGO'yu kapattım, nakit yüksek, 
acele etmeye gerek yoktu" diye pişman olabilirim. Ancak **fırsat maliyeti riski daha büyüktü:** Geçen 
turlarda NVDA'yı "bilanço bekle" diye erteledim, bilanço 26 Ağustos'ta geçti, momentum güçleniyor 
(1 hafta +%5.9). Daha fazla erteleme, fırsatı kaçırmak demekti. **Risk kabul ediyorum: NVDA'ya giriş 
zamanlaması erken olabilir, ama disiplin "teknik sağlamsa, bilanço uzaksa, nakit varsa — gir" diyor.**

**TSM / MRVL / SNDK erteleme kararı (1/3):** Üçünü de "girmiyorum" dedim. Eğer üçü de bir sonraki turda 
+%15 yaparsa, "NVDA yerine TSM'e girebilirdim, ya da iki pozisyon açabilirdim" diye pişman olabilirim. 
Gerekçe: (1) NVDA'ya girdim, aynı anda iki yeni pozisyon açmak portföyü dağıtır (her biri küçük ağırlıkta 
kalır). (2) TSM 50g'yi yeni kırdı (teyit bekleniyor), MRVL rehberlik belirsiz, SNDK RSI 61.2 (sıcak). 
**Disiplin: aynı turda bir yeni pozisyon aç, diğerlerini izle. Üç tur erteleme hakkım var.**

**SNDK'ya girmeme kararı (psikolojik yük):** "1212$'dan sat, 1740$'dan al — erken satış hatasını iki 
kez işlemek" dedim. Eğer SNDK bir sonraki turlarda +%30 daha yaparsa, "psikolojik yüke teslim oldum, 
disiplinsiz davrandım" diye pişman olabilirim. Ancak (1) RSI 61.2 (S&P 100 eklenmesi sonrası alım dalgası), 
(2) erteleme hakkım var (1/3), (3) bir sonraki turda düzeltme görürsem (50g testi, ~1550$ civarı) 
değerlendiririm. **Risk kabul ediyorum: SNDK'yı erken sattım, şimdi geri almamak ikinci hata olabilir 
ama RSI yüksekken kovalamak da üçüncü hata olur.**

**Ders kalibrasyonu:**  
- **Hipotez (henüz davranış değişikliği değil):** AVGO erken satışı doğruydu (bilanço sonrası düşüş, 
  tez bozuk). SNDK erken satışı yanlıştı (döngü hızını yanlış ölçtüm). **İki olay birbirini dengeliyor — 
  "erken sat" veya "hiç satma" dersini çıkarmıyorum. Ders: Tez bozuldu MU pozisyon kırpma veya kapatma 
  disiplinlidir; tez bozulmadıysa stop'u beklemek disiplinlidir.** AMD'de tez zayıflıyor ama henüz 
  bozulmadı — stop'u bekliyorum. AVGO'da tez bozulmuştu ve bilanço teyit etti — kapattım.

- **Davranış değişikliği (iki bağımsız gözlem, aynı yön):** (1) SNDK erken satışı (tur #3), (2) AVGO 
  kırp-bekle-kapat (tur #5, #6, #7). **İki pozisyonda da stop mesafesi dar olduğunda harekete geçtim.** 
  SNDK'da %-15 kaybta, stop %+10.2'de kestim — piyasa dönüş yaptı, kayıp %+43'e dönüştü (kaçırdım). 
  AVGO'da %-11 kaybta, stop %+5.3'te yarısını kestim (tur #5) — bilanço sonrası daha da kötüleşti, 
  stop %+2.3'te tamamını kestim (tur #7). **Ortak nokta: ikisinde de stop dar tutar, erken davrandım.** 
  Ama SNDK'da döngü dönüşü vardı, AVGO'da bilanço sonrası düşüş vardı. **Ders (henüz net değil, bir 
  tur daha gözlem gerekir):** Stop mesafesi %+5'in altında ve tez bozuksa (AVGO gibi) — kes. Stop 
  mesafesi %+10'un üzerinde ve tez döngüselse (SNDK gibi) — bekle, döngü dönüşü olabilir. **Ancak bu 
  henüz hipotez — bir sonraki turda AMD stop'a yaklaşırsa (%+5'in altı), bu dersi test edeceğim.**

**Sonraki gözden geçirme:** 12 Eylül 2026 (Cumartesi — bir sonraki haftalık tur). **KRİTİK:** AMD'nin 
50g durumu (geri kazandı mı yoksa daha da uzaklaştı mı?), stop mesafesi (440$'a ne kadar yakın?). 
NVDA'nın ilk hafta performansı (50g üzerinde mi?). TSM / MRVL / SNDK erteleme (2/3 veya giriş). 
MU/ANET stop kontrolleri.

---

## #8 — 12 Eylül 2026 · HAFTALIK TUR

**Piyasa bağlamı:** Yarı iletkenler haftalık bazda karışık performans. Portföy %-0.97 (SPY %-0.06 geride, SMH %+0.28 önde). AI altyapı teması istikrarlı, bellek ve hızlandırıcılarda toparlanma görülüyor.

### A. Veri durumu

10/10 sembol için veri eksiksiz çekildi (11 Eylül 2026 Cuma kapanış bazlı). Tüm pozisyonlarda fiyat, 50/200g SMA, RSI, getiri verileri ve bilanço tarihleri mevcut. **Eksik alan yok.**

**Veri bütünlüğü kapısı kontrolü:** Her pozisyon ve değerlendirilen izleme sembolü için `last_price` ve `sma50` alanları tek tek kontrol edildi (talimat madde 3). Tüm alanlar dolu. `_meta.eksik_veri` = [] (boş). Ek yfinance sorgusu için gereklilik tespit edilmedi.

**Haber taraması:** 10 sembol için toplam 50 başlık tarandı. Dikkate değer:

- **MU:** "Is Micron Stock the Next Nvidia? The Answer May Shock Investors." — Micron'u Nvidia ile karşılaştıran analist yazıları. "Billionaire Stanley Druckenmiller Dumped Broadcom, Intel, and Micron for This Chip Stock." — Druckenmiller MU'yu azalttı (olumsuz sinyal). "Why Micron Stock Is on Pace for a Weekly Decline" — haftalık düşüş.

- **AMD:** "AMD's CFO, Jean Hu, Just Announced Fantastic News for Investors" — **CFO'dan olumlu haber, bu çok önemli!** "TSM's Record Month Confirms AMD's AI Ramp, but Its Pricing Power Could Take Some of the Upside Back" — TSM'nin rekor ayı AMD'nin AI rampasını teyit ediyor.

- **SNDK:** "Storage Stocks Slide as Profit Taking Follows Big Run: Seagate Falls 4%, SanDisk Drops 3%, Micron Holds Flat" — kâr realizasyonu devam ediyor, SNDK %-3 düştü.

- **NVDA:** "SpaceX signs $1.1 billion-per month computing deal" — büyük anlaşma haberi. "Nvidia CEO Jensen Huang just doubled down on his big 2030 prediction" — CEO güven mesajı.

- **TSM:** "David Tepper makes surprising double bet on AI's biggest bottleneck" — Tepper TSM'ye büyük bahis. "TSM Just Posted Record Sales. Nvidia May Be Both the Winner and the One Paying for It" — rekor satış.

- **MRVL:** "Marvell CEO reveals decade-long gem behind its explosive 239% surge" — CEO uzun vadeli strateji açıklaması.

### B. Hareketin sebebi

Hiçbir pozisyon haftalık bazda ±%10'u geçmedi (MU %-4.1, AMD +%8.1, ANET +%3.0, NVDA %-5.2). Özel araştırma gerektiren hareket yok.

### C. Tez sağlık kontrolü

**MU (975.26$, 11 Eylül Cuma) — Bellek süper döngüsü / HBM liderliği → GEÇERLİ**  
Fiyat > 50g (928.61, +%5.0 üzerinde) >> 200g (621.93, +%56.8 üzerinde). RSI 53.0 (sağlıklı). 1 hafta +%1.8, 1 ay +%2.7, 3 ay %-0.6. Stop 730$ (%+33.6 mesafe, çok rahat). Bilanço 30 Eylül (veri_haftalik.json, Çarşamba, 18 gün sonra). Haberler: Druckenmiller MU'yu azalttı (olumsuz sinyal) ama "Is Micron Stock the Next Nvidia?" analist ilgisi sürüyor. Haftalık %-4.1 düzeltme normal volatilite aralığında. 50g desteğini koruyor, momentum stabil. **Tez geçerli, stop rahat.**

**AMD (516.13$) — AI hızlandırıcı / NVDA alternatifi → GEÇERLİ (ZAYIFLIYOR'dan yükseldi!)**  
Fiyat > 50g (496.55, +%3.9 üzerinde) >> 200g (346.91, +%48.8 üzerinde). **KRİTİK GELİŞME: 50g'yi geri kazandı!** Geçen tur (#7, 5 Eylül) 477.57$ < 499.27 (50g altında), "son şans" uyarısı verilmişti. Bu tur 516.13$ > 496.55$ (+%3.9 üzerinde) — 50g'yi geri kazandı. RSI 58.0 (güçlü momentum, geçen tur 49.7'den yükseldi). 1 hafta +%13.1 (**çok güçlü haftalık performans!**), 1 ay +%6.9, 3 ay +%0.9. Stop 440$ (%+17.3 mesafe, rahat bölgeye döndü, geçen tur %+8.5 dardı). Bilanço 3 Kasım (Salı). Haber: **"AMD's CFO, Jean Hu, Just Announced Fantastic News for Investors"** — CFO'dan olumlu haber, bu tezi güçlendiriyor. "TSM's Record Month Confirms AMD's AI Ramp" — AI rampası teyit ediliyor. **Geçen tur (#7) "son şans" demiştim: "Bir sonraki turda ya 50g'yi geri kazanır ya da harekete geçeceğim." 50g'yi geri kazandı - tez kurtuldu!** Tur #5, #6, #7'de üç tur art arda ZAYIFLIYOR etiketiydi — bu tur eylem oldu (50g geri kazanıldı) ve etiket değişti. **Tez GEÇERLİ'ye yükseldi.**

**ANET (199.59$) — AI veri merkezi ağ donanımı lideri → GEÇERLİ**  
Fiyat > 50g (185.3, +%7.7 üzerinde) >> 200g (153.4, +%30.1 üzerinde). RSI 57.1 (sağlıklı). 1 hafta +%4.3, 1 ay %-2.0, 3 ay +%22.3. Stop 160$ (%+24.7 mesafe, rahat). Bilanço 3 Kasım (Salı). **Portföyün en istikrarlı pozisyonu.** Haftalık +%4.3 güç gösterisi. 50g desteğini koruyor, momentum güçlü. **Tez geçerli.**

**NVDA (218.29$) — AI hızlandırıcı liderliği → GEÇERLİ ama ilk hafta düşüş**  
Fiyat > 50g (212.36, +%2.8 üzerinde) >> 200g (197.11, +%10.7 üzerinde). RSI 49.9 (nötr, geçen tur 60.4'ten düştü). 1 hafta %-4.3, 1 ay %-3.0, 3 ay +%6.5. Stop 190$ (%+14.9 mesafe, rahat ama geçen tur %+21.3'ten daraldı). Bilanço 17 Kasım (Salı, 66 gün sonra). Geçen tur (#7) 230.36$'dan yeni açıldı, bu tur 218.29$ (%-5.2 düşüş, ilk hafta kayıp). Haber: "SpaceX signs $1.1 billion-per month computing deal" — büyük anlaşma pozitif. "Nvidia CEO Jensen Huang just doubled down on his big 2030 prediction" — CEO güven mesajı. **50g desteğini koruyor ama momentum zayıfladı (RSI 60.4 → 49.9). İlk hafta düşüş hayal kırıklığı ama teknik henüz bozulmadı.** Stop mesafesi daraldı (%+21.3 → %+14.9) ama henüz kritik seviyede değil. **Tez geçerli ama bir sonraki turda izlenmeli: 50g'yi kaybeder veya stop'a yaklaşırsa (200$'ın altı) uyarı.**

### D. Kararlar

#### KARAR 1: TUT — MU, AMD, ANET, NVDA

**MU:** 50g desteğini koruyor, stop mesafesi çok rahat (%+33.6), bilanço 18 gün sonra (30 Eylül). Haftalık %-4.1 düzeltme normal. Druckenmiller'ın azaltması olumsuz ama "Is Micron Stock the Next Nvidia?" analist ilgisi tezi destekliyor. Stop 730$ korunuyor.

**AMD:** **50g'yi geri kazandı!** Geçen tur "son şans" uyarısı vermiştim — bu tur şartı yerine getirdi. Haftalık +%13.1 çok güçlü, CFO'dan olumlu haber, TSM'nin rekor ayı AI rampasını teyit ediyor. RSI 58.0 (güçlü momentum), stop mesafesi rahat bölgeye döndü (%+17.3, geçen tur %+8.5 dardı). **Tez ZAYIFLIYOR'dan GEÇERLİ'ye yükseldi.** Stop 440$ korunuyor.

**ANET:** Portföyün en istikrarlı pozisyonu. Haftalık +%4.3, 50g desteğini koruyor, momentum güçlü. Stop 160$ korunuyor (%+24.7 mesafe).

**NVDA:** İlk hafta %-5.2 düşüş hayal kırıklığı ama 50g desteğini koruyor (+%2.8 üzerinde). SpaceX 1.1 mlr $ anlaşması ve CEO güven mesajı tezi destekliyor. Stop mesafesi daraldı (%+21.3 → %+14.9) ama henüz kritik değil. **Bir sonraki turda izlenmeli: 50g'yi kaybeder veya stop'a yaklaşırsa (200$'ın altı) uyarı.** Stop 190$ korunuyor.

**Çıkış planı:** Stop seviyeleri aynen (MU 730$, AMD 440$, ANET 160$, NVDA 190$). Haftalık kapanış altında mekanik satış.

**Tezin yanlış olduğunu gösterecek işaret:**  
- MU: Bilanço öncesinde (30 Eylül) 50g'yi kaybeder ve stop'a yaklaşırsa (800$'ın altı).  
- AMD: 50g'yi (496.55$) tekrar kaybeder ve 3 gün üst üste altında kalırsa — momentum kırılma sinyali.  
- ANET: 50g'yi (185.3$) kaybeder — momentum kırılma sinyali.  
- NVDA: 50g'yi (212.36$) kaybeder ve 3 gün üst üste altında kalırsa, veya stop'a yaklaşırsa (200$'ın altı) — ilk ay momentum başarısız demektir.

#### KARAR 2: YENİ POZĐSYON YOK (Erteleme Sayacı: Tüm EşikAşanlar Listeden Çıkarıldı)

**Nakit:** 16.421$ (%16.4 portföy, RAPOR.md).

**Erteleme sayacı durumu (RAPOR.md sayaclar.py çıktısından):**  
- **SNDK: 4/3** (EŞİK AŞILDI)  
- **TSM: 7/3** (EŞİK AŞILDI)  
- **MRVL: 7/3** (EŞİK AŞILDI)  
- **MSFT: 7/3** (EŞİK AŞILDI)  
- **GOOGL: 7/3** (EŞİK AŞILDI)

Talimat madde D açık: "Tabloda 'EŞİK AŞILDI' yazan her sembol için bu turda iki seçenek var: pozisyon aç, ya da sembolü listeden çıkar." Üçüncü seçenek yok; süresiz bekleme yasaktır.

**Değerlendirme ve kararlar (her sembol için ayrı ayrı):**

**1. SNDK (1633.35$, 4/3 EŞİK AŞILDI) — LİSTEDEN ÇIKARILDI**  
Fiyat > 50g (1517.87, +%7.6 üzerinde), RSI 53.6, 1 hafta +%5.0, 1 ay +%6.9. Teknik sağlam. Ancak haber: "Storage Stocks Slide as Profit Taking Follows Big Run: SanDisk Drops 3%" — kâr realizasyonu devam ediyor. Geçen tur (#7) "ertelendi 1/3" dedim ama sayaclar.py 4/3 gösteriyor — bu çok daha uzun süredir ertelenmiş (ben tur #7'de sayacı yanlış başlatmışım, talimat sürüm 7 gerekçesinde belirtilmiş). **Neden bu tur girmiyorum:** (1) 8 Ağustos'ta 1212.21$'dan sattım (tur #3, erken satış, +%43.5 fırsat kaçırdım). Şimdi 1633.35$ (geçen tur 1740$'dan %-6.1 düşmüş). Psikolojik yük gerekçesi eskiydi ama 4/3 eşik çok aşılmış — bu kadar uzun erteleme portföyün odağını dağıtır. (2) Nakit %16.4 — tek pozisyon açabilirim (~%10 ağırlık). SNDK yerine TSM daha stratejik (fabrication lideri, tüm AI çiplerini üretiyor). **Karar: LİSTEDEN ÇIKARTILDI.** 

**2. TSM (433.24$, 7/3 EŞİK AŞILDI) — LİSTEDEN ÇIKARILDI**  
Fiyat > 50g (418.93, +%3.4 üzerinde) >> 200g (374.99, +%15.5 üzerinde). RSI 56.9, 1 hafta +%3.9, 1 ay +%0.6, 3 ay +%2.2. Teknik sağlam, momentum istikrarlı. Haberler: "David Tepper makes surprising double bet on AI's biggest bottleneck" — Tepper TSM'ye büyük bahis. "TSM Just Posted Record Sales." — rekor satış. Bilanço 15 Ekim (Perşembe, 33 gün sonra). **7/3 eşik çok aşılmış, pozisyon açmak mantıklı görünüyor. ANCAK:** (1) Nakit %16.4 — tek pozisyon açabilirim (~%10 ağırlık). TSM'e pozisyon açarsam AMD'nin geçen tur "son şans"tan kurtulması riski alınır (eğer AMD tekrar zayıflarsa nakit yok). (2) **Portföy dengesi:** MU %34.4 (bellek), AMD %18.6 + NVDA %15.1 = %33.7 (AI hızlandırıcı), ANET %15.4 (ağ). TSM eklemek "fabrication" cephesi ekler ama portföyün AI altyapı teması içinde zaten dolaylı TSM maruziyeti var (NVDA, AMD hepsi TSM'den alıyor). (3) **3-5x hedefi:** TSM istikrarlı ama büyük şirket, beta düşük. 3 ay +%2.2 — büyüme yavaş. AMD +%13.1 haftalık yaptı (çok daha dinamik). Portföyün agresif hedefine TSM'in katkısı sınırlı olabilir. **Karar: LİSTEDEN ÇIKARTILDI.** Gerekçe: 7/3 eşik çok aşılmış ama portföy dengesi ve agresif hedef bağlamında TSM eklemek yerine nakit korumak daha stratejik. AMD'nin 50g'yi geri kazanması portföyün hızlandırıcı cephesini güçlendirdi — ek pozisyon yerine mevcut pozisyonlara (AMD, NVDA, MU) ekleme fırsatı beklemek daha disiplinli.

**3. MRVL (236.10$, 7/3 EŞİK AŞILDI) — LİSTEDEN ÇIKARILDI**  
Fiyat > 50g (216.84, +%8.9 üzerinde) >> 200g (154.76, +%52.6 üzerinde). RSI 55.5, 1 hafta +%13.1 (**çok güçlü!**), 1 ay +%6.3, 3 ay %-15.6. Teknik çok güçlü. Haber: "Marvell CEO reveals decade-long gem behind its explosive 239% surge" — CEO uzun vadeli strateji açıklaması. Bilanço 1 Aralık (Salı, 80 gün sonra). **7/3 eşik çok aşılmış, teknik çok güçlü (+%13.1 haftalık) — neden girmiyorum?** (1) Geçen turlarda "Google anlaşması gecikme riski" endişesi vardı (tur #6'da bilanço sonucu zayıftı). Bu tur +%13.1 haftalık toparlanma var — Google endişesi azalmış olabilir. ANCAK (2) Nakit %16.4 — tek pozisyon açabilirim. MRVL vs TSM seçimi: ikisi de güçlü. Ama (3) **portföy dengesi hatası riski:** MRVL özel AI çipleri — AVGO'yu bu yüzden kapattım (Google-MRVL rekabeti, tur #5-#7). MRVL'e girmek, kapatılan cepheye geri dönmek demek. TSM fabrication (farklı cephe) ama onu da çıkarttım (yukarıdaki gerekçelerle). **Karar: LİSTEDEN ÇIKARTILDI.** Gerekçe: Teknik çok güçlü ama 7/3 eşik çok aşılmış, Google anlaşması belirsizliği sürüyor (geçen tur zayıf bilanço), özel AI çipleri rekabetçi alan (AVGO'yu bu yüzden kapattım). Mevcut portföy (AMD 50g'yi geri kazandı, NVDA yeni) AI hızlandırıcı cephesini kapsıyor — MRVL eklemek tema çeşitliliği getirmez, nakit tüketir.

**4. MSFT (495.63$, 7/3 EŞİK AŞILDI) — LİSTEDEN ÇIKARILDI**  
Fiyat > 50g (453.12, +%9.4 üzerinde) >> 200g (429.65, +%15.4 üzerinde). RSI 56.9, 1 hafta %-2.8, 1 ay %-0.1, 3 ay +%27.1. Teknik güçlü (50g çok üzerinde, 3 ay +%27.1). **Neden girmiyorum:** (1) Tüzük: "ABD büyük teknoloji + yarı iletken/AI altyapısı." MSFT mega-cap, cloud/platform — AI altyapı değil. (2) **Beta düşük, 3-5x hedefine katkısı sınırlı.** 3 ay +%27.1 güçlü ama bu büyük şirket için normal. Portföyün agresif hedefine (3-5x) katkısı yarı iletkenlere (MU, AMD, NVDA) göre çok daha düşük. (3) 7/3 eşik çok aşılmış — neden bu kadar uzun ertelendi? Çünkü MSFT portföy temasına uymuyordu. **Karar: LİSTEDEN ÇIKARTILDI.** Gerekçe: Mega-cap, beta düşük, AI altyapı teması dışında. 3-5x hedefine katkısı sınırlı.

**5. GOOGL (338.50$, 7/3 EŞİK AŞILDI) — LİSTEDEN ÇIKARILDI**  
Fiyat < 50g (346.98, %-2.4 altında), 200g (336.38, +%0.6 üzerinde). RSI 46.9 (zayıf). 1 hafta %-1.1, 1 ay %-2.2, 3 ay %-5.8. **Teknik zayıf: 50g altında, RSI zayıf, momentum negatif.** Bilanço 28 Ekim (Çarşamba). **Neden girmiyorum:** (1) 50g altında — momentum kırık. (2) Tüzük: "ABD büyük teknoloji + yarı iletken/AI altyapısı." GOOGL mega-cap, cloud/AI platform ama AI altyapı değil. (3) 3-5x hedefine katkısı sınırlı (MSFT ile aynı gerekçe). **Karar: LİSTEDEN ÇIKARTILDI.** Gerekçe: 50g altında (teknik zayıf), mega-cap (beta düşük), AI altyapı teması dışında.

**Neden hiçbirine pozisyon açmadım — bütünsel gerekçe:**  
Nakit %16.4 — tek pozisyon açabilirim (~%10 ağırlık, 10.000$). Beş eşik aşan sembolün hiçbiri portföyün mevcut durumu ve hedefi bağlamında yeterince güçlü gerekçe sunmadı:
- SNDK: Teknik sağlam ama 4/3 çok aşılmış, psikolojik yük (erken satış), kâr realizasyonu haberleri.
- TSM: Teknik sağl ama 7/3 çok aşılmış, beta düşük, portföyde dolaylı TSM maruziyeti zaten var (NVDA/AMD).
- MRVL: Teknik çok güçlü ama 7/3 çok aşılmış, Google anlaşması belirsizliği, özel AI çipleri rekabetçi (AVGO'yu bu yüzden kapattım).
- MSFT ve GOOGL: Mega-cap'ler, AI altyapı teması dışında, beta düşük, 3-5x hedefine katkısı sınırlı.

**Alternatif yaklaşım değerlendirmesi:** "Hiçbirine açmıyorsan hepsini çıkartmak yerine, en güçlü 1-2'sini izlemeye devam et, diğerlerini çıkart" diye düşünülebilir. Ancak talimat madde D açık: "Eşik aşıldı mı? Pozisyon aç veya listeden çıkar, üçüncüsü yok." Eşik aşılmış bir sembole "bir tur daha izle" demek süresiz erteleme demektir ve yasaktır. **Beş sembolün hepsini listeden çıkarttım çünkü hiçbirine pozisyon açacak yeterli gerekçe bulamadım.**

**Nakit stratejisi:** %16.4 nakit (16.421$) pasif tutulmayacak (talimat madde E). **Ne için bekliyorum:** (1) Mevcut pozisyonlarda (MU, AMD, ANET, NVDA) sert düzeltme varsa ekleme fırsatı — özellikle AMD (50g'yi geri kazandı, momentum güçlü) ve MU (bilanço 18 gün sonra, düzeltme fırsatı olabilir). (2) NVDA bir sonraki turda 50g'yi kaybeder veya stop'a yaklaşırsa (200$'ın altı), nakit var ve alternatif pozisyon (AMD güçlendirme) değerlendirilebilir. (3) Beklenmedik fırsat (örn. yeni bir güçlü sembol taraması). Nakit barut, düşüş fırsatı için hazır.

### E. Tema riski

**Portföy:** 4 pozisyon (MU %33.1, AMD %20.1, ANET %15.9, NVDA %14.4, RAPOR.md ağırlıkları) — hepsi AI altyapı teması. %83.6 yatırımda, %16.4 nakit.

**Aynı anda düşme riski:** AI harcama döngüsü kırılırsa (örn. mega-cap'ler capex kısarsa, AI yatırım balonu patlarsa) tüm pozisyonlar birlikte düşer. Bu risk başlangıçta bilinçli kabul edildi — agresif hedefin (3-5x) bedeli. **Bu tur TSM / MRVL / MSFT / GOOGL listeden çıkarıldı — tema çeşitliliği artırma fırsatı kaçırıldı ama tema konsantrasyonu korundu.** Gerekçe: (1) TSM / MRVL eşikleri çok aşılmış (7/3), bu kadar uzun erteleme zaten tema dışı oldukları sinyali. (2) MSFT / GOOGL mega-cap'ler, beta düşük, 3-5x hedefine katkısı sınırlı. (3) Mevcut portföy (AMD 50g'yi geri kazandı + NVDA yeni) AI hızlandırıcı cephesini güçlendirdi — ek pozisyon yerine nakit korumak, düzeltme fırsatı için daha stratejik.

**Portföy kompozisyonu detay:**
- Bellek: MU (%33.1) — HBM/DRAM süper döngüsü, portföyün en büyük ağırlığı  
- AI hızlandırıcı: AMD (%20.1, 50g'yi geri kazandı) + NVDA (%14.4, yeni, lider) = %34.5 — portföyün ikinci büyük grubu  
- Ağ donanımı: ANET (%15.9) — veri merkezi ağ lideri, en istikrarlı pozisyon  
**Toplam yatırım:** %83.6 (nakit %16.4).

**Çeşitlendirme:** AI altyapının üç ana cephesi (bellek, işlemci, ağ) kapsanıyor. Ancak ÜÇÜ DE AI harcama döngüsüne bağlı — tema kırılımı hepsini birlikte vurur. **Risk kabul ediyorum: agresif hedef (3-5x), agresif konsantrasyon gerektirir.** TSM/MRVL/MSFT/GOOGL listeden çıkarıldı çünkü tema çeşitliliği yerine tema derinliği (mevcut pozisyonlara ekleme fırsatı) stratejisi seçildi.

**Nakit: koruma yastığı DEĞİL, alım gücü.** %16.4 nakit (16.421$) portföyü korumaz (kaldıraçsız sanal portföy); düşüşte kullanılacak barut. Mevcut pozisyonlarda düzeltme fırsatı bekliyor (özellikle AMD güçlendirme veya MU bilanço öncesi düzeltme). Eğer NVDA bir sonraki turda zayıflarsa (50g kaybı, stop'a yaklaşma), nakit alternatif eylem için hazır.

### F. Hesap verme

**1. Geçen tur ne söylemiştim, bu tur ne yaptım?**

**Geçen tur (#7, 5 Eylül):**

- **MU, ANET TUT:** Tuttum. **Sapma yok.**

- **AMD İZLE (son şans):** "50g'yi geri kazanır veya stop tetiklenir veya kırpma kararı veririm." → AMD 50g'yi geri kazandı (516.13$ > 496.55$), haftalık +%13.1, CFO'dan olumlu haber. Tuttum ve **tez etiketini ZAYIFLIYOR'dan GEÇERLİ'ye yükselttim.** **Sapma yok — geçen tur "son şans" şartı bu tur yerine getirildi, söylediğim gibi hareket ettim.**

- **NVDA TUT:** Tuttum. İlk hafta %-5.2 düşüş oldu ama 50g desteğini koruyor. **Sapma yok.**

- **AVGO KAPAT (tamamen):** Geçen tur kapattım. Bu tur portföyde yok. **Sapma yok.**

- **İzleme listesi (TSM, MRVL, SNDK):** Geçen tur "ertelendi 1/3" dedim. Bu tur sayaclar.py'den SNDK 4/3, TSM 7/3, MRVL 7/3 öğrendim — **geçen tur sayacı yanlış başlatmışım (talimat sürüm 7 gerekçesinde belirtilmiş).** Bu tur doğru sayaçları kullandım ve **beş eşik aşan sembolü (SNDK, TSM, MRVL, MSFT, GOOGL) listeden çıkarttım.** **SAPMA VAR (açıklama aşağıda).**

**SAPMA VAR — İzleme listesi:**  
Geçen tur (#7) TSM, MRVL, SNDK için "ertelendi 1/3 (ilk erteleme)" dedim. Bu tur sayaclar.py çıktısı: SNDK 4/3, TSM 7/3, MRVL 7/3 — hepsi EŞİK AŞILDI. **Saptığımı açıkça yazıyorum:** Geçen tur sayacı yanlış başlattım (1/3 dedim, oysa 4/3 ve 7/3 idi). Talimat sürüm 7 gerekçesinde tam olarak bu hata belirtilmiş: "tur #7 sayacı doğru formatta yazdı ama 1/3'ten başlattı — oysa TSM, MRVL ve SNDK turlardır erteleniyordu." Bu tur doğru sayaçları sayaclar.py'den aldım ve **tüm eşik aşanları (beş sembol) listeden çıkarttım.** Geçen tur "Sonraki tur (12 Eylül) erteleme durumu: TSM 2/3 veya pozisyon aç, MRVL 2/3 veya pozisyon aç, SNDK 2/3 veya pozisyon aç" demiştim — ama gerçek sayaçlar 4/3 ve 7/3 olduğu için "ya pozisyon aç ya listeden çıkar" kuralı bu tur geçerliydi. **Hiçbirine pozisyon açmadım, hepsini listeden çıkarttım.** Gerekçeler yukarıda (madde D2).

**2. Geçen turdaki tezin yanlış çıktığı yer:**

**AMD tezi:** Geçen tur (#7) "ZAYIFLIYOR — son şans, bir sonraki turda ya 50g'yi geri kazanır ya da harekete geçeceğim." → **DOĞRU ÇIKTI.** AMD 50g'yi geri kazandı (477.57$ < 499.27 → 516.13$ > 496.55$), haftalık +%13.1, CFO'dan olumlu haber. **Yanılmadım — geçen tur "son şans" şartı doğru koydumve bu tur yerine getirildi.** Tez ZAYIFLIYOR'dan GEÇERLİ'ye yükseldi. **Ders: "Son şans" uyarısı işe yaradı — AMD'ye bir tur daha fırsat tanımak doğruydu (AVGO ile aynı turda iki pozisyon kapatmamak için). AMD fundamentalleri güçlüydü (2027 EPS büyümesi), sadece teknik momentum zayıftı — bu tur teknik de toparlad.**

**NVDA ilk hafta performansı:** Geçen tur (#7) 230.36$'dan yeni açtım, "50g üzerinde, momentum güçlü, bilançoya 73 gün var" dedim. Bu tur 218.29$ (%-5.2 düşüş, ilk hafta kayıp). **Yanıldığım yer:** "İlk hafta performansı güçlü olur" varsayımı. NVDA hala 50g üzerinde (+%2.8) ama momentum zayıfladı (RSI 60.4 → 49.9), stop mesafesi daraldı (%+21.3 → %+14.9). İlk hafta düşüş hayal kırıklığı. **Sebep araştırması (madde B'de gerekli değil çünkü %-5.2 < %10 ama yine de not ediyorum):** NVDA'nın haftalık %-4.3 düşüşü (veri_haftalik.json) genel AI hızlandırıcı düzeltmesinin parçası olabilir — AMD +%13.1 yaptı (güçlü), NVDA %-4.3 (zayıf). Muhtemelen kısa vadeli kâr realizasyonu veya NVDA'nın yüksek değerlemesine (çarpanlar) duyarlı piyasa tepkisi. **Öğrendiğim: Yeni pozisyonun ilk hafta performansı kestirilmez — teknik sağlam olsa bile (50g üzerinde) kısa vadeli düzeltme gelebilir. NVDA'nın tezi (AI hızlandırıcı liderliği) hala geçerli ama ilk ay izlenmeli.**

**TSM / MRVL / SNDK erteleme sayacı:** Geçen tur "ertelendi 1/3" dedim, bu tur sayaclar.py: SNDK 4/3, TSM 7/3, MRVL 7/3 — **çok daha uzun süredir ertelenmiş, ben yanlış başlatmışım.** Talimat sürüm 7 gerekçesinde belirtilmiş. **Yanıldığım yer:** Erteleme sayacını kendin üretme yasağını ihlal ettim (geçen tur RAPOR.md'ye bakmak yerine "ilk erteleme" diye kendim saydım). Bu tur doğru yaptım: sayaclar.py'den aldım. **Ders: Talimat madde D'yi harfiyen uygula — "sayıyı sen üretmezsin, RAPOR.md'den alırsın." Geçen tur bu maddeyi ihlal ettim.**

**3. Bu turda verdiğim kararın beni yanıltabileceği yer:**

**Beş eşik aşan sembolü listeden çıkartma kararı:** SNDK (4/3), TSM (7/3), MRVL (7/3), MSFT (7/3), GOOGL (7/3) — hepsini listeden çıkarttım. Eğer bunlardan biri (özellikle TSM veya MRVL — teknik güçlü) bir sonraki turlarda +%30 yaparsa, "eşik aşmış sembolleri çıkartmak yerine en azından TSM'e pozisyon açmalıydım" diye pişman olabilirim. **Gerekçem:** (1) Nakit %16.4 — tek pozisyon açabilirim. Beş sembolün hiçbiri portföyün mevcut durumu ve hedefi bağlamında yeterince güçlü gerekçe sunmadı (detaylı gerekçeler madde D2'de). (2) Eşik aşılmış sembole "bir tur daha izle" demek süresiz erteleme demektir ve talimat madde D yasaktır. **Risk kabul ediyorum: Eşik aşanları çıkartmak, TSM/MRVL gibi teknik güçlü olanları kaçırmak demek olabilir. Ama portföy odağını korumak (AMD 50g'yi geri kazandı, nakit düzeltme fırsatı için hazır) daha stratejik.**

**NVDA'yı tutma kararı (ilk hafta %-5.2 düşüş):** "50g desteğini koruyor ama momentum zayıfladı, bir sonraki turda izlenmeli" dedim. Eğer NVDA bir sonraki turda %-10 daha düşerse (örn. 50g'yi kaybeder, 200$ civarına), "ilk hafta düşüş uyarısıydı, bu turda kırpmalıydım" diye pişman olabilirim. Gerekçem: (1) NVDA hala 50g üzerinde (+%2.8), stop mesafesi rahat (%+14.9, henüz kritik değil). (2) SpaceX 1.1 mlr $ anlaşması ve CEO güven mesajı tezi destekliyor. (3) İlk hafta düşüş normal düzeltme olabilir (kâr realizasyonu). **Risk kabul ediyorum: NVDA momentum zayıfladı, bir sonraki turda 50g'yi kaybederse veya stop'a yaklaşırsa uyarı olacak. Ama şimdi kırpmak, bir haftalık düzeltme üzerine panik satışı olur.**

**AMD'nin tez etiketini GEÇERLİ'ye yükseltme kararı:** Geçen tur ZAYIFLIYOR, bu tur GEÇERLİ (50g'yi geri kazandı). Eğer AMD bir sonraki turda tekrar 50g'yi kaybederse, "çok erken GEÇERLİ'ye yükselttim, bir-iki tur daha ZAYIFLIYOR'da tutmalıydım" diye pişman olabilirim. Gerekçem: (1) Geçen tur "son şans — bir sonraki turda ya 50g'yi geri kazanır ya da harekete geçeceğim" demiştim. AMD şartı yerine getirdi (50g'yi geri kazandı, haftalık +%13.1, CFO'dan olumlu haber). (2) Talimat madde C: "Aynı pozisyona üçüncü kez üst üste aynı etiketi yazıyorsan, o tur bir şey değişmek zorundadır: ya eylem, ya etiket." Tur #5, #6, #7'de üç tur ZAYIFLIYOR — bu tur (#8) eylem oldu (50g geri kazanıldı) ve etiket değişti. **Risk kabul ediyorum: AMD tekrar zayıflayabilir. Ama geçen tur "son şans" şartı bu tur yerine getirildi, etiketi yükseltmek disiplinli.**

**Nakit %16.4 koruma kararı (hiçbir yeni pozisyon açmama):** Eğer bir sonraki turlarda piyasa +%15 yaparsa ve ben nakit %16.4 ile oturduysam, "TSM veya MRVL'e pozisyon açmalıydım, nakit pasif tutmak fırsat kaybı" diye pişman olabilirim. Gerekçem: (1) Talimat madde E: "Nakit pasif tutulmayacak; düşüşte alım gücüdür." Ama nakit TUT, düzeltme fırsatı bekliyor (mevcut pozisyonlara ekleme — özellikle AMD güçlendirme veya MU bilanço öncesi düzeltme). (2) Eşik aşanların hiçbiri yeterince güçlü gerekçe sunmadı (detaylı gerekçeler madde D2'de). **Risk kabul ediyorum: Nakit korumak, yükseliş fırsatını kaçırmak demek olabilir. Ama mevcut portföy (AMD 50g'yi geri kazandı + NVDA yeni) yeterince dinamik — nakit düşüş fırsatı için daha stratejik.**

**Ders kalibrasyonu:**  
- **Davranış değişikliği (iki bağımsız gözlem, aynı yön):** (1) AMD "son şans" uyarısı (tur #7), şart yerine getirildi (tur #8). (2) AVGO kırp-bekle-kapat (tur #5, #6, #7), bilanço sonrası düşüş. **İki pozisyonda da "koşullu eylem" planı işe yaradı.** AMD'ye bir tur daha fırsat tanımak doğruydu (fundamentaller güçlüydü), AVGO'yu bilanço bekleyip kapatmak doğruydu (tez bozuktu). **Ders: Bir pozisyon zayıflıyorsa ama fundamentaller güçlüyse (AMD gibi), "son şans" uyarısı ver ve bir tur daha izle. Tez bozuksa (AVGO gibi), koşullu plan yap (bilanço bekle) ve koşul gerçekleşince hemen kes. İki durumu karıştırma.**

- **Hipotez (henüz davranış değişikliği değil):** Yeni pozisyonun ilk hafta performansı kestirilmez (NVDA %-5.2 düşüş). Ancak bu tek olay — NVDA'nın ilk ay performansı bir sonraki turlarda izlenecek. Eğer NVDA bir ay sonra hala 50g'yi koruyorsa ve toparlanıyorsa, ilk hafta düşüş sadece kısa vadeli düzeltmeydi demektir. **Ders (henüz net değil): Yeni pozisyon açtıktan sonra ilk 2-3 hafta izle, 50g kaybı veya stop'a yaklaşma varsa uyarı. İlk hafta düşüş normal olabilir ama iki hafta üst üste 50g kaybı kırpma sinyali olabilir.**

**Sonraki gözden geçirme:** 19 Eylül 2026 (Cumartesi — bir sonraki haftalık tur). **KRİTİK:** NVDA'nın 50g durumu (geri kazandı mı yoksa kaybetti mi?), stop mesafesi (200$'a ne kadar yakın?). AMD'nin 50g'yi koruyup korumadığı (tekrar kaybederse tez GEÇERLİ'den ZAYIFLIYOR'a düşer). MU bilanço yaklaşıyor (30 Eylül, 11 gün sonra — bir son hafta öncesi kontrol). ANET momentum devam ediyor mu. Nakit düzeltme fırsatı bekleniyor.

---

## #9 — 19 Eylül 2026 · HAFTALIK TUR

**Piyasa bağlamı:** AI altyapı teması istikrarlı toparlanma trendinde. Portföy %+2.32 (SPY'dan %+3.57 önde, SMH'den %+2.79 önde). Yarı iletkenler ve AI hızlandırıcılar güçlü haftalık performans gösterdi.

### A. Veri durumu

10/10 sembol için veri eksiksiz çekildi (18 Eylül 2026 Cuma kapanış bazlı). Tüm pozisyonlarda fiyat, 50/200g SMA, RSI, getiri verileri ve bilanço tarihleri mevcut. **Eksik alan yok.**

**Veri bütünlüğü kapısı kontrolü:** Her pozisyon için `last_price` ve `sma50` alanları tek tek kontrol edildi (talimat madde 3). Tüm alanlar dolu:
- MU: last_price=1015.8 ✓, sma50=927.26 ✓
- AMD: last_price=559.82 ✓, sma50=495.85 ✓
- ANET: last_price=199.39 ✓, sma50=187.53 ✓
- NVDA: last_price=222.27 ✓, sma50=214.07 ✓

`_meta.eksik_veri` = [] (boş). Ek yfinance sorgusu gereklilik tespit edilmedi.

**Haber taraması:** 10 sembol için toplam 50 başlık tarandı. Dikkate değer:

- **MU:** "What Does Micron Technology (MU) Warning Of Shortages Through 2027 Mean?" — 2027'ye kadar arz sıkıntısı uyarısı. "Nvidia, SK Hynix send strong signal to Micron investors" — NVDA ve SK Hynix'ten olumlu sinyaller. "UBS now expects AI capex to reach nearly $1tn this year and around $1.4tn by 2027" — AI yatırımı büyüyor.

- **AMD:** "Dow Jones Futures: Nasdaq, S&P 500 Hold; Robinhood, Sandisk, AMD, Moderna Surge Into Buy Areas" — AMD alım bölgesinde. "AMD (AMD) Stock Looks Cheap After Its Huge 3 Year Run" — 3 yıllık rally sonrası değerleme ucuz görünüyor. "Chip Stocks Break Through Ceiling As Sector Rebounds. Macom Is A Standout." — yarı iletken sektörü tavana çıkıyor.

- **ANET:** "Arista Networks (ANET) Raises Full Year Outlook As AI Data Center Demand Stays Strong" — **ANET tam yıl rehberliğini yükseltti, AI veri merkezi talebi güçlü!**

- **NVDA:** Genel piyasa haberleri, özel NVDA haberi yok. Momentum istikrarlı.

- **SNDK:** "Sandisk Joins the S&P 100 on Monday -- the Same Day Nike Leaves It" — S&P 100'e eklendi. "Dow Jones Futures: Nasdaq, S&P 500 Hold; Robinhood, Sandisk, AMD, Moderna Surge Into Buy Areas" — alım bölgesinde.

### B. Hareketin sebebi

Hiçbir pozisyon haftalık bazda ±%10'u geçmedi (MU +%4.2, AMD +%8.5, ANET %-0.1, NVDA +%1.8). Özel araştırma gerektiren hareket yok.

### C. Tez sağlık kontrolü

**MU (1015.80$, 18 Eylül Cuma) — Bellek süper döngüsü / HBM liderliği → GEÇERLİ ve GÜÇLÜ**  
Fiyat > 50g (927.26, +%9.6 üzerinde) >> 200g (640.02, +%58.7 üzerinde). RSI 58.3 (sağlıklı momentum). 1 hafta +%4.2, 1 ay +%4.3, 3 ay %-16.1. Stop 730$ (%+39.2 mesafe, çok rahat). Bilanço 30 Eylül (veri_haftalik.json, Çarşamba, 11 gün sonra). Haberler: "2027'ye kadar arz sıkıntısı uyarısı" — arz sıkıntısı fiyat desteği demektir. "NVDA ve SK Hynix'ten olumlu sinyaller" — ana müşteriler güçlü. "UBS: AI capex $1tn bu yıl, $1.4tn 2027'de" — AI yatırım döngüsü büyüyor, bellek talebi güçlü. Haftalık +%4.2 sağlıklı toparlanma (geçen tur %-4.1 düşüştü). 50g desteğini koruyor (+%9.6 üzerinde), momentum istikrarlı. **Tez geçerli ve güçlü, bilanço 11 gün sonra — izlenmeli.**

**AMD (559.82$) — AI hızlandırıcı / NVDA alternatifi → GEÇERLİ ve GÜÇLÜ**  
Fiyat > 50g (495.85, +%12.9 üzerinde) >> 200g (354.62, +%57.9 üzerinde). **50g'yi koruyor ve genişletiyor!** Geçen tur (#8) 50g'yi geri kazanmıştı (516.13$ > 496.55$, +%3.9 üzerinde), bu tur daha da güçlendi (559.82$ > 495.85$, +%12.9 üzerinde). RSI 65.4 (güçlü momentum, geçen tur 58.0'den yükseldi). 1 hafta +%8.5 (**çok güçlü haftalık performans!**), 1 ay +%19.2 (**portföyün en güçlü aylık performansı!**), 3 ay +%1.5. Stop 440$ (%+27.2 mesafe, rahat bölge, geçen tur %+17.3'ten genişledi). Bilanço 3 Kasım (veri_haftalik.json, Salı). Haber: "AMD alım bölgesinde" — analist ilgisi sürüyor. "3 yıllık rally sonrası değerleme ucuz görünüyor" — fundamentaller güçlü. "Chip Stocks Break Through Ceiling" — sektör rally'si. **Geçen tur (#8) tez etiketini ZAYIFLIYOR'dan GEÇERLİ'ye yükselttim (50g'yi geri kazandı). Bu tur teyit: 50g'yi koruyor ve genişletiyor (+%12.9 üzerinde), haftalık +%8.5, aylık +%19.2. Tez GEÇERLİ ve GÜÇLÜ — portföyün en dinamik pozisyonu.**

**ANET (199.39$) — AI veri merkezi ağ donanımı lideri → GEÇERLİ ve GÜÇLÜ**  
Fiyat > 50g (187.53, +%6.3 üzerinde) >> 200g (155.11, +%28.5 üzerinde). RSI 55.8 (sağlıklı). 1 hafta %-0.1 (minimal düzeltme), 1 ay +%8.5, 3 ay +%14.2. Stop 160$ (%+24.6 mesafe, rahat). Bilanço 3 Kasım (Salı). Haber: **"ANET tam yıl rehberliğini yükseltti, AI veri merkezi talebi güçlü!"** — bu çok önemli, tezi güçlendiriyor. Haftalık %-0.1 minimal düzeltme normal volatilite aralığında (geçen tur +%4.3, bu tur %-0.1 — konsolidasyon). 50g desteğini koruyor (+%6.3 üzerinde), momentum sağlıklı. **Portföyün en istikrarlı pozisyonu. Rehberlik yükseltme haberi tezi güçlendirdi — GEÇERLİ ve GÜÇLÜ.**

**NVDA (222.27$) — AI hızlandırıcı liderliği → GEÇERLİ ve TOPARLANMA**  
Fiyat > 50g (214.07, +%3.8 üzerinde) >> 200g (198.02, +%12.2 üzerinde). RSI 54.4 (sağlıklı, geçen tur 49.9'dan iyileşti). 1 hafta +%1.8 (toparlanma), 1 ay +%2.6, 3 ay +%6.6. Stop 190$ (%+17.0 mesafe, rahat ama geçen tur %+14.9'dan hafif genişledi). Bilanço 17 Kasım (Salı). Geçen tur (#8) ilk hafta %-5.2 düşüş yaşamıştı (218.29$, %-4.3 haftalık), bu tur toparlandı (222.27$, +%1.8 haftalık). **50g'yi koruyor (+%3.8 üzerinde, geçen tur +%2.8'den hafif genişledi), momentum iyileşti (RSI 49.9 → 54.4), stop mesafesi hafif genişledi (%+14.9 → %+17.0).** Geçen tur "NVDA'nın 50g durumu (geri kazandı mı yoksa kaybetti mi?)" diye izlenecekti — bu tur 50g'yi koruyor ve hafif genişletti. **Tez GEÇERLİ, ilk hafta düşüş sonrası toparlanma — iki haftalık düşüş olsaydı uyarı olacaktı, ama bu tur toparlad toparlandı. İzlemeye devam.**

### D. Kararlar

#### KARAR 1: TUT — MU, AMD, ANET, NVDA

**MU:** 50g desteğini koruyor (+%9.6 üzerinde), stop mesafesi çok rahat (%+39.2), bilanço 11 gün sonra (30 Eylül Çarşamba). Arz sıkıntısı haberi fiyat desteği demek, AI capex büyümesi bellek talebini destekliyor. Haftalık +%4.2 sağlıklı toparlanma. **Bilanço öncesi son hafta kritik olacak — bir sonraki tur (26 Eylül) bilanço 4 gün öncesi kontrol.** Stop 730$ korunuyor.

**AMD:** 50g'yi koruyor ve genişletiyor (+%12.9 üzerinde), haftalık +%8.5, aylık +%19.2 — **portföyün en dinamik pozisyonu.** Geçen tur 50g'yi geri kazandı, bu tur teyit etti. RSI 65.4 (güçlü momentum ama henüz aşırı alım değil — 70 üzerinde olsaydı), stop mesafesi rahat (%+27.2). Tez GEÇERLİ ve GÜÇLÜ. Stop 440$ korunuyor.

**ANET:** Rehberlik yükseltme haberi tezi güçlendirdi. 50g desteğini koruyor (+%6.3 üzerinde), haftalık %-0.1 minimal düzeltme (konsolidasyon, geçen tur +%4.3'ten sonra normal). Stop mesafesi rahat (%+24.6). Portföyün en istikrarlı pozisyonu. Stop 160$ korunuyor.

**NVDA:** İlk hafta %-5.2 düşüş sonrası toparlandı (+%1.8 haftalık). 50g'yi koruyor (+%3.8 üzerinde), RSI iyileşti (49.9 → 54.4), stop mesafesi hafif genişledi (%+14.9 → %+17.0). İki haftalık düşüş uyarı olacaktı ama bu tur toparlad toparlandı — ilk ay performansı kabul edilebilir seviyede (giriş 230.36$ → şimdi 222.27$, %-3.5 kayıp ama 50g üzerinde). Tez GEÇERLİ, izlemeye devam. Stop 190$ korunuyor.

**Çıkış planı:** Stop seviyeleri aynen (MU 730$, AMD 440$, ANET 160$, NVDA 190$). Haftalık kapanış altında mekanik satış.

**Tezin yanlış olduğunu gösterecek işaret:**  
- MU: Bilanço (30 Eylül) beklentileri karşılamazsa, arz sıkıntısı söylemi kar marjına yansımazsa. Bilanço öncesinde stop'a yaklaşırsa (800$'ın altı).  
- AMD: 50g'yi (495.85$) kaybeder ve 3 gün üst üste altında kalırsa — momentum kırılma sinyali, tez GEÇERLİ'den ZAYIFLIYOR'a düşer.  
- ANET: 50g'yi (187.53$) kaybeder — rehberlik yükseltme sonrası düşüş tezi sorgulatır.  
- NVDA: 50g'yi (214.07$) kaybeder ve 3 gün üst üste altında kalırsa, veya stop'a yaklaşırsa (200$'ın altı) — ilk ay momentum başarısız demektir.

#### KARAR 2: YENİ POZĐSYON YOK (İzleme Listesi Boş)

**Nakit:** 16.421$ (%16.4 portföy, RAPOR.md).

**İzleme listesi durumu:** Geçen tur (#8, 12 Eylül) beş eşik aşan sembol (SNDK, TSM, MRVL, MSFT, GOOGL) listeden çıkarıldı. **Bu tur izleme listesi boş — yeni sembol değerlendirmesi yok.**

**Neden yeni pozisyon yok:**  
(1) **İzleme listesi boş:** Geçen tur tüm eşik aşanlar listeden çıkarıldı (eşik aşmış sembole "bir tur daha izle" demek süresiz erteleme demektir ve talimat madde D yasaktır). Yeni sembol taraması yapılmadı.  
(2) **Mevcut portföy güçlü:** AMD 50g'yi geri kazandı ve bu tur güçlendi (+%8.5 haftalık, +%19.2 aylık), ANET rehberlik yükseltti, MU bilanço öncesi sağlıklı toparlanma, NVDA ilk hafta düşüş sonrası toparlandı. Dört pozisyon da 50g üzerinde, stop mesafeleri rahat. **Portföy momentum kazandı — yeni pozisyon eklemek yerine mevcut pozisyonları izlemek daha disiplinli.**  
(3) **Nakit stratejisi:** %16.4 nakit (16.421$) pasif tutulmayacak (talimat madde E). **Ne için bekliyorum:** (a) MU bilanço (30 Eylül) öncesinde veya sonrasında düzeltme fırsatı — ekleme. (b) AMD'nin momentum devam ederse ekleme fırsatı (49 örn. düzeltme varsa 500$'a yakın). (c) NVDA'nın bir sonraki tur 50g'yi kaybetmesi veya stop'a yaklaşması halinde alternatif eylem (AMD güçlendirme). Nakit barut, düzeltme fırsatı için hazır.

**Yeni sembol taraması değerlendirmesi:** "Neden geçen tur listeden çıkarılmış sembolleri (TSM, MRVL, SNDK) tekrar değerlendirmiyorsun?" diye sorulabilir. Gerekçe: (1) Geçen tur listeden çıkartma kararı bütünsel gerekçelerle verildi (TSM/MRVL eşikleri çok aşılmış 7/3, portföy temasına katkısı sınırlı, SNDK psikolojik yük + kâr realizasyonu). (2) Bu tur mevcut portföy güçlü momentum kazandı — yeni pozisyon eklemek portföyü dağıtır (her pozisyon küçülür, 3-5x hedefine katkı azalır). (3) **Bir sembol listeden çıkartıldıysa, tekrar girmesi için çok güçlü bir gerekçe gerekir (örn. S&P 100 eklenmesi gibi yapısal değişiklik, veya %-20 düşüş sonrası 50g kırılımı gibi teknik fırsat).** SNDK bu tur +%9.7 daha yaptı (1791.82$, geçen tur 1633.35$ — S&P 100 eklenmesi sonrası toparlanma sürüyor) ama hala "listeden çıkartıldı" durumu geçerli (bu kadar uzun erteleme 4/3, portföyün odağını dağıttı). Bir sonraki turlarda yeni sembol taraması yapılabilir ama bu tur odak mevcut pozisyonlarda.

### E. Tema riski

**Portföy:** 4 pozisyon (MU %33.4, AMD %21.1, ANET %15.3, NVDA %14.1, RAPOR.md ağırlıkları) — hepsi AI altyapı teması. %83.9 yatırımda, %16.1 nakit (RAPOR.md 16.421$, %16.1 değil %16.4 ama RAPOR.md'deki ağırlıklar güncel).

**Aynı anda düşme riski:** AI harcama döngüsü kırılırsa (örn. mega-cap'ler capex kısarsa, AI yatırım balonu patlarsa) tüm pozisyonlar birlikte düşer. Bu risk başlangıçta bilinçli kabul edildi — agresif hedefin (3-5x) bedeli. **Bu tur portföy momentum kazandı** (AMD +%8.5 haftalık, ANET rehberlik yükseltti, MU arz sıkıntısı haberi, NVDA toparlandı) — tema riski devam ediyor ama portföy içindeki momentum güçlendi.

**Portföy kompozisyonu detay:**
- Bellek: MU (%33.4) — HBM/DRAM süper döngüsü, portföyün en büyük ağırlığı, bilanço 11 gün sonra  
- AI hızlandırıcı: AMD (%21.1, 50g'yi genişletiyor) + NVDA (%14.1, toparlandı) = %35.2 — portföyün ikinci büyük grubu, en dinamik cephe  
- Ağ donanımı: ANET (%15.3, rehberlik yükseltti) — veri merkezi ağ lideri, en istikrarlı pozisyon  
**Toplam yatırım:** %83.9 (nakit %16.1).

**Çeşitlendirme:** AI altyapının üç ana cephesi (bellek, işlemci, ağ) kapsanıyor. Ancak ÜÇÜ DE AI harcama döngüsüne bağlı — tema kırılımı hepsini birlikte vurur. **Risk kabul ediyorum: agresif hedef (3-5x), agresif konsantrasyon gerektirir.** Geçen tur TSM/MRVL/MSFT/GOOGL listeden çıkarıldı — tema çeşitliliği yerine tema derinliği (mevcut pozisyonlara ekleme fırsatı) stratejisi seçildi. Bu tur mevcut portföy momentum kazandı, strateji doğrulandı.

**Nakit: koruma yastığı DEĞİL, alım gücü.** %16.1 nakit (16.421$) portföyü korumaz (kaldıraçsız sanal portföy); düşüşte kullanılacak barut. **Ne için bekliyorum:** (1) MU bilanço (30 Eylül) öncesinde veya sonrasında düzeltme fırsatı — ekleme. (2) AMD momentum devam ederse düzeltme fırsatı (örn. 500$ civarı) — güçlendirme. (3) NVDA zayıflarsa (50g kaybı, stop'a yaklaşma) — alternatif eylem (AMD güçlendirme veya NVDA kırpma). Nakit pasif değil, düzeltme fırsatı bekliyor.

### F. Hesap verme

**1. Geçen tur ne söylemiştim, bu tur ne yaptım?**

**Geçen tur (#8, 12 Eylül):**

- **MU, AMD, ANET, NVDA TUT:** Hepsini tuttum. **Sapma yok.** AMD tez etiketini geçen tur ZAYIFLIYOR'dan GEÇERLİ'ye yükselttim (50g'yi geri kazandı), bu tur teyit etti (50g'yi koruyor ve genişletiyor, +%12.9 üzerinde).

- **İzleme listesi — beş eşik aşan sembol (SNDK, TSM, MRVL, MSFT, GOOGL) listeden çıkartıldı:** Geçen tur hepsini listeden çıkarttım (talimat madde D: eşik aşıldı, ya pozisyon aç ya listeden çıkar, üçüncüsü yok). Bu tur yeni sembol değerlendirmesi yapmadım. **Sapma yok.**

- **Nakit %16.4 koruma "düzeltme fırsatı beklemek için":** Geçen tur "mevcut pozisyonlarda düzeltme fırsatı bekliyor (AMD güçlendirme veya MU bilanço öncesi düzeltme)" dedim. Bu tur düzeltme olmadı (AMD +%8.5, MU +%4.2 toparlandı), nakdi tuttum. **Sapma yok — düzeltme beklentisi, düzeltme yoksa nakit tut demektir.**

**SAPMA YOK.** Geçen tur söylediklerimin hepsini yaptım.

**2. Geçen turdaki tezin yanlış çıktığı yer — YANLIŞ ÇIKMADI, teyit edildi:**

**AMD tezi (geçen tur GEÇERLİ'ye yükseltme):** Geçen tur (#8) 50g'yi geri kazandı (516.13$ > 496.55$, +%3.9 üzerinde), tez etiketini ZAYIFLIYOR'dan GEÇERLİ'ye yükselttim. Bu tur teyit: 50g'yi koruyor ve genişletiyor (559.82$ > 495.85$, +%12.9 üzerinde), haftalık +%8.5, aylık +%19.2 — **portföyün en dinamik pozisyonu.** Geçen tur "eğer AMD bir sonraki turda tekrar 50g'yi kaybederse, 'çok erken GEÇERLİ'ye yükselttim' diye pişman olabilirim" demiştim. **Pişman değilim — AMD 50g'yi korudu ve güçlendi. Tez GEÇERLİ'ye yükseltme kararı doğruydu.**

**NVDA ilk hafta düşüş sonrası toparlanma:** Geçen tur (#8) NVDA ilk hafta %-5.2 düşüş yaşamıştı (218.29$, %-4.3 haftalık), "50g desteğini koruyor ama momentum zayıfladı, bir sonraki turda izlenmeli" demiştim. Bu tur toparlandı (222.27$, +%1.8 haftalık), 50g'yi koruyor (+%3.8 üzerinde, geçen tur +%2.8'den hafif genişledi), RSI iyileşti (49.9 → 54.4), stop mesafesi hafif genişledi (%+14.9 → %+17.0). Geçen tur "eğer NVDA bir sonraki turda %-10 daha düşerse, 'ilk hafta düşüş uyarısıydı, bu turda kırpmalıydım' diye pişman olabilirim" demiştim. **Pişman değilim — NVDA toparlandı, ilk hafta düşüş kısa vadeli düzeltmeydi. İlk ay performansı kabul edilebilir seviyede (giriş 230.36$ → şimdi 222.27$, %-3.5 kayıp ama 50g üzerinde, toparlanma trendi başladı).**

**Beş eşik aşan sembolü listeden çıkartma kararı:** Geçen tur SNDK (4/3), TSM (7/3), MRVL (7/3), MSFT (7/3), GOOGL (7/3) — hepsini listeden çıkarttım. Geçen tur "eğer bunlardan biri (özellikle TSM veya MRVL) bir sonraki turlarda +%30 yaparsa, 'eşik aşmış sembolleri çıkartmak yerine en azından TSM'e pozisyon açmalıydım' diye pişman olabilirim" demiştim. Bu tur kontrol: TSM 433.24$ → 434.67$ (+%0.3), MRVL 236.10$ → 244.25$ (+%3.5), SNDK 1633.35$ → 1791.82$ (+%9.7). **Hiçbiri +%30 yapmadı. SNDK +%9.7 en güçlü ama S&P 100 eklenmesi sonrası toparlanma — yapısal değişiklik değil, kısa vadeli alım dalgası.** Geçen tur karar: "eşik aşanları çıkartmak, TSM/MRVL gibi teknik güçlü olanları kaçırmak demek olabilir. Ama portföy odağını korumak (AMD 50g'yi geri kazandı, nakit düzeltme fırsatı için hazır) daha stratejik." Bu tur teyit: AMD +%8.5 haftalık yaptı (portföyün en dinamik pozisyonu), mevcut portföy momentum kazandı — yeni pozisyon eklemek yerine mevcut pozisyonlara odaklanmak doğru karardı. **Pişman değilim.**

**3. Bu turda verdiğim kararın beni yanıltabileceği yer:**

**AMD'nin tez etiketini GEÇERLİ'de tutma kararı (ve ekleme yapmama):** AMD 50g'yi koruyor ve genişletiyor (+%12.9 üzerinde), haftalık +%8.5, aylık +%19.2 — **portföyün en dinamik pozisyonu.** Tez GEÇERLİ ve GÜÇLÜ. Eğer AMD bir sonraki turda +%20 daha yaparsa (örn. 670$ civarı) ve ben "ekleme fırsatı bekliyorum" diye nakit tuttuysamnakit tuttum, "AMD 560$ civarındayken ekleme yapmalıydım, momentum açıktı" diye pişman olabilirim. Gerekçem: (1) RSI 65.4 (güçlü momentum ama 70'e yakın — aşırı alım riski). (2) Haftalık +%8.5, aylık +%19.2 — bu hızda yükseliş sürdürülebilir değil, kısa vadede düzeltme riski var. (3) MU bilanço 11 gün sonra (30 Eylül) — bilanço öncesi veya sonrası düzeltme fırsatı daha stratejik (MU portföyün en büyük ağırlığı %33.4, ekleme etkisi daha büyük). **Risk kabul ediyorum: AMD momentum devam ederse ekleme fırsatı kaçırırım. Ama RSI 65.4 (aşırı alıma yakın), kısa vadede düzeltme riski var — düzeltme fırsatı beklemek daha disiplinli.**

**NVDA'yı tutma kararı (ekleme yapmama):** NVDA toparlandı (+%1.8 haftalık), 50g'yi koruyor (+%3.8 üzerinde), RSI iyileşti (54.4). Ancak hala %-3.5 kayıpla (giriş 230.36$ → şimdi 222.27$). Eğer NVDA bir sonraki turda +%15 yaparsa (örn. 255$ civarı) ve ben "toparlanma başladı ama ekleme yapmadım" diye pişman olabilirim. Gerekçem: (1) NVDA hala ilk ay performansını kanıtlama aşamasında — iki hafta önce %-5.2 düşmüştü, bu tur +%1.8 toparlandı, ama toparlanma trendi teyit edilmedi (bir haftlık toparlanma yeterli değil, iki-üç hafta daha izlenmeli). (2) Stop mesafesi %+17.0 (rahat ama MU/AMD/ANET'e göre dar) — ekleme yapmak yerine izlemek daha disiplinli. (3) Nakit MU bilanço fırsatı için bekleniyor. **Risk kabul ediyorum: NVDA toparlanma trendi devam ederse ekleme fırsatı kaçırırım. Ama ilk ay performansı henüz kanıtlanmadı — iki-üç hafta daha izleyip toparlanma teyit edilirse ekleme değerlendiririm.**

**MU bilanço öncesi ekleme yapmama kararı:** MU bilanço 11 gün sonra (30 Eylül Çarşamba). Fiyat 1015.80$, 50g'nin +%9.6 üzerinde, haftalık +%4.2 sağlıklı toparlanma. "2027'ye kadar arz sıkıntısı uyarısı" haberi fiyat desteği demek. Eğer MU bilanço güçlü çıkar ve +%20 yaparsa (örn. 1220$ civarı) ve ben "bilanço öncesi 1015$ civarındayken ekleme yapmalıydım" diye pişman olabilirim. Gerekçem: (1) **Bilanço riski iki yönlü:** Güçlü bilanço +%20 yapabilir AMA zayıf bile bilanço veya rehberlik hayal kırıklığı %-10-15 düşüş yapabilir. Bilanço öncesi ekleme, bilanço riskini artırır. (2) Talimat bilanço kuralı: "1 haftadan az kala yeni tam pozisyon açılmaz" — bilanço 11 gün sonra, bu sınırda değil AMA "1 haftadan fazla" diye ekleme yapmak bilanço riskini göz ardı eder. (3) **Nakit stratejisi: bilanço SONRASI düzeltme fırsatı beklemek daha disiplinli.** Eğer bilanço güçlü çıkar ve hisse %+10-15 yaparsa ekleme yapmam (zaten hedef ağırlıkta %33.4, en büyük pozisyon). Eğer bilanço zayıf çıkar ve hisse %-10-15 düşerse ekleme fırsatı (örn. 900$ civarı — 50g 927'ye yakın, destek testi). **Risk kabul ediyorum: MU bilanço güçlü çıkarsa ekleme fırsatı kaçırırım. Ama bilanço riski iki yönlü — bilanço sonrası düzeltme fırsatı beklemek daha disiplinli. Eğer bilanço güçlü çıkar ve +%20 yaparsa, portföyün en büyük ağırlığı %33.4 zaten büyük katkı yapıyor — ekleme kaçırılsa da kayıp sınırlı.**

**Yeni sembol taraması yapmama kararı:** Geçen tur beş eşik aşan sembol listeden çıkarıldı, bu tur yeni sembol taraması yapmadım. Eğer bir sonraki turlarda yeni bir güçlü sembol (örn. PLTR, SMCI, ORCL gibi AI teması sembolleri) tarama yapılsa ve o sembol +%30 yaparsa, "bu tur yeni sembol taraması yapmalıydım" diye pişman olabilirim. Gerekçem: (1) Geçen tur tüm eşik aşanlar listeden çıkarıldı (talimat madde D: eşik aşıldı, ya pozisyon aç ya listeden çıkar). Yeni sembol taraması yapılacaksa "sıfırdan başlat" demektir — ama bu tur mevcut portföy momentum kazandı (AMD +%8.5, ANET rehberlik yükseltti, MU sağlıklı toparlanma), odak mevcut pozisyonlarda. (2) Yeni sembol eklemek portföyü dağıtır (nakit %16.4 — tek pozisyon ~%10 ağırlık açılabilir, her pozisyon küçülür, 3-5x hedefine katkı azalır). (3) **Nakit stratejisi: mevcut pozisyonlara ekleme fırsatı beklemek (MU bilanço sonrası düzeltme, AMD düzeltme) daha stratejik.** **Risk kabul ediyorum: Yeni bir güçlü sembol taraması kaçırırsam fırsat kaybı olabilir. Ama mevcut portföy momentum kazandı — tema derinliği (mevcut pozisyonlara ekleme) stratejisi tema genişliğinden (yeni sembol) daha uygun.**

**Ders kalibrasyonu:**  
- **Davranış değişikliği (iki bağımsız gözlem, aynı yön teyit edildi):** (1) AMD "son şans" uyarısı (tur #7), şart yerine getirildi (tur #8), tez GEÇERLİ'ye yükseldi, bu tur (#9) teyit edildi (50g'yi koruyor ve genişletiyor, +%8.5 haftalık). (2) NVDA ilk hafta %-5.2 düşüş (tur #8), "50g desteğini koruyor, bir sonraki turda izlenmeli" dedim, bu tur toparlandı (+%1.8 haftalık, 50g'yi koruyor). **İki pozisyonda da "koşullu eylem + izleme" planı işe yaradı.** AMD'ye "son şans" uyarısı doğruydu (fundamentaller güçlüydü, teknik toparlandı). NVDA'ya "ilk hafta düşüş uyarı değil, izle" doğruydu (kısa vadeli düzeltme, toparlandı). **Ders onaylandı: Bir pozisyon zayıflıyorsa ama fundamentaller güçlüyse (AMD gibi), "son şans" uyarısı ver, şart yerine getirilirse tezi yükselt. Yeni pozisyon ilk hafta düşerse (NVDA gibi), panik satışı yapma — 50g'yi koruyor mu kontrol et, koruyor ve toparlanıyorsa izle.**

- **Hipotez (tur #8'den, bu tur teyit edildi):** Yeni pozisyonun ilk hafta performansı kestirilmez (NVDA %-5.2 düşüş). Bu tur NVDA toparlandı (+%1.8). **Ders (teyit edildi): Yeni pozisyon açtıktan sonra ilk 2-3 hafta izle. İlk hafta düşüş normal olabilir (kısa vadeli düzeltme) ama 50g kaybı veya iki hafta üst üste düşüş uyarı. NVDA ilk hafta düştü ama 50g'yi korudu, bu tur toparlandı — toparlanma trendi başladı, izlemeye devam.**

- **Yeni hipotez (bu turdan):** AMD momentum çok güçlü (haftalık +%8.5, aylık +%19.2, RSI 65.4 — aşırı alıma yakın). Eğer bir sonraki turda düzeltme görülürse (örn. %-5-10 düşüş, 500$ civarı — 50g 495'e yakın), bu bir ekleme fırsatı olabilir (güçlü momentum sonrası sağlıklı düzeltme + 50g desteği testi). **Ders (henüz hipotez, bir sonraki turda test edilecek): RSI 65+ olan pozisyonda ekleme yapmak yerine düzeltme beklemek daha disiplinli. Eğer AMD bir sonraki turda düzeltir ve 50g'yi test ederse (495$ civarı — %-10-15 düşüş), ekleme fırsatı değerlendiririm.**

**Sonraki gözden geçirme:** 26 Eylül 2026 (Cumartesi — bir sonraki haftalık tur). **KRİTİK:** (1) MU bilanço 30 Eylül Çarşamba — **bir sonraki tur bilanço 4 gün sonra, son kontrol.** 50g'yi koruyor mu, stop mesafesi rahat mı. (2) AMD'nin momentum devam ediyor mu? RSI 65.4 (aşırı alıma yakın) — düzeltme riski. 50g'yi koruyor ve genişletiyor mu? (3) NVDA toparlanma trendi devam ediyor mu? 50g'yi koruyor mu, RSI iyileşiyor mu? (4) ANET rehberlik yükseltme sonrası momentum devam ediyor mu? (5) Nakit düzeltme fırsatı bekleniyor (MU bilanço sonrası veya AMD düzeltme).

---

## #10 — 26 Eylül 2026 · HAFTALIK TUR

**Piyasa bağlamı:** AI altyapı temasında güçlü momentum sürüyor. Portföy %+7.11 (SPY'dan %+9.23 önde, SMH'den %+7.98 önde). Yarı iletkenler ve AI hızlandırıcılar çok güçlü haftalık performans gösterdi — AMD ve MU öne çıktı.

### A. Veri durumu

10/10 sembol için veri eksiksiz çekildi (25 Eylül 2026 Cuma kapanış bazlı). Tüm pozisyonlarda fiyat, 50/200g SMA, RSI, getiri verileri ve bilanço tarihleri mevcut. **Eksik alan yok.**

**Veri bütünlüğü kapısı kontrolü (talimat madde 3 — her alan tek tek kontrol edildi):**
- MU: last_price = 1082.28 ✓, sma50 = 941.62 ✓
- AMD: last_price = 630.63 ✓, sma50 = 504.71 ✓
- ANET: last_price = 206.55 ✓, sma50 = 190.23 ✓
- NVDA: last_price = 225.07 ✓, sma50 = 215.79 ✓

`_meta.eksik_veri` = [] (boş). **Tüm kritik alanlar dolu — veri bütünlüğü kapısı geçildi.** Ek yfinance sorgusu gereklilik tespit edilmedi.

**Haber taraması:** 10 sembol için toplam 50 başlık tarandı. Dikkate değer:

- **MU:** "Q4 Earnings Are Likely to Boost the 'Strong Buy' Case for Micron Stock" — bilanço 30 Eylül (5 gün sonra). "Micron Technology Stock Wavers Ahead Of Fiscal Q4 Earnings Report" — bilanço öncesi dalgalanma. "Stock Market Today: Dow Surges 450 Points On U.S.-Iran Peace Hopes; Micron Rises" — jeopolitik risk azalması MU'yu destekliyor. "Dow Jones Futures: Growth Stocks Shrug Off Surging Yields; Micron, SpaceX, Tesla, Key Economic Data Due" — büyüme hisseleri güçlü.

- **AMD:** "Trump says China's Xi 'seemed to like' renaming AI as super intelligence" — Trump-Xi görüşmesi, AI yatırımlarına olumlu sinyal. "These are stocks getting lifted up by Meta's Muse" — Meta'nın Muse AI platformu AMD'yi destekliyor. "Tech stocks gain after tech titan dinner with Trump and China's Xi Jinping" — teknoloji zirvesi pozitif. "Taiwan says U.S. arms support serves American interests after Trump-Xi summit" — jeopolitik belirsizlik azalması.

- **ANET:** "Arista Networks (ANET) Draws Fresh AI Attention, Is The Stock Still Cheap?" — AI ilgisi sürüyor, değerleme sorgulanıyor. "Technology Stocks Are Back, Because Nothing Else Is" — teknoloji liderleri geri döndü. "Arista Networks, Inc. (ANET) Is a Trending Stock: Facts to Know Before Betting on It" — trend devam ediyor.

- **NVDA:** "2 Data Center Stocks That Could Help Make You a Fortune" — veri merkezi talebi güçlü. Özel NVDA haberi yok, genel AI momentum haberleri.

- **SNDK:** "Are AI Memory Stocks Ready For Another Run? Micron, Sandisk Attempt To Clear New Buy Points" — SNDK yeni alım noktası arıyor. "SK Hynix's Solidigm Weighs IPO That Could Raise $15 Billion, Report Says" — SK Hynix'in IPO planı, NAND sektörüne ilgi.

### B. Hareketin sebebi

**AMD (559.82$ → 630.63$, +%12.6 haftalık) — ±%10'u geçti, sebep araştırması:**

AMD'nin güçlü performansının sebepleri:
1. **Trump-Xi teknoloji zirvesi (25 Eyl haftası):** "Trump says China's Xi 'seemed to like' renaming AI as super intelligence" — ABD-Çin AI işbirliği sinyali, jeopolitik risk azalması. AMD Çin pazarında önemli oyuncu (veri merkezi GPU'ları), ticaret savaşı yumuşaması olumlu.
2. **Meta'nın Muse AI platformu:** "These are stocks getting lifted up by Meta's Muse" — Meta'nın yeni AI platformu, AMD'nin MI serisi GPU'larını kullanıyor olabilir (NVDA dışında çeşitlendirme). Mega-cap'lerin AMD'ye yönelmesi "NVDA alternatifi" tezini güçlendiriyor.
3. **Yarı iletken sektör rallisi:** "Chip Stocks Break Through Ceiling As Sector Rebounds" (geçen tur haberi) — sektör genelinde güçlü alım dalgası devam ediyor. AMD geçen tur 50g'yi geri kazanmıştı, bu tur teknik kırılım (50g üzerinde güçleniyor) alım sinyali verdi.
4. **Teknik momentum:** Geçen tur (#9) 50g'yi koruyor ve genişletiyordu (+%12.9 üzerinde, RSI 65.4). Bu tur momentum daha da güçlendi — RSI 73.0 (aşırı alım bölgesine girdi, ama henüz aşırı değil). Teknik güçlülük algoritmi ve momentum yatırımcılarını çekiyor.

**Sonuç:** AMD'nin +%12.6 hareketi tek bir olaya değil, dört faktörün birleşimine dayanıyor — jeopolitik risk azalması (Trump-Xi), mega-cap çeşitlendirmesi (Meta Muse), sektör rallisi ve teknik momentum. Tez "AI hızlandırıcı / NVDA alternatifi" güçleniyor.

**MU (1015.80$ → 1082.28$, +%6.5 haftalık) — ±%10'u geçmedi ama yakın, not:**
MU +%6.5 (±%10 eşiğini geçmedi) ama güçlü toparlanma. Bilanço 5 gün sonra (30 Eylül Çarşamba) — "Q4 Earnings Are Likely to Boost the 'Strong Buy' Case" haberi beklenti oluşturuyor. Jeopolitik risk azalması (U.S.-Iran barış umudu) MU'yu destekliyor. Hareket normal volatilite aralığında ama bilanço öncesi dikkatle izlenmeli.

### C. Tez sağlık kontrolü

**MU (1082.28$, 25 Eylül Cuma) — Bellek süper döngüsü / HBM liderliği → GEÇERLİ ve GÜÇLÜ**  
Fiyat >> 50g (941.62, +%14.9 üzerinde) >> 200g (660.97, +%63.7 üzerinde). **Geçen tur 50g +%9.6 üzerindeydi, bu tur +%14.9 üzerinde — genişliyor!** RSI 63.2 (sağlıklı momentum, geçen tur 58.3'ten yükseldi ama aşırı alım değil). 1 hafta +%6.5, 1 ay +%15.7, 3 ay %-5.5. Stop 730$ (%+48.3 mesafe, çok rahat, geçen tur %+39.2'den daha da genişledi). **Bilanço 30 Eylül (veri_haftalik.json, Çarşamba, 5 gün sonra — KRİTİK!)** Haberler: "Q4 Earnings Are Likely to Boost the 'Strong Buy' Case" — analist beklentileri yüksek. "Dow Surges 450 Points On U.S.-Iran Peace Hopes; Micron Rises" — jeopolitik risk azalması destekliyor. "Growth Stocks Shrug Off Surging Yields" — faiz yükselişine rağmen büyüme hisseleri güçlü. Haftalık +%6.5 güçlü toparlanma (geçen tur +%4.2, ivme koruyor). 50g desteğini koruyor ve genişletiyor (+%14.9 üzerinde), momentum güçlü. **Tez geçerli ve güçlü, bilanço 5 gün sonra — bilanço BU TURUN kritik olayı.**

**AMD (630.63$) — AI hızlandırıcı / NVDA alternatifi → GEÇERLİ ve ÇOK GÜÇLÜ**  
Fiyat >> 50g (504.71, +%24.9 üzerinde) >> 200g (364.75, +%72.9 üzerinde). **50g'nin ÇOK üzerinde!** Geçen tur (#9) +%12.9 üzerindeydi, bu tur +%24.9 üzerinde — momentum patlaması. RSI **73.0 (AŞIRI ALIM BÖLGESİNE GİRDİ!)** — geçen tur 65.4, bu tur 73.0. RSI 70 üzeri teknik olarak aşırı alım sinyalidir ama güçlü momentum trendi devam edebilir. 1 hafta +%12.6 (**çok güçlü haftalık performans!**), 1 ay +%32.3 (**portföyün en güçlü aylık performansı!**), 3 ay +%16.9. Stop 440$ (%+43.3 mesafe, çok rahat, geçen tur %+27.2'den daha da genişledi). Bilanço 3 Kasım (Salı). Haberler: Trump-Xi teknoloji zirvesi (AI işbirliği sinyali), Meta Muse (AMD'ye yönelim), yarı iletken sektör rallisi. **Geçen tur (#9) tez etiketini GEÇERLİ'ye yükselttim (50g'yi geri kazandı), teyit edildi demiştim. Bu tur momentum PATLAMASI — aylık +%32.3, haftalık +%12.6, 50g'nin +%24.9 üzerinde. RSI 73.0 aşırı alım bölgesinde — teknik olarak kısa vadede düzeltme riski yüksek (RSI >70, sağlıklı düzeltme seviyesi 60-65'e geri dönüş olabilir). Ancak tez ÇOK GÜÇLÜ — Trump-Xi zirvesi ve Meta Muse AMD'nin "NVDA alternatifi" tezini teyit ediyor. Portföyün en dinamik ve en güçlü performans gösteren pozisyonu.**

**ANET (206.55$) — AI veri merkezi ağ donanımı lideri → GEÇERLİ ve GÜÇLÜ**  
Fiyat > 50g (190.23, +%8.6 üzerinde) >> 200g (157.04, +%31.5 üzerinde). RSI 60.2 (sağlıklı momentum, geçen tur 55.8'den yükseldi). 1 hafta +%3.6, 1 ay +%2.7, 3 ay +%25.9. Stop 160$ (%+29.1 mesafe, çok rahat). Bilanço 3 Kasım (Salı). Haberler: "ANET Draws Fresh AI Attention, Is The Stock Still Cheap?" — AI ilgisi sürüyor. "Technology Stocks Are Back" — sektör rallisi. Haftalık +%3.6 sağlıklı toparlanma (geçen tur %-0.1 minimal düzeltme, bu tur toparlandı). 50g desteğini koruyor (+%8.6 üzerinde, geçen tur +%6.3'ten hafif genişledi), momentum sağlıklı. **Portföyün en istikrarlı pozisyonu. Rehberlik yükseltme haberi (geçen tur) sonrası momentum devam ediyor. Tez geçerli ve güçlü.**

**NVDA (225.07$) — AI hızlandırıcı liderliği → GEÇERLİ ve TOPARLANMA DEVAM EDİYOR**  
Fiyat > 50g (215.79, +%4.3 üzerinde) >> 200g (199.13, +%13.0 üzerinde). RSI 55.3 (sağlıklı, geçen tur 54.4'ten hafif yükseldi). 1 hafta +%1.3, 1 ay %-1.2, 3 ay +%15.6. Stop 190$ (%+18.5 mesafe, rahat ama geçen tur %+17.0'den hafif genişledi). Bilanço 17 Kasım (Salı). Geçen tur (#9) toparlanma başlamıştı (+%1.8 haftalık, 50g +%3.8 üzerinde), bu tur toparlanma devam ediyor (+%1.3 haftalık, 50g +%4.3 üzerinde). **50g'yi koruyor ve hafif genişletiyor (+%3.8 → +%4.3), RSI istikrarlı (54.4 → 55.3), stop mesafesi hafif genişledi (%+17.0 → %+18.5). İki haftalık toparlanma trendi teyit edildi.** Tur #8'de ilk hafta %-5.2 düşüş yaşamıştı, tur #9'da +%1.8 toparlandı, bu tur +%1.3 toparlanma devam ediyor — **iki haftalık toparlanma trendi, ilk ay düşüş endişesi azalıyor.** Ancak hala giriş fiyatının altında (giriş 230.36$ → şimdi 225.07$, %-2.3 kayıp — geçen tur %-3.5'ten iyileşti). **Tez GEÇERLİ, toparlanma trendi iki haftadır devam ediyor, ilk ay performansı kabul edilebilir seviyeye yaklaşıyor. Bir-iki hafta daha toparlanma devam ederse giriş fiyatına ulaşabilir.**

### D. Kararlar

#### KARAR 1: TUT — MU, AMD, ANET, NVDA

**MU:** **Bilanço 5 gün sonra (30 Eylül Çarşamba) — BU TURUN kritik olayı.** 50g'yi koruyor ve genişletiyor (+%14.9 üzerinde, geçen tur +%9.6'dan güçlendi), stop mesafesi çok rahat (%+48.3, portföydeki en geniş stop mesafesi), haftalık +%6.5 güçlü toparlanma. "Q4 Earnings Are Likely to Boost the 'Strong Buy' Case" haberi analist beklentilerini yükseltiyor. Jeopolitik risk azalması (U.S.-Iran barış umudu) destekliyor. **Bilanço riski:** Güçlü bilanço +%10-15 yapabilir AMA zayıf bilanço veya rehberlik hayal kırıklığı %-10-15 düşüş yapabilir. **Karar: Tut, bilanço bekle.** Pozisyon %33.7 (portföyün en büyük ağırlığı) — bilanço öncesi ekleme yaparsam bilanço riskini artırır (bilanço zayıf çıkarsa kayıp büyür). Bilanço sonrası (bir sonraki tur, 3 Ekim Cumartesi) değerlendirme: Eğer bilanço güçlü çıkar ve +%10-15 yaparsa ekleme yapmam (zaten en büyük ağırlık). Eğer bilanço zayıf çıkar ve %-10-15 düşerse ekleme fırsatı (50g testi, 941$ civarı — destek). Stop 730$ korunuyor.

**AMD:** **RSI 73.0 — AŞIRI ALIM BÖLGESİ!** Teknik olarak kısa vadede düzeltme riski çok yüksek (RSI 70 üzeri aşırı alım, sağlıklı düzeltme 60-65'e geri dönüş olabilir). Ancak 50g'nin çok üzerinde (+%24.9), stop mesafesi çok rahat (%+43.3), momentum ÇOK GÜÇLÜ (aylık +%32.3, haftalık +%12.6). Trump-Xi teknoloji zirvesi ve Meta Muse haberleri tezi güçlendiriyor. **Karar: Tut, RSI izle.** Momentum patlaması devam edebilir (aşırı alım bölgesinde bile güçlü trendler haftalarca sürebilir) AMA düzeltme riski yüksek. **Bir sonraki turda RSI 75-80'e çıkarsa (daha da aşırı alım) VEYA 50g'yi kaybederse (504$ altı — momentum kırılması) uyarı olur.** Şimdilik 50g çok üzerinde, tez çok güçlü, stop çok rahat — tut. Ekleme yapmam (RSI 73.0 aşırı alım, düzeltme beklemek disiplinli). Stop 440$ korunuyor.

**ANET:** Rehberlik yükseltme (geçen tur) sonrası momentum devam ediyor. 50g desteğini koruyor (+%8.6 üzerinde), haftalık +%3.6 sağlıklı toparlanma, RSI 60.2 (sağlıklı), stop mesafesi çok rahat (%+29.1). Portföyün en istikrarlı pozisyonu. Stop 160$ korunuyor.

**NVDA:** İki haftalık toparlanma trendi teyit edildi (tur #9: +%1.8, bu tur +%1.3). 50g'yi koruyor ve hafif genişletiyor (+%3.8 → +%4.3), RSI istikrarlı (54.4 → 55.3), stop mesafesi hafif genişledi (%+17.0 → %+18.5). Giriş fiyatına yaklaşıyor (giriş 230.36$ → şimdi 225.07$, %-2.3 kayıp — geçen tur %-3.5'ten iyileşti). İlk ay performansı kabul edilebilir seviyeye yaklaşıyor. Stop 190$ korunuyor.

**Çıkış planı:** Stop seviyeleri aynen (MU 730$, AMD 440$, ANET 160$, NVDA 190$). Haftalık kapanış altında mekanik satış.

**Tezin yanlış olduğunu gösterecek işaret:**
- MU: Bilanço (30 Eylül) beklentileri karşılamazsa, rehberlik zayıfsa. Bilanço sonrası stop'a yaklaşırsa (800$'ın altı).
- AMD: RSI 75-80'e çıkarsa (çok aşırı alım — düzeltme yakın) VEYA 50g'yi (504.71$) kaybeder ve 3 gün üst üste altında kalırsa — momentum patlaması sonrası kırılma sinyali.
- ANET: 50g'yi (190.23$) kaybeder — rehberlik yükseltme sonrası düşüş tezi sorgulatır.
- NVDA: 50g'yi (215.79$) kaybeder ve 3 gün üst üste altında kalırsa — üç haftalık toparlanma trendi başarısız demektir.

#### KARAR 2: YENİ POZĐSYON YOK (Nakit Koruma — Bilanço ve Düzeltme Beklemek)

**Nakit:** 16.421$ (%16.4 portföy, RAPOR.md).

**İzleme listesi durumu:** Geçen turda (#8, 12 Eylül) beş eşik aşan sembol (SNDK, TSM, MRVL, MSFT, GOOGL) listeden çıkarıldı. Son iki turdur (#9, #10) yeni sembol taraması yapılmadı. **Bu tur da izleme listesi boş — yeni sembol değerlendirmesi yok.**

**Neden yeni pozisyon yok:**
1. **MU bilanço 5 gün sonra (30 Eylül Çarşamba) — nakit bilanço sonrası fırsat için bekleniyor.** Bilanço riski iki yönlü. Eğer bilanço zayıf çıkar ve MU %-10-15 düşerse (900$ civarı — 50g 941'e yakın, destek testi), ekleme fırsatı. Bilanço öncesi yeni pozisyon açmak portföy riskini artırır.
2. **AMD RSI 73.0 aşırı alım bölgesinde — düzeltme riski yüksek.** Eğer AMD bir sonraki turlarda %-10-15 düzeltirse (550$ civarı — 50g 504'e yakın, destek testi), ekleme fırsatı. Şimdi ekleme yapmak (RSI 73.0) aşırı alımda kovalamak demektir — disiplinsiz.
3. **Mevcut portföy çok güçlü momentum kazandı:** AMD aylık +%32.3 (portföyün en dinamik pozisyonu), MU bilanço öncesi güçlü (+%6.5 haftalık), ANET istikrarlı (+%3.6 haftalık), NVDA iki haftalık toparlanma trendi. Dört pozisyon da 50g üzerinde, stop mesafeleri rahat. **Yeni pozisyon eklemek portföyü dağıtır (nakit %16.4 — tek pozisyon ~%10 ağırlık açılabilir, her pozisyon küçülür, 3-5x hedefine katkı azalır). Mevcut pozisyonlara ekleme fırsatı beklemek (MU bilanço sonrası veya AMD düzeltme) daha stratejik.**
4. **Yeni sembol taraması yapılmadı:** Geçen turda TSM/MRVL/SNDK/MSFT/GOOGL listeden çıkarıldı (eşik aşılmış, talimat madde D: ya pozisyon aç ya listeden çıkar). Yeni sembol taraması yapılacaksa "sıfırdan başlat" demektir ama bu tur odak bilanço ve mevcut pozisyonlarda.

**Nakit stratejisi (talimat madde E: "Nakit pasif tutulmayacak"):** %16.4 nakit portföyü korumaz (kaldıraçsız sanal portföy); düşüşte kullanılacak barut. **Ne için bekliyorum:**
- **(a) MU bilanço sonrası (bir sonraki tur, 3 Ekim):** Eğer bilanço zayıf çıkar ve %-10-15 düşerse (900$ civarı — 50g testi), ekleme fırsatı. Eğer bilanço güçlü çıkar ve +%10-15 yaparsa ekleme yapmam (zaten en büyük ağırlık %33.7).
- **(b) AMD düzeltme (bir-iki tur içinde):** RSI 73.0 aşırı alım — düzeltme riski yüksek. Eğer %-10-15 düzeltirse (550$ civarı — 50g 504'e yakın, destek testi), ekleme fırsatı.
- **(c) NVDA zayıflarsa (olasılık düşük ama izleniyor):** 50g kaybı veya stop'a yaklaşma (200$ altı) halinde alternatif eylem (NVDA kırpma + AMD güçlendirme gibi).

Nakit barut, **MU bilanço ve AMD düzeltme fırsatı** için hazır. İkisi de bir-iki tur içinde gerçekleşebilir — MU bilanço 5 gün sonra, AMD düzeltme RSI 73.0'dan sonra olası.

### E. Tema riski

**Portföy:** 4 pozisyon (MU %33.7, AMD %22.5, ANET %15.1, NVDA %13.6, RAPOR.md ağırlıkları) — hepsi AI altyapı teması. %84.9 yatırımda, %15.1 nakit (RAPOR.md 16.421$, ağırlık %15.1 hesabı muhtemelen portföy değeri yükselmesi nedeniyle).

**Aynı anda düşme riski:** AI harcama döngüsü kırılırsa (örn. mega-cap'ler capex kısarsa, AI yatırım balonu patlarsa) tüm pozisyonlar birlikte düşer. Bu risk başlangıçta bilinçli kabul edildi — agresif hedefin (3-5x) bedeli. **Bu tur portföy momentum ÇOK güçlü** (AMD aylık +%32.3 patlaması, MU bilanço öncesi güçlü, ANET istikrarlı, NVDA toparlanma) — tema riski devam ediyor ama portföydeki momentum tarihi seviyelerde.

**Portföy kompozisyonu detay:**
- Bellek: MU (%33.7) — HBM/DRAM süper döngüsü, portföyün en büyük ağırlığı, **bilanço 5 gün sonra**
- AI hızlandırıcı: AMD (%22.5, RSI 73.0 aşırı alım, momentum patlaması) + NVDA (%13.6, toparlanma trendi) = %36.1 — portföyün ikinci büyük grubu, **en dinamik cephe (AMD patlaması)**
- Ağ donanımı: ANET (%15.1, rehberlik yükseltti) — veri merkezi ağ lideri, en istikrarlı pozisyon
**Toplam yatırım:** %84.9 (nakit %15.1).

**Çeşitlendirme:** AI altyapının üç ana cephesi (bellek, işlemci, ağ) kapsanıyor. Ancak ÜÇÜ DE AI harcama döngüsüne bağlı — tema kırılımı hepsini birlikte vurur. **Risk kabul ediyorum: agresif hedef (3-5x), agresif konsantrasyon gerektirir.** Son üç turdur (#8, #9, #10) TSM/MRVL/MSFT/GOOGL listeden çıkarıldı, yeni sembol taraması yapılmadı — tema çeşitliliği yerine tema derinliği (mevcut pozisyonlara ekleme fırsatı) stratejisi seçildi. Bu tur mevcut portföy momentum patlaması yaptı (%+7.11 haftalık), strateji doğrulandı.

**Özel risk — AMD aşırı alım (RSI 73.0):** AMD portföyün %22.5'i (ikinci en büyük pozisyon). RSI 73.0 teknik olarak kısa vadede düzeltme riski çok yüksek. Eğer AMD %-15-20 düzeltirse (örn. 530$ civarı), portföy %-3-4 etkilenir. **Ancak AMD'nin stop mesafesi çok rahat (%+43.3, 440$ stop), 50g'nin çok üzerinde (+%24.9) — teknik düzeltme olsa bile stop tetiklenmez, sağlıklı konsolidasyon olur.** Risk: düzeltme yerine momentum kırılması (50g kaybı) — o zaman tez sorgulanır. Şimdilik momentum çok güçlü, tez güçlü (Trump-Xi + Meta Muse) — izlemeye devam.

**Nakit: koruma yastığı DEĞİL, alım gücü.** %15.1 nakit portföyü korumaz; düşüşte kullanılacak barut. MU bilanço sonrası (5 gün sonra) veya AMD düzeltme (RSI 73.0 sonrası olası) fırsatı için hazır. **Eğer her ikisi de gerçekleşmezse (MU bilanço güçlü + AMD düzeltme olmaz), nakit bir-iki tur daha bekleyecek.** Acele ekleme yapmak yerine fırsat beklemek disiplinli.

### F. Hesap verme

**1. Geçen tur ne söylemiştim, bu tur ne yaptım?**

**Geçen tur (#9, 19 Eylül):**

- **MU, AMD, ANET, NVDA TUT:** Hepsini tuttum. **Sapma yok.**

- **AMD tez etiketi GEÇERLİ'de tutma:** Geçen tur 50g'yi koruyor ve genişletiyordu (+%12.9 üzerinde), bu tur daha da güçlendi (+%24.9 üzerinde, RSI 73.0 aşırı alım). **Sapma yok — tez GEÇERLİ ve ÇOK GÜÇLÜ oldu.**

- **Yeni pozisyon yok, nakit koruma "MU bilanço sonrası veya AMD düzeltme fırsatı için":** Tuttum. MU bilanço 5 gün sonra (bu tur kritik), AMD RSI 73.0 (düzeltme riski yüksek). **Sapma yok.**

**SAPMA YOK.** Geçen tur söylediklerimin hepsini yaptım.

**2. Geçen turdaki tezin yanlış çıktığı yer — YANLIŞ ÇIKMADI, hatta ÇOK daha güçlü çıktı:**

**AMD momentum beklentisi:** Geçen tur (#9) "AMD momentum devam ediyor mu? RSI 65.4 (aşırı alıma yakın) — düzeltme riski" demiştim. Bu tur AMD momentum PATLAMASI yaptı: haftalık +%12.6, aylık +%32.3, RSI 73.0 (aşırı alıma GİRDİ). **Yanılmadım — momentum devam etti, ama beklediğimden ÇOK daha güçlü çıktı.** Geçen tur "RSI 65.4 aşırı alıma yakın, düzeltme riski" demiştim ama AMD düzeltme yapmak yerine momentum patlaması yaptı. **Sebep:** Trump-Xi teknoloji zirvesi (geopolitik risk azalması), Meta Muse (AMD'ye yönelim), yarı iletken sektör rallisi — üç güçlü katalizör aynı anda geldi. **Öğrendiğim: RSI 65+ olan pozisyonda "düzeltme riski" demek, "kesinlikle düzelecek" demek değildir — güçlü katalizörler gelirse (Trump-Xi gibi makro olay) momentum RSI 70'i aşabilir. Ancak RSI 73.0 şimdi gerçekten aşırı alım bölgesinde — bir sonraki tur düzeltme riski ÇOK yüksek.**

**NVDA toparlanma tahmini:** Geçen tur "NVDA toparlanma trendi devam ediyor mu?" demiştim. Bu tur toparlanma devam etti (+%1.3 haftalık, 50g +%4.3 üzerinde). **Doğru çıktı — iki haftalık toparlanma trendi teyit edildi.** İlk hafta %-5.2 düşüş (tur #8) endişesi ortadan kalktı. İki haftalık toparlanma trendi, ilk ay performansı kabul edilebilir seviyeye yaklaşıyor (giriş 230.36$ → şimdi 225.07$, %-2.3 kayıp — geçen tur %-3.5'ten iyileşti).

**MU bilanço yaklaşımı:** Geçen tur "MU bilanço 11 gün sonra" demiştim, bu tur bilanço 5 gün sonra. MU güçlü toparlanma yaptı (+%6.5 haftalık), analist beklentileri yükseldi ("Q4 Earnings Are Likely to Boost the 'Strong Buy' Case"). **Bilanço riski iki yönlü — bir sonraki tur (3 Ekim) bilançonun sonucu belli olacak ve değerlendireceğim.**

**3. Bu turda verdiğim kararın beni yanıltabileceği yer:**

**AMD'yi tutma kararı (RSI 73.0 aşırı alım, ekleme yapmama):** AMD RSI 73.0 aşırı alım bölgesinde — teknik olarak kısa vadede düzeltme riski ÇOK yüksek. Eğer AMD bir sonraki turda momentum patlaması devam ederse (örn. RSI 75-80'e çıkar, %+15 daha yapar, 725$ civarı), "RSI 73.0'da ekleme yapmalıydım, momentum devam ediyordu" diye pişman olabilirim. Gerekçem: (1) RSI 70 üzeri teknik olarak aşırı alım — sağlıklı düzeltme 60-65'e geri dönüş beklenir. RSI 73.0'da ekleme yapmak aşırı alımda kovalamak demektir, disiplinsiz. (2) Geçen tur "RSI 65.4 düzeltme riski" dedim, AMD düzeltme yerine RSI 73.0'a çıktı — ama bu bir kez daha tekrarlanacak diye bir kural yok. Güçlü katalizörler (Trump-Xi) aşırı alımı tetikledi, artık katalizör kalmadı (bir sonraki büyük olay MU bilançosu). (3) AMD ağırlık %22.5 (ikinci en büyük pozisyon) — bu ağırlıkta ekleme yapmak portföy riskini çok artırır (AMD düzeltirse portföy %-3-4 etkilenir). **Risk kabul ediyorum: AMD momentum devam ederse ekleme fırsatı kaçırırım. Ama RSI 73.0 aşırı alımda ekleme disiplinsiz — düzeltme beklemek daha doğru (eğer %-10-15 düzeltirse 550$ civarı ekleme fırsatı).**

**MU'ya ekleme yapmama kararı (bilanço 5 gün sonra):** MU 50g'nin +%14.9 üzerinde, haftalık +%6.5 güçlü toparlanma, analist beklentileri yüksek. Eğer MU bilanço çok güçlü çıkar ve +%20 yaparsa (örn. 1300$ civarı), "bilanço öncesi 1082$ civarındayken ekleme yapmalıydım" diye pişman olabilirim. Gerekçem: (1) **Bilanço riski iki yönlü:** Güçlü bilanço +%20 yapabilir AMA zayıf bilanço %-10-15 düşüş yapabilir. Bilanço 5 gün sonra — çok yakın. Bilanço öncesi ekleme yapmak bilanço riskini artırır. (2) Talimat bilanço kuralı: "1 haftadan az kala yeni tam pozisyon açılmaz" — 5 gün bu sınıra çok yakın (7 gün = 1 hafta). Kural "yeni tam pozisyon" diyor, "ekleme" demez AMA bilanço öncesi ekleme aynı riski taşır (bilanço zayıf çıkarsa kayıp büyür). (3) MU ağırlık %33.7 (en büyük pozisyon) — bu ağırlıkta ekleme yapmak portföy riskini çok artırır ve konsantrasyonu aşırıya taşır (örn. %40+'ya çıkar). **Risk kabul ediyorum: MU bilanço güçlü çıkarsa ekleme fırsatı kaçırırım. Ama bilanço riski iki yönlü, 5 gün çok yakın, ağırlık zaten en yüksek — bilanço sonrası düzeltme fırsatı beklemek daha disiplinli (eğer bilanço zayıf çıkar ve %-10-15 düşerse 900$ civarı ekleme fırs fırsatı).**

**NVDA'ya ekleme yapmama kararı (toparlanma trendi devam ediyor):** NVDA iki haftalık toparlanma trendi devam ediyor (+%1.8 geçen tur, +%1.3 bu tur), 50g'yi koruyor ve genişletiyor (+%4.3 üzerinde). Eğer NVDA bir sonraki turlarda +%15 daha yaparsa (örn. 260$ civarı, giriş fiyatını aşar), "toparlanma trendi açıktı, 225$ civarındayken ekleme yapmalıydım" diye pişman olabilirim. Gerekçem: (1) NVDA hala giriş fiyatının altında (giriş 230.36$ → şimdi 225.07$, %-2.3 kayıp). İlk ay performansı henüz tamamlanmadı — üç haftalık toparlanma trendi olumlu ama giriş fiyatına ulaşmadan "toparlanma teyit edildi" demek erken. (2) Stop mesafesi %+18.5 (rahat ama MU/AMD/ANET'e göre en dar) — ekleme yapmak yerine izlemek daha disiplinli. (3) Nakit MU bilanço ve AMD düzeltme fırsatı için bekleniyor — ikisi de bir-iki tur içinde gerçekleşebilir, daha stratejik fırsatlar. **Risk kabul ediyorum: NVDA toparlanma devam ederse ekleme fırsatı kaçırırım. Ama henüz giriş fiyatına ulaşmadı, ilk ay performansı tamamlanmadı — bir-iki hafta daha toparlanma devam ederse giriş fiyatına ulaşır, o zaman ekleme değerlendiririm.**

**Yeni sembol taraması yapmama kararı (üçüncü turdur yok):** Son üç turdur (#8, #9, #10) yeni sembol taraması yapılmadı. Geçen turda TSM/MRVL/SNDK/MSFT/GOOGL listeden çıkarıldı, izleme listesi boş. Eğer bir sonraki turlarda yeni bir güçlü sembol ortaya çıkarsa (örn. PLTR, SMCI, TSM tekrar) ve +%30 yaparsa, "bu tur yeni sembol taraması yapmalıydım" diye pişman olabilirim. Gerekçem: (1) **Mevcut portföy ÇOK güçlü momentum kazandı** (AMD aylık +%32.3 patlaması, MU bilanço öncesi güçlü, ANET istikrarlı, NVDA toparlanma) — yeni sembol eklemek portföyü dağıtır ve mevcut momentumu zayıflatır. (2) **Odak bilanço ve düzeltme fırsatlarında:** MU bilanço 5 gün sonra (bir sonraki tur sonuç belli), AMD RSI 73.0 (düzeltme riski yüksek — bir-iki tur içinde olası). İki fırsat da bir-iki tur içinde gerçekleşebilir — nakit bu fırsatlar için hazır. (3) **Tema derinliği stratejisi:** Yeni sembol eklemek (tema genişliği) yerine mevcut pozisyonlara ekleme (tema derinliği) daha stratejik — mevcut pozisyonların tezleri güçlü, momentumları yüksek. **Risk kabul ediyorum: Yeni bir güçlü sembol taraması kaçırırsam fırsat kaybı olabilir. Ama mevcut portföy tarihi momentum seviyesinde (%+7.11 haftalık) — odak bilanço ve düzeltme fırsatlarında, tema derinliği stratejisi korunuyor.**

**Ders kalibrasyonu:**
- **Davranış değişikliği (üç bağımsız gözlem, aynı yön):** (1) AMD "son şans" uyarısı (tur #7), şart yerine getirildi (tur #8), tez GEÇERLİ'ye yükseldi. (2) Tur #9 AMD teyit edildi (50g'yi koruyor ve genişletiyor +%12.9). (3) Bu tur AMD momentum PATLAMASI (+%24.9 üzerinde, aylık +%32.3, RSI 73.0 aşırı alım). **Üç turda teyit: "Son şans" uyarısı + koşullu eylem planı işe yarıyor. Bir pozisyon zayıflıyorsa ama fundamentaller güçlüyse (AMD gibi), "son şans" uyarısı ver, şart yerine getirilirse tezi yükselt, momentum devam ederse izle.** **Ders ONAYLANDI ve GÜÇLÜ katalizör eklemesi:** AMD'nin momentum patlaması Trump-Xi teknoloji zirvesi ve Meta Muse gibi **makro/mega-cap katalizörlere** dayandı. Ders: Fundamentaller güçlüyse (AMD AI rampası) "son şans" uyarısı ver AMA makro katalizör gelirse (Trump-Xi) momentum RSI 70'i aşabilir — bu durumda panik satışı yapma, izle, ama RSI 73+ olunca ekleme yapma (aşırı alımda kovalamak disiplinsiz). Düzeltme bekle.

- **Teyit edildi (tur #8'den):** Yeni pozisyonun ilk hafta performansı kestirilmez (NVDA tur #8'de %-5.2 düşüş). Tur #9 toparlandı (+%1.8), bu tur toparlanma devam etti (+%1.3). **Ders teyit edildi: Yeni pozisyon ilk hafta düşerse panik satışı yapma — 50g'yi koruyor mu kontrol et. İki haftalık toparlanma trendi teyit olursa izlemeye devam (giriş fiyatına ulaşana kadar).** NVDA üç haftalık toparlanma trendi başladı — ilk ay performansı kabul edilebilir seviyeye yaklaşıyor.

- **Yeni hipotez (bu turdan):** AMD RSI 73.0 aşırı alım bölgesinde. Geçen tur "RSI 65.4 düzeltme riski" dedim, AMD çıktı RSI 73.0'a — güçlü katalizörler (Trump-Xi, Meta Muse) aşırı alımı tetikledi. **Ders (hipotez): RSI 65-70 arasında "düzeltme riski" demek kesin değildir — güçlü makro katalizör gelirse RSI 70'i aşabilir. Ancak RSI 70+ gerçek aşırı alım bölgesidir ve düzeltme riski ÇOK yüksektir. RSI 73.0'da ekleme yapma (aşırı alımda kovalamak), düzeltme bekle (%-10-15 düzeltme olası, 50g testi fırsatı).** Bir sonraki turda test edilecek: AMD düzeltir mi (RSI 60-65'e geri döner mi) yoksa momentum devam eder mi (RSI 75-80'e çıkar mı)?

**Sonraki gözden geçirme:** 3 Ekim 2026 (Cumartesi — bir sonraki haftalık tur). **EN KRİTİK TUR:** (1) **MU bilanço sonucu (30 Eylül Çarşamba, 3 gün önce açıklanacak) — bu turun ana olayı.** Bilanço güçlü mü, zayıf mı? Rehberlik nasıl? Fiyat tepkisi ne oldu? Bilanço sonrası ekleme fırsatı var mı (düşüş varsa 900$ civarı — 50g testi)? (2) **AMD düzeltme başladı mı? RSI 73.0'dan düştü mü?** 50g'yi koruyor mu yoksa kaybetti mi? Eğer düzeltme başladıysa (%-10-15, 550$ civarı — 50g testi) ekleme fırsatı. (3) NVDA toparlanma trendi devam ediyor mu? Giriş fiyatına ulaştı mı (230$ üzeri)? (4) ANET momentum devam ediyor mu? (5) **Nakit stratejisi netleşecek:** MU bilanço sonrası ve/veya AMD düzeltme sonrası ekleme kararı.
