#!/usr/bin/env python3
"""İzleme listesi erteleme sayaçlarını KARAR_GUNLUGU.md'den hesaplar.

Neden ayrı bir script: talimat sürüm 6 sayacı zorunlu kıldı, tur #7 sayacı doğru
formatta yazdı ama TSM/MRVL/SNDK için 1/3'ten başlattı — oysa üçü de tur #4'ten beri
erteleniyordu. Sayaç, sayanın kendi beyanı olduğu sürece sıfırlanabiliyor. Bu yüzden
artık AI'ın yazdığı değil, önüne konan bir veri: guncelle.py bunu RAPOR.md'ye basar.

Sayım kuralı (talimat madde D'nin mekanik karşılığı):
  N = sembol veri setinde dururken pozisyon açılmadan geçen tur sayısı.
      Sıfırlanması için bir "sıfırlama olayı" gerekir: o sembolde işlem (portfoy.json
      islem_gecmisi) ya da sembolün listeden çıkarılması (günlükte "LİSTEDEN ÇIKAR").
      Tanım kasten mekanik: neyin "gerçek değerlendirme" sayıldığı yoruma açık olsaydı
      sayaç yeniden pazarlık konusu olurdu. Veri seti = haftalik_veri.py'deki liste;
      listeden çıkarma kararı prose'da verilir, script onu okur.
"""

import json
import os
import re
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
GUNLUK_YOLU = os.path.join(BASE, "KARAR_GUNLUGU.md")
PF_YOLU = os.path.join(BASE, "portfoy.json")
VERI_YOLU = os.path.join(BASE, "veri_haftalik.json")

ESIK = 3  # üçüncü ertelemede: ya pozisyon aç ya listeden çıkar

AY = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5,
    "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9,
    "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12,
}

BASLIK = re.compile(r"^## #(\d+) — (\d{1,2}) (\S+) (\d{4})", re.MULTILINE)


def turlari_ayikla(metin):
    """Günlüğü [(tur_no, tarih, gövde), ...] listesine böler."""
    eslesmeler = list(BASLIK.finditer(metin))
    turlar = []
    for i, m in enumerate(eslesmeler):
        ay = AY.get(m.group(3).lower())
        if ay is None:
            continue
        son = eslesmeler[i + 1].start() if i + 1 < len(eslesmeler) else len(metin)
        turlar.append((
            int(m.group(1)),
            date(int(m.group(4)), ay, int(m.group(2))),
            metin[m.start():son],
        ))
    return turlar


def sembol_gecer(govde, sembol):
    """Sembol bu turda geçiyor mu (kelime sınırıyla — MU'nun 'MU' içinde kaybolmaması için)."""
    return re.search(rf"\b{re.escape(sembol)}\b", govde) is not None


def sayaclari_hesapla(turlar, islem_gecmisi, adaylar):
    """Her aday sembol için (durum, N, cikarildigi_tur) döndürür."""
    sonuc = {}
    for sembol in adaylar:
        sifirlama = [
            date.fromisoformat(i["tarih"])
            for i in islem_gecmisi if i["sembol"] == sembol
        ]
        cikarildi_tur = None
        for no, tarih, govde in turlar:
            for satir in govde.splitlines():
                if sembol_gecer(satir, sembol) and "LİSTEDEN ÇIKAR" in satir.upper():
                    cikarildi_tur = no
                    sifirlama.append(tarih)

        son_sifirlama = max(sifirlama) if sifirlama else None
        if son_sifirlama is None:
            sayilan = [no for no, _, _ in turlar]
        else:
            sayilan = [no for no, tarih, _ in turlar if tarih > son_sifirlama]

        if cikarildi_tur is not None and (not sayilan or max(sayilan) <= cikarildi_tur):
            sonuc[sembol] = ("cikarildi", len(sayilan), cikarildi_tur)
        else:
            sonuc[sembol] = ("izlemede", len(sayilan), None)
    return sonuc


def adaylari_bul(pf, veri):
    """İzleme adayları = veri setindeki semboller eksi açık pozisyonlar."""
    pozisyonlar = {p["sembol"] for p in pf["pozisyonlar"]}
    return [s for s in veri if s != "_meta" and s not in pozisyonlar]


def rapor_blogu():
    """RAPOR.md'ye gömülecek metni üretir. Veri yoksa boş döner."""
    if not (os.path.exists(GUNLUK_YOLU) and os.path.exists(VERI_YOLU)):
        return ""
    with open(GUNLUK_YOLU, encoding="utf-8") as f:
        turlar = turlari_ayikla(f.read())
    with open(PF_YOLU, encoding="utf-8") as f:
        pf = json.load(f)
    with open(VERI_YOLU, encoding="utf-8") as f:
        veri = json.load(f)

    adaylar = adaylari_bul(pf, veri)
    if not turlar or not adaylar:
        return ""

    sayaclar = sayaclari_hesapla(turlar, pf.get("islem_gecmisi", []), adaylar)
    satirlar = []
    for sembol in adaylar:
        durum, n, cikarildi_tur = sayaclar[sembol]
        if durum == "cikarildi":
            satirlar.append(f"| {sembol} | — | tur #{cikarildi_tur}'de listeden çıkarıldı |")
        else:
            not_ = ("**EŞİK AŞILDI — bu tur ya pozisyon aç ya listeden çıkar**"
                    if n >= ESIK else "")
            satirlar.append(f"| {sembol} | {n}/{ESIK} | {not_} |")

    return f"""
## Erteleme sayaçları

KARAR_GUNLUGU.md'den hesaplandı (sayaclar.py) — bu sayılar turda yeniden üretilmez,
buradan alınır. Sıfırlanması için ya pozisyon açılmış ya sembol listeden çıkarılmış olmalı.

| Sembol | Ertelendi | Not |
|---|---|---|
{chr(10).join(satirlar)}
"""


if __name__ == "__main__":
    print(rapor_blogu() or "(hesaplanamadı: günlük ya da veri dosyası yok)")
