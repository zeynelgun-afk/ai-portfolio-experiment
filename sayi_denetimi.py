#!/usr/bin/env python3
"""LLM çıktısındaki rakamları prompt'taki rakamlarla karşılaştır — halüsinasyon kapısı.

Neden var: `HAFTALIK_TALIMAT.md` "kaynaksız rakam yazma" diyor ve tur #7'de tam olarak
bu ihlal edildi — NVDA tezine hafızadan "%~80-90 pazar payı" yazıldı. Talimatın kendi
ilkesi bunun cevabını veriyor: **"Bir kuralın yazılı olması yetmiyorsa, o kural veriye
dönüştürülür."** Prompt bir güvenlik duvarı değildir; bu modül o kuralı koda çeviriyor.

Kural tek cümle: **çıktıdaki her rakam ya prompt'ta geçmeli, ya prompt'taki iki
rakamdan türetilebilmeli.** Türetme kasten geniş: talimat yüzdeyi tabanıyla yazmayı
zorunlu kılıyor, yani "50g'nin %+14.9 üzerinde" meşru bir hesaptır ve prompt'ta
o hâliyle geçmez — ikili oranlar izinli kümeye ekleniyor.

Yanlış pozitif riski bilinçli olarak kabul ediliyor: bir rakam haksız yere işaretlenirse
sonuç iddianın DEĞİŞMEMESİ olur (eski metin kalır), uydurma bir rakamın yazılması değil.
Kapı bu yönde hata yapacak şekilde kuruldu.
"""

import re

# Rakam biçimleri: 1,082.28 · 1.082,28 · 905.4 · 3.6 · -7 · 941
_BINLIK_NOKTA = re.compile(r"^\d{1,3}(?:\.\d{3})+(?:,\d+)?$")
_BINLIK_VIRGUL = re.compile(r"^\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
_SAYI = re.compile(r"\d[\d.,]*\d|\d")

# Sayım/sıra sayıları: "üç turdur", "2 ardışık kontrol", "3 gün". Pazar payı gibi
# uydurma bir oranı taşıyacak kadar büyük olmadıkları için serbest.
SAYIM_UST_SINIR = 12
# Yıl gibi görünen sayılar prompt'ta tarih olarak geçiyor; ayrıca serbest bırakılmaz —
# tarih zaten prompt'ta yazılı olduğu için izinli kümeye kendiliğinden girer.

# Tolerans yalnızca MUTLAK. Oransal tolerans denendi ve kapıyı işlevsiz yapıyordu:
# 2026 için %0.1 oransal tolerans 2.03 demek, yani uydurma bir "2027" sessizce
# geçiyordu. Mutlak 0.051, yazım yuvarlamasını (3.65 → "3.6", 905.4 → "905.40")
# affetmeye yeter ve komşu tam sayıyı yutmaz.
# Gösterge parametreleri iddia değil, terimdir: "50g ortalama", "RSI(14)",
# "20 günlük hacim", "200g". Model bunları veri bloğunda geçmeseler de yazacaktır ve
# hiçbiri piyasa hakkında bir sayı iddiası taşımaz. Kapıya takılmaları saf yanlış
# pozitif olurdu — meşru bir yorumun reddedilmesi, kapının kendi amacına zarar verir.
SERBEST_TERIMLER = {14, 20, 50, 200}

MUTLAK_TOLERANS = 0.051

# Türetme yalnızca AYNI BÜYÜKLÜK MERTEBESİNDEKİ çiftler için yapılır. Sınırsız
# bırakıldığında (ilk deneme) 14 rakamdan ~2200 izinli değer çıkıyordu ve yüzde
# uzayı öyle yoğunlaşıyordu ki tur #7'nin gerçek halüsinasyonu ("%80-90 pazar payı")
# "türetilebilir" sayılıp kapıdan geçiyordu. Fiyatı fiyatla kıyaslamak anlamlı;
# fiyatı adetle kıyaslamak değil.
TURETME_MERTEBE_ALT = 0.1
TURETME_MERTEBE_UST = 10.0
# Türetme tabanına yalnızca ölçüm büyüklüğündeki sayılar girer. Tarih ve tanımlayıcı
# parçaları (2026-09-30'un 9'u, seans_ici_5m'in 5'i) türetmeye sokulduğunda
# (9/5-1)*100 = 80 çıkıyordu ve tur #7'nin "%80-90 pazar payı" uydurması tam bu yolla
# kapıdan geçiyordu. Bu eşiğin altındaki tam sayılar zaten sayım olarak serbest,
# yani tabandan çıkarmak hiçbir meşru rakamı kaybettirmez.
TURETME_TABAN_ALT = 12


def _normalize(ham):
    """'1.082,28' → 1082.28 · '1,082.28' → 1082.28 · '905.4' → 905.4"""
    s = ham.strip(".,")
    if not s:
        return None
    if _BINLIK_NOKTA.match(s):
        s = s.replace(".", "").replace(",", ".")
    elif _BINLIK_VIRGUL.match(s):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
        if s.count(".") > 1:  # 1.082.28 gibi belirsiz biçim — ayıklama
            s = s.replace(".", "", s.count(".") - 1)
    try:
        return float(s)
    except ValueError:
        return None


def sayilari_ayikla(metin):
    """Metindeki rakamları (ham_metin, deger) listesi olarak döndür."""
    bulunan = []
    for eslesme in _SAYI.finditer(metin or ""):
        ham = eslesme.group(0)
        deger = _normalize(ham)
        if deger is not None:
            bulunan.append((ham, deger))
    return bulunan


def izinli_kume(*metinler):
    """Prompt'taki rakamlar + onlardan türetilebilen oranlar/farklar.

    Türetilenler: her (a, b) çifti için %değişim, oran ve fark. Hepsi 1 ve 2
    basamağa yuvarlanmış hâlleriyle eklenir, çünkü talimat yüzdeleri yuvarlatarak
    yazdırıyor.
    """
    ham = set()
    for m in metinler:
        for _, deger in sayilari_ayikla(m):
            ham.add(deger)

    izinli = set(ham)
    for a in ham:
        izinli.update(_yazim_bicimleri(a))
    liste = [d for d in ham if abs(d) > TURETME_TABAN_ALT]
    for a in liste:
        for b in liste:
            if a == b or not b:
                continue
            oran = abs(a / b)
            if not (TURETME_MERTEBE_ALT <= oran <= TURETME_MERTEBE_UST):
                continue  # farklı mertebe: kıyaslamanın anlamı yok
            for tureti in ((a / b - 1) * 100, a / b, a - b):
                if not (-1e9 < tureti < 1e9):
                    continue
                # Türetilenlere kırpma UYGULANMAZ, yalnızca 1-2 basamak yuvarlama.
                # Tam yazım biçimi seti denendi ve izinli kümeyi 624'e çıkarıp iki
                # haneli tam sayıların %40'ını kazara geçirdi. Talimat zaten yüzdeyi
                # tabanıyla ve ondalıklı yazdırıyor ("%-3.8"); türetilmiş bir yüzdenin
                # çıplak tam sayı olarak yazılması olağan değil.
                izinli.update({round(tureti, 1), round(tureti, 2),
                               round(abs(tureti), 1), round(abs(tureti), 2)})
    return izinli


def _yazim_bicimleri(a):
    """Bir rakamın meşru yazım biçimleri: yuvarlanmış VE kırpılmış hâlleri.

    Eşiği 941.62 olan bir koşul için model "941 üstü" yazabilir — yuvarlamak 942
    verir, kırpmak 941. İkisi de meşru yazımdır; yalnızca yuvarlamayı kabul etmek
    kapıyı yanlış yere kapatıyordu (gerçek testte tam bu yüzden bir karar reddedildi).
    """
    bicimler = {a, abs(a)}
    for n in (0, 1, 2):
        for x in (a, abs(a)):
            bicimler.add(round(x, n) if n else float(round(x)))
            kat = 10 ** n
            bicimler.add(int(x * kat) / kat)  # kırpma
    return bicimler


def _izinli_mi(deger, izinli):
    if abs(deger) <= SAYIM_UST_SINIR and float(deger).is_integer():
        return True  # sayım/sıra sayısı
    if deger in SERBEST_TERIMLER:
        return True  # gösterge parametresi (50g, RSI(14), 20g hacim, 200g)
    for a in izinli:
        if abs(deger - a) <= MUTLAK_TOLERANS:
            return True
    return False


def kaynaksiz_rakamlar(cikti, *kaynaklar):
    """Çıktıda olup kaynaklarda bulunmayan/türetilemeyen rakamları döndür.

    Dönen: [(ham_metin, deger), ...] — boş liste "temiz" demektir.
    """
    izinli = izinli_kume(*kaynaklar)
    kaynaksiz, gorulen = [], set()
    for ham, deger in sayilari_ayikla(cikti):
        if _izinli_mi(deger, izinli) or deger in gorulen:
            continue
        gorulen.add(deger)
        kaynaksiz.append((ham, deger))
    return kaynaksiz


def geri_besleme_metni(kaynaksiz):
    """Modele ikinci denemede verilecek düzeltme talimatı."""
    liste = ", ".join(ham for ham, _ in kaynaksiz)
    return (
        "Önceki yanıtında şu rakamlar sana verilen veri bloğunda YOK ve o bloktaki "
        f"rakamlardan da türetilemiyor: {liste}.\n"
        "Bunlar kaynaksız rakamdır ve deneyin tüzüğü bunu yasaklar. Yanıtı yeniden yaz: "
        "bu rakamları tamamen çıkar ya da yerlerine veri bloğunda GEÇEN rakamları koy. "
        "Bir rakamı doğrulayamıyorsan cümleyi rakamsız kur — tez rakamsız da kurulur. "
        "Yine aynı şemada, yalnızca JSON döndür."
    )
