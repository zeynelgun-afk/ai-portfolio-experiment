#!/usr/bin/env python3
"""Seans içi otonom işlemi UYGULAYAN katman — deterministik, LLM yok.

Neden ayrı bir script: kararın içeriği AI'ın (tüzük sürüm 2), ama uygulaması
aritmetik. LLM'in doğrudan `portfoy.json`'a yazması, tek bir bozuk yfinance barının
gerçek bir işleme dönüşmesi demekti. Burada karar aynen uygulanır — ama önce
aritmetiği ve veri bütünlüğü doğrulanır. Bu bir karar kısıtı DEĞİLDİR: hiçbir
doğrulama "bu işlem yanlış" demez, yalnızca "bu sayılarla bu işlem yapılamaz" der.

Fiyat LLM'den ALINMAZ. Dolgu fiyatı `durum/ihlaller.json`'daki, dedektörün ölçtüğü
seans içi fiyattır — modelin cümlesinden değil, ölçümden gelir.

Uygulanmama nedenleri (hepsi günlüğe ve bekleyen notlara yazılır, sessiz düşüş yok):
  * seans kapalı (işlem ertelenir, karar Cumartesi turuna not olur)
  * fiyat kaynağı canlı değil (`veri_kaynagi != seans_ici_5m`)
  * aritmetik tutmuyor (nakit yetmiyor, adet elindekinden fazla)
  * aynı gün aynı yönde işlem zaten yapıldı (islem_kilidi.json)

Kullanım:
    python islem_uygula.py
    python islem_uygula.py --dry-run     # portfoy.json'a yazmaz, ne yapacağını basar
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
PF_YOLU = os.path.join(BASE, "portfoy.json")
GUNLUK_YOLU = os.path.join(BASE, "KARAR_GUNLUGU.md")

CANLI_KAYNAK = "seans_ici_5m"
EN_KUCUK_ADET = 1e-6


def env(ad, varsayilan=""):
    return (os.environ.get(ad) or varsayilan).strip()


def simdi():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%MZ")


def json_oku(yol, varsayilan):
    if not os.path.exists(yol):
        return varsayilan
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as hata:
        print(f"UYARI: {os.path.basename(yol)} okunamadı ({hata})")
        return varsayilan


def json_yaz(yol, veri):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")


def sayi(deger):
    try:
        d = float(deger)
    except (TypeError, ValueError):
        return None
    return d if d == d and abs(d) != float("inf") else None


# ------------------------------------------------------------------- doğrulama


def dogrula(karar, pf, veri, seans, kilitler, bugun):
    """(uygulanabilir, ret_nedeni, ayrintilar) döndürür. Karar içeriğini yargılamaz."""
    sym = karar.get("sembol")
    islem = karar.get("islem")
    if islem == "TUT":
        return False, "karar TUT — uygulanacak işlem yok", {}

    d = veri.get(sym, {})
    fiyat = sayi(d.get("fiyat"))
    if fiyat is None or fiyat <= 0:
        return False, f"{sym} için ölçülmüş fiyat yok — işlem yapılmadı", {}
    if d.get("veri_kaynagi") != CANLI_KAYNAK:
        return False, (f"fiyat kaynağı canlı değil ({d.get('veri_kaynagi')}) — "
                       "seans içi işlem yapılmadı"), {}
    if not seans:
        return False, "seans kapalı — işlem bir sonraki seansa/Cumartesi turuna kaldı", {}

    kilit = f"{bugun.isoformat()}:{sym}:{islem}"
    if kilit in kilitler:
        return False, f"aynı gün aynı yönde işlem zaten yapıldı ({kilit})", {}

    pozlar = {p["sembol"]: p for p in pf.get("pozisyonlar", [])}
    nakit = sayi(pf.get("nakit_usd")) or 0.0

    if islem in ("SAT", "KIRP"):
        poz = pozlar.get(sym)
        if not poz:
            return False, f"{sym} portföyde yok — satılacak pozisyon yok", {}
        elde = sayi(poz.get("adet")) or 0.0
        adet = elde if islem == "SAT" else sayi(karar.get("adet"))
        if adet is None or adet <= 0:
            return False, f"geçersiz adet ({karar.get('adet')!r})", {}
        if adet > elde + EN_KUCUK_ADET:
            return False, f"adet elindekinden fazla ({adet} > {elde})", {}
        return True, None, {"adet": min(adet, elde), "fiyat": fiyat,
                            "tutar": min(adet, elde) * fiyat, "kilit": kilit}

    if islem == "AL":
        tutar = sayi(karar.get("tutar_usd"))
        if tutar is None or tutar <= 0:
            return False, f"geçersiz tutar_usd ({karar.get('tutar_usd')!r})", {}
        if tutar > nakit + 0.01:
            return False, f"nakit yetmiyor ({tutar:.2f} $ > {nakit:.2f} $)", {}
        return True, None, {"adet": tutar / fiyat, "fiyat": fiyat, "tutar": tutar,
                            "kilit": kilit}

    return False, f"bilinmeyen işlem ({islem!r})", {}


# --------------------------------------------------------------------- uygulama


def uygula(karar, pf, ayrinti, an):
    """portfoy.json'u yerinde güncelle ve islem_gecmisi kaydını döndür."""
    sym, islem = karar["sembol"], karar["islem"]
    adet, fiyat, tutar = ayrinti["adet"], ayrinti["fiyat"], ayrinti["tutar"]
    pozlar = {p["sembol"]: p for p in pf["pozisyonlar"]}

    if islem in ("SAT", "KIRP"):
        poz = pozlar[sym]
        kalan = round((sayi(poz["adet"]) or 0.0) - adet, 6)
        pf["nakit_usd"] = round((sayi(pf.get("nakit_usd")) or 0.0) + tutar, 2)
        if kalan <= EN_KUCUK_ADET:
            pf["pozisyonlar"] = [p for p in pf["pozisyonlar"] if p["sembol"] != sym]
            islem_adi = "SAT"
        else:
            oran = kalan / (kalan + adet)
            poz["adet"] = kalan
            # Maliyet oransal düşer; giriş fiyatı değişmez (kısmi satış ortalamayı bozmaz).
            poz["maliyet_usd"] = round((sayi(poz.get("maliyet_usd")) or 0.0) * oran, 2)
            islem_adi = "KIRP"
    else:  # AL — mevcut pozisyona ekleme ya da yeni pozisyon
        pf["nakit_usd"] = round((sayi(pf.get("nakit_usd")) or 0.0) - tutar, 2)
        poz = pozlar.get(sym)
        if poz:
            eski_adet = sayi(poz["adet"]) or 0.0
            eski_maliyet = sayi(poz.get("maliyet_usd")) or 0.0
            yeni_adet = round(eski_adet + adet, 6)
            poz["adet"] = yeni_adet
            poz["maliyet_usd"] = round(eski_maliyet + tutar, 2)
            poz["giris_fiyati"] = round(poz["maliyet_usd"] / yeni_adet, 2)
        else:
            pf["pozisyonlar"].append({
                "sembol": sym, "adet": round(adet, 6), "giris_fiyati": round(fiyat, 2),
                "giris_tarihi": an.date().isoformat(), "maliyet_usd": round(tutar, 2),
                "agirlik_hedef_pct": None,
                "stop_haftalik_kapanis": sayi(karar.get("yeni_stop")),
                "sonraki_bilanco": None,
            })
            poz = pf["pozisyonlar"][-1]
        islem_adi = "AL"

    yeni_stop = sayi(karar.get("yeni_stop"))
    if yeni_stop and poz in pf["pozisyonlar"]:
        poz["stop_haftalik_kapanis"] = yeni_stop

    kayit = {
        "tarih": an.date().isoformat(),
        "saat_utc": an.strftime("%H:%M"),
        "islem": islem_adi,
        "sembol": sym,
        "adet": round(adet, 6),
        "fiyat": round(fiyat, 2),
        "tutar_usd": round(tutar, 2),
        "kaynak": "seans_ici_otonom",
        "not": karar.get("gerekce", "")[:400],
    }
    pf.setdefault("islem_gecmisi", []).append(kayit)
    pf["son_guncelleme"] = an.date().isoformat()
    return kayit


def gunluge_yaz(an, uygulananlar, reddedilenler):
    """Seans içi kararlar KARAR_GUNLUGU.md'ye ayrı bir kayıt tipiyle düşer.

    Tüzük madde 1: her karar günlüğe yazılır. Seans içi kararın haftalık turdan
    ayırt edilebilmesi için başlık 'S#' ön ekiyle numaralanır.
    """
    if not uygulananlar and not reddedilenler:
        return
    with open(GUNLUK_YOLU, encoding="utf-8") as f:
        mevcut = f.read()
    sira = mevcut.count("· SEANS İÇİ KARAR") + 1
    satirlar = [f"\n## S#{sira} — {an.date().isoformat()} {an.strftime('%H:%M')} UTC "
                "· SEANS İÇİ KARAR\n",
                "Bu kayıt haftalık tur değil, olay güdümlü seans içi turdur "
                "(`dedektor.py` → `yeniden_degerlendir.py` → `islem_uygula.py`). "
                "Eşik aşıldı, 2 ardışık kontrolde teyit edildi, tez seviyesi "
                "yeniden değerlendirme tetiklendi.\n"]
    for k, ayrinti in uygulananlar:
        satirlar += [
            f"### {k['sembol']} — {ayrinti['islem_adi']} (UYGULANDI)\n",
            f"- **Tetikleyici:** {k.get('tetikleyici', '-')}",
            f"- **Dolgu:** {ayrinti['adet']:.4f} adet × {ayrinti['fiyat']:.2f} $ "
            f"= {ayrinti['tutar']:,.2f} $ (fiyat kaynağı: dedektörün ölçtüğü seans içi bar)",
            f"- **Tez değerlendirmesi:** {k.get('tez_degerlendirmesi', '-')}",
            f"- **Gerekçe:** {k.get('gerekce', '-')}",
            f"- **Tezin yanlış olduğunu gösterecek işaret:** "
            f"{k.get('carpitma_isareti', '-')}",
            f"- **Model:** {k.get('model', '-')}\n",
        ]
    for k, neden in reddedilenler:
        satirlar += [
            f"### {k.get('sembol')} — {k.get('islem')} (UYGULANMADI)\n",
            f"- **Tetikleyici:** {k.get('tetikleyici', '-')}",
            f"- **Uygulanmama nedeni:** {neden}",
            f"- **Modelin gerekçesi (kayda geçer, uygulanmadı):** "
            f"{k.get('gerekce', '-')}\n",
        ]
    with open(GUNLUK_YOLU, "a", encoding="utf-8") as f:
        f.write("\n".join(satirlar))


def not_ekle(yol, baslik, govde):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "a", encoding="utf-8") as f:
        f.write(f"\n## {baslik}\n\n{govde}\n")


def main():
    ap = argparse.ArgumentParser(description="Seans içi otonom kararı uygula")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--durum-dizin", default=os.path.join(BASE, "durum"))
    args = ap.parse_args()

    karar_yolu = os.path.join(args.durum_dizin, "bekleyen_karar.json")
    kilit_yolu = os.path.join(args.durum_dizin, "islem_kilidi.json")
    notlar_yolu = os.path.join(args.durum_dizin, "bekleyen_notlar.md")
    ihlal_yolu = os.path.join(args.durum_dizin, "ihlaller.json")

    paket = json_oku(karar_yolu, {})
    kararlar = paket.get("kararlar", [])
    if not kararlar:
        print("Uygulanacak karar yok")
        return 0

    ihlaller = json_oku(ihlal_yolu, {})
    veri = ihlaller.get("veri", {})
    seans = bool(ihlaller.get("seans_ici"))
    pf = json_oku(PF_YOLU, None)
    if pf is None:
        print("HATA: portfoy.json okunamadı — işlem yapılmadı")
        return 1

    an = simdi()
    bugun = an.date()
    kilitler = json_oku(kilit_yolu, {})
    uygulananlar, reddedilenler = [], []

    for karar in kararlar:
        tamam, neden, ayrinti = dogrula(karar, pf, veri, seans, kilitler, bugun)
        etiket = f"{karar.get('sembol')} {karar.get('islem')}"
        if not tamam:
            print(f"✗ {etiket}: {neden}")
            if karar.get("islem") != "TUT":
                reddedilenler.append((karar, neden))
            continue
        if args.dry_run:
            print(f"[dry-run] {etiket}: {ayrinti['adet']:.4f} adet × "
                  f"{ayrinti['fiyat']:.2f} $ = {ayrinti['tutar']:,.2f} $")
            continue
        kayit = uygula(karar, pf, ayrinti, an)
        ayrinti["islem_adi"] = kayit["islem"]
        kilitler[ayrinti["kilit"]] = iso(an)
        uygulananlar.append((karar, ayrinti))
        print(f"✓ {etiket} uygulandı: {kayit['adet']} adet × {kayit['fiyat']} $ "
              f"= {kayit['tutar_usd']} $ · nakit {pf['nakit_usd']} $")

    if args.dry_run:
        return 0

    if uygulananlar:
        json_yaz(PF_YOLU, pf)
        json_yaz(kilit_yolu, kilitler)
    gunluge_yaz(an, uygulananlar, reddedilenler)
    for karar, neden in reddedilenler:
        not_ekle(notlar_yolu,
                 f"{iso(an)} · {karar.get('sembol')} · KARAR UYGULANMADI",
                 f"**Önerilen işlem:** {karar.get('islem')}\n\n"
                 f"**Uygulanmama nedeni:** {neden}\n\n"
                 f"**Modelin gerekçesi:** {karar.get('gerekce', '-')}\n\n"
                 "Cumartesi turu bu kararı yeniden değerlendirir.")

    # Karar paketi tüketildi; bir sonraki koşumda tekrar uygulanmasın.
    os.remove(karar_yolu)

    gh_out = env("GITHUB_OUTPUT")
    if gh_out:
        ozet = "; ".join(f"{k['sembol']} {a['islem_adi']} {a['adet']:.4f}@{a['fiyat']:.2f}"
                         for k, a in uygulananlar) or "yok"
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"islem_sayisi={len(uygulananlar)}\n")
            f.write(f"islem_ozet={ozet}\n")
            f.write(f"red_sayisi={len(reddedilenler)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
