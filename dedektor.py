#!/usr/bin/env python3
"""Olay güdümlü yeniden değerlendirme — deterministik değişim dedektörü.

Neden var: Cumartesi turunda yazılan yorumlar hafta içi bayatlıyordu. Fiyat Pazartesi
50 günlük ortalamanın altına sarktığında `tezler.json`'da hâlâ "ortalamanın %+14.9
üzerinde" yazıyordu. İlke: **veri sürekli akar, yorum yalnızca anlam değişince
güncellenir.**

Bu dosyada LLM YOK. Burada yalnızca `tezler.json`'daki geçerlilik koşulları ölçülür ve
eşiğin aşılıp aşılmadığına karar verilir. Aşıldıysa çıkış koduyla sinyal verilir;
yorumu kimin nasıl yeniden yazacağı `yeniden_degerlendir.py`'nin işi.

Çıkış kodları (workflow bunlara bakar):
    0  → değişiklik yok (ya da yalnızca `uyari` seviyesinde işaret)
    10 → `iddia` seviyesi: tek bir iddia yeniden yazılacak
    20 → `tez` seviyesi: pozisyonun tüm tezi yeniden değerlendirilecek

Flapping önleme (üçü birlikte):
  * Histerezis    — bir koşul ihlalde sayılmak için 2 ardışık kontrolde ihlalde kalmalı.
                    Veri şüpheliyse (fiyat önceki kapanıştan %25'ten fazla sapmışsa)
                    3 ardışık kontrol gerekir; bozuk bir bar bir turluk gecikmeyle
                    ayıklanır, gerçek bir çöküş 60 dakikada yine yakalanır.
  * Geri dönüş bandı — eşiğin %1'i. 850 altı tetikler, temizlenmesi için 858.5 üstü
                    gerekir; eşiğin iki yanında salınan fiyat sinyal üretmez.
  * Cooldown      — aynı iddia 4 saat içinde ikinci kez yeniden yazılmaz.

Kullanım:
    python dedektor.py                        # canlı seans içi veri
    python dedektor.py --tam-yenileme         # eşik aşılmasa da tüm iddiaları gözden geçir
    python dedektor.py --dry-run              # hiçbir durum dosyası yazılmaz
    python dedektor.py --sabit-veri tests/ornek.json   # ağ yok, veri dosyadan
"""

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, time, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
TEZLER_YOLU = os.path.join(BASE, "tezler.json")
PF_YOLU = os.path.join(BASE, "portfoy.json")

# Geri dönüş bandı: eşiğin %1'i. Tek bir sabit, çünkü her koşul tipi için ayrı bant
# tanımlamak bandı pazarlık konusu yapardı.
BANT_ORANI = 0.01
COOLDOWN_SAAT = 4
GEREKEN_ARDISIK = 2
GEREKEN_ARDISIK_SUPHELI = 3
# Fiyat önceki kapanıştan bu kadar saparsa veri şüphelidir (bozuk yfinance barı).
SUPHELI_SAPMA_PCT = 25.0

SIDDET_KOD = {"uyari": 0, "iddia": 10, "tez": 20}

# ABD seansı (UTC). Yaz saati farkını kovalamıyoruz: pencere kasten geniş tutuldu,
# dışında kalan koşum yorum tazeler ama işlem uygulamaz (bkz. islem_uygula.py).
SEANS_BASI = time(13, 30)
SEANS_SONU = time(20, 0)


def env(ad, varsayilan=""):
    """Env okumaları hep .strip()'li: Actions secret'larında sonda newline olabiliyor."""
    return (os.environ.get(ad) or varsayilan).strip()


def simdi():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def seans_ici(dt=None):
    dt = dt or simdi()
    if dt.weekday() >= 5:
        return False
    return SEANS_BASI <= dt.time() <= SEANS_SONU


# --------------------------------------------------------------------------- veri


def _seri(df, alan, sembol):
    """yfinance tek/çok sembolde farklı kolon şeması döndürüyor; ikisini de karşıla."""
    try:
        alt = df[alan]
    except (KeyError, TypeError):
        return None
    if hasattr(alt, "columns"):
        if sembol not in alt.columns:
            return None
        alt = alt[sembol]
    return alt.dropna()


def _son_gecerli(seri):
    if seri is None or len(seri) == 0:
        return None
    deger = float(seri.iloc[-1])
    return deger if math.isfinite(deger) else None


def canli_veri_topla(semboller, bilanco_yedek=None):
    """Seans içi fiyat + önceki kapanış + 20g ortalama hacim + bilanço tarihi.

    Fiyat kaynağı seans içi 5 dakikalık bar (yfinance, ~15 dk gecikmeli). Seans içi
    çekim başarısız olursa günlük kapanışa düşülür ve bu `veri_kaynagi` alanında
    yazılır — sessizce günlük veriyle "canlı" demek, bayat yorumun ta kendisi olurdu.
    """
    import yfinance as yf

    liste = " ".join(semboller)
    gunluk = yf.download(liste, period="120d", interval="1d",
                         auto_adjust=False, progress=False)
    if gunluk is None or gunluk.empty:
        raise RuntimeError("Günlük veri alınamadı — hiçbir sembol için seri yok")

    try:
        anlik = yf.download(liste, period="1d", interval="5m",
                            auto_adjust=False, progress=False, prepost=False)
    except Exception as hata:  # ağ/şema hatası tezleri bloke etmesin
        print(f"UYARI: seans içi çekim başarısız ({hata}) — günlük kapanışa düşülüyor")
        anlik = None

    sonuc = {}
    for sym in semboller:
        kapanislar = _seri(gunluk, "Close", sym)
        if kapanislar is None or len(kapanislar) < 2:
            print(f"UYARI {sym}: günlük kapanış serisi yetersiz — atlanıyor")
            continue

        bugun = date.today()
        # Seans içindeyken günlük serinin son satırı bugünün yarım barıdır; önceki
        # kapanış o satır değil, ondan önceki gündür.
        if kapanislar.index[-1].date() == bugun and len(kapanislar) >= 2:
            onceki_kapanis = float(kapanislar.iloc[-2])
            gunluk_son = float(kapanislar.iloc[-1])
        else:
            onceki_kapanis = float(kapanislar.iloc[-1])
            gunluk_son = float(kapanislar.iloc[-1])

        fiyat = _son_gecerli(_seri(anlik, "Close", sym)) if anlik is not None else None
        kaynak = "seans_ici_5m"
        if fiyat is None:
            fiyat, kaynak = gunluk_son, "gunluk_kapanis"

        hacimler = _seri(gunluk, "Volume", sym)
        hacim_ort_20g = None
        if hacimler is not None and len(hacimler) >= 21:
            # Bugünün yarım hacmi ortalamayı aşağı çekmesin: son tam 20 gün.
            pencere = hacimler.iloc[-21:-1] if hacimler.index[-1].date() == bugun \
                else hacimler.iloc[-20:]
            ort = float(pencere.mean())
            hacim_ort_20g = ort if math.isfinite(ort) and ort > 0 else None

        hacim = None
        if anlik is not None:
            anlik_hacim = _seri(anlik, "Volume", sym)
            if anlik_hacim is not None and len(anlik_hacim):
                hacim = float(anlik_hacim.sum())
        if hacim is None and hacimler is not None and len(hacimler):
            hacim = float(hacimler.iloc[-1])

        sonuc[sym] = {
            "fiyat": round(fiyat, 4),
            "onceki_kapanis": round(onceki_kapanis, 4),
            "hacim": hacim,
            "hacim_ort_20g": hacim_ort_20g,
            "bilanco_tarihi": _bilanco_tarihi(yf, sym, bilanco_yedek),
            "veri_kaynagi": kaynak,
        }
    return sonuc


def _bilanco_tarihi(yf, sym, yedek):
    """yfinance calendar → portfoy.json yedeği → yok. Hiçbir durumda hata verme."""
    try:
        takvim = yf.Ticker(sym).calendar
        if takvim:
            tarihler = takvim.get("Earnings Date") or []
            if tarihler:
                ilk = tarihler[0]
                return ilk.isoformat() if hasattr(ilk, "isoformat") else str(ilk)
    except Exception:
        pass
    return (yedek or {}).get(sym)


# ------------------------------------------------------------------- koşul ölçümü


def olcum_yap(kosul, sym, veri, stop, bugun):
    """Koşulu ölç. Döner: (olcum, esik, ihlal_yonu, aciklama) ya da ölçülemezse None.

    ihlal_yonu "alti": ölçüm eşiğin altına inerse ihlal; "ustu": üstüne çıkarsa.
    """
    tip = kosul.get("tip")
    d = veri.get(sym, {})
    fiyat = d.get("fiyat")

    if tip == "fiyat_alti":
        if fiyat is None:
            return None
        return fiyat, float(kosul["deger"]), "alti", f"fiyat {fiyat:.2f}"

    if tip == "stop_yakinlik_pct":
        if fiyat is None or not stop:
            return None
        mesafe = (fiyat / float(stop) - 1) * 100
        return (round(mesafe, 2), float(kosul["deger"]), "alti",
                f"stop mesafesi %{mesafe:+.1f} (stop {stop})")

    if tip == "hacim_oran_20g":
        hacim, ort = d.get("hacim"), d.get("hacim_ort_20g")
        if not hacim or not ort:
            return None
        oran = hacim / ort
        return round(oran, 2), float(kosul["deger"]), "ustu", f"hacim {oran:.1f}x"

    if tip == "gunluk_degisim_pct":
        onceki = d.get("onceki_kapanis")
        if fiyat is None or not onceki:
            return None
        degisim = (fiyat / onceki - 1) * 100
        return (round(degisim, 2), float(kosul["deger"]), "alti",
                f"günlük değişim %{degisim:+.1f}")

    if tip == "sektor_etf_degisim_pct":
        etf = kosul.get("sembol", "SMH")
        e = veri.get(etf, {})
        if e.get("fiyat") is None or not e.get("onceki_kapanis"):
            return None
        degisim = (e["fiyat"] / e["onceki_kapanis"] - 1) * 100
        return (round(degisim, 2), float(kosul["deger"]), "alti",
                f"{etf} %{degisim:+.1f}")

    if tip == "bilanco_tarihi_yaklasti":
        ham = d.get("bilanco_tarihi")
        if not ham:
            return None  # bilanço tarihi yoksa atla, hata verme
        try:
            bilanco = date.fromisoformat(str(ham)[:10])
        except ValueError:
            return None
        kalan = (bilanco - bugun).days
        if kalan < 0:
            return None  # geçmiş bilanço koşulu tetiklemez
        return (kalan, float(kosul["gun"]), "alti",
                f"bilançoya {kalan} gün ({bilanco.isoformat()})")

    return None  # bilinmeyen tip sessizce atlanır; şema ileride büyüyebilir


def ihlal_mi(olcum, esik, yon):
    return olcum < esik if yon == "alti" else olcum > esik


def temizlendi_mi(olcum, esik, yon):
    """Geri dönüş bandı: ihlalden çıkmak için eşiği bandı kadar aşmak gerekir."""
    bant = abs(esik) * BANT_ORANI
    return olcum >= esik + bant if yon == "alti" else olcum <= esik - bant


# --------------------------------------------------------------------- durum G/Ç


def json_oku(yol, varsayilan):
    if not os.path.exists(yol):
        return varsayilan
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as hata:
        print(f"UYARI: {os.path.basename(yol)} okunamadı ({hata}) — sıfırdan başlanıyor")
        return varsayilan


def json_yaz(yol, veri):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def cooldownda_mi(cooldown, anahtar, an):
    damga = cooldown.get(anahtar)
    if not damga:
        return False
    try:
        son = datetime.fromisoformat(damga.replace("Z", "+00:00"))
    except ValueError:
        return False
    return an - son < timedelta(hours=COOLDOWN_SAAT)


# ------------------------------------------------------------------------- akış


def calistir(tezler, veri, stoplar, eski_durum, cooldown, an, tam_yenileme=False):
    """Saf fonksiyon: ağ ve dosya yok. Testler doğrudan buraya veri veriyor."""
    bugun = an.date()
    yeni_durum, tetiklenen, isaretler = {}, [], []
    semantik_degisim = False

    for sym, poz in tezler.items():
        if sym.startswith("_"):
            continue
        d = veri.get(sym, {})
        supheli = False
        if d.get("fiyat") and d.get("onceki_kapanis"):
            sapma = abs(d["fiyat"] / d["onceki_kapanis"] - 1) * 100
            supheli = sapma > SUPHELI_SAPMA_PCT
        gereken = GEREKEN_ARDISIK_SUPHELI if supheli else GEREKEN_ARDISIK

        for iddia in poz.get("iddialar", []):
            for i, kosul in enumerate(iddia.get("kosullar", [])):
                anahtar = f"{iddia['id']}#{i}"
                onceki = eski_durum.get(anahtar, {})
                sonuc = olcum_yap(kosul, sym, veri, stoplar.get(sym), bugun)
                if sonuc is None:
                    # Ölçülemeyen koşul önceki durumunu korur; "veri yok" ihlal değildir.
                    if onceki:
                        yeni_durum[anahtar] = dict(onceki, olculemedi=True)
                    continue
                olcum, esik, yon, aciklama = sonuc

                if onceki.get("ihlal"):
                    ihlal = not temizlendi_mi(olcum, esik, yon)
                else:
                    ihlal = ihlal_mi(olcum, esik, yon)

                ardisik = (onceki.get("ardisik", 0) + 1) if ihlal else 0
                onayli = ihlal and ardisik >= gereken
                kayit = {
                    "sembol": sym,
                    "iddia_id": iddia["id"],
                    "tip": kosul["tip"],
                    "siddet": kosul.get("siddet", "uyari"),
                    "ihlal": ihlal,
                    "ardisik": ardisik,
                    "onayli": onayli,
                    "gereken_ardisik": gereken,
                    "veri_supheli": supheli,
                    "olcum": olcum,
                    "esik": esik,
                    "aciklama": aciklama,
                    "ilk_gorulme": onceki.get("ilk_gorulme") if ihlal and onceki.get("ihlal")
                    else (iso(an) if ihlal else None),
                }
                yeni_durum[anahtar] = kayit

                for alan in ("ihlal", "ardisik", "onayli"):
                    if onceki.get(alan) != kayit[alan]:
                        semantik_degisim = True

                if not onayli:
                    continue
                siddet = kayit["siddet"]
                if siddet == "uyari":
                    isaretler.append(kayit)
                    continue
                kilit = f"tez:{sym}" if siddet == "tez" else iddia["id"]
                if cooldownda_mi(cooldown, kilit, an):
                    kayit["cooldown"] = True
                    continue
                tetiklenen.append({
                    "sembol": sym,
                    "iddia_id": iddia["id"],
                    "siddet": siddet,
                    "kosul_tipi": kosul["tip"],
                    "olcum": olcum,
                    "esik": esik,
                    "tetikleyici": aciklama,
                    "cooldown_anahtari": kilit,
                })

    kod = 0
    if tetiklenen:
        kod = max(SIDDET_KOD[t["siddet"]] for t in tetiklenen)
    elif tam_yenileme:
        kod = 10  # eşik aşılmasa da toplu gözden geçirme isteniyor

    return {
        "zaman": iso(an),
        "seans_ici": seans_ici(an),
        "tam_yenileme": tam_yenileme,
        "kod": kod,
        "kosullar": yeni_durum,
        "tetiklenen": tetiklenen,
        "isaretler": isaretler,
        "semantik_degisim": semantik_degisim or bool(tetiklenen),
    }


def main():
    ap = argparse.ArgumentParser(description="Tez geçerlilik koşullarını ölç")
    ap.add_argument("--dry-run", action="store_true",
                    help="durum dosyalarına yazma, sadece raporla")
    ap.add_argument("--sabit-veri", metavar="DOSYA",
                    help="ağ yerine bu JSON'dan veri oku (test)")
    ap.add_argument("--tam-yenileme", action="store_true",
                    help="eşik aşılmasa da tüm iddialar gözden geçirilsin (kod 10)")
    ap.add_argument("--durum-dizin", default=os.path.join(BASE, "durum"))
    args = ap.parse_args()

    tezler = json_oku(TEZLER_YOLU, {})
    if not [k for k in tezler if not k.startswith("_")]:
        print("tezler.json'da iddia yok — dedektör atlandı")
        return 0

    pf = json_oku(PF_YOLU, {"pozisyonlar": []})
    stoplar = {p["sembol"]: p.get("stop_haftalik_kapanis") for p in pf["pozisyonlar"]}
    bilanco_yedek = {p["sembol"]: p.get("sonraki_bilanco") for p in pf["pozisyonlar"]}

    an = simdi()
    if args.sabit_veri:
        sabit = json_oku(os.path.join(BASE, args.sabit_veri), {})
        veri = sabit.get("semboller", sabit)
        if sabit.get("zaman"):
            an = datetime.fromisoformat(sabit["zaman"].replace("Z", "+00:00"))
    else:
        etfler = {k.get("sembol", "SMH")
                  for poz in tezler.values() if isinstance(poz, dict)
                  for idd in poz.get("iddialar", [])
                  for k in idd.get("kosullar", [])
                  if k.get("tip") == "sektor_etf_degisim_pct"}
        semboller = sorted({k for k in tezler if not k.startswith("_")} | etfler)
        veri = canli_veri_topla(semboller, bilanco_yedek)

    ihlal_yolu = os.path.join(args.durum_dizin, "ihlaller.json")
    cooldown_yolu = os.path.join(args.durum_dizin, "cooldown.json")
    eski = json_oku(ihlal_yolu, {}).get("kosullar", {})
    cooldown = json_oku(cooldown_yolu, {})

    rapor = calistir(tezler, veri, stoplar, eski, cooldown, an, args.tam_yenileme)
    rapor["veri"] = {s: veri.get(s, {}) for s in sorted(veri)}

    if not args.dry_run:
        json_yaz(ihlal_yolu, rapor)

    # --- İnsan okunur özet ---
    print(f"Kontrol {rapor['zaman']} · seans içi: {rapor['seans_ici']} · kod {rapor['kod']}")
    for t in rapor["tetiklenen"]:
        print(f"  [{t['siddet'].upper()}] {t['sembol']} {t['iddia_id']}: "
              f"{t['tetikleyici']} (eşik {t['esik']})")
    for i in rapor["isaretler"]:
        print(f"  [işaret] {i['sembol']} {i['iddia_id']}: {i['aciklama']}")
    bekleyen = [k for k, v in rapor["kosullar"].items()
                if v.get("ihlal") and not v.get("onayli")]
    if bekleyen:
        print(f"  teyit bekliyor (histerezis): {', '.join(sorted(bekleyen))}")
    if not rapor["tetiklenen"] and not rapor["isaretler"]:
        print("  değişiklik yok")

    gh_out = env("GITHUB_OUTPUT")
    if gh_out:
        tez_semboller = sorted({t["sembol"] for t in rapor["tetiklenen"]
                                if t["siddet"] == "tez"})
        ozet = "; ".join(f"{t['sembol']} {t['iddia_id']}: {t['tetikleyici']}"
                         for t in rapor["tetiklenen"]) or "yok"
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"kod={rapor['kod']}\n")
            f.write(f"seans_ici={'true' if rapor['seans_ici'] else 'false'}\n")
            f.write(f"durum_degisti={'true' if rapor['semantik_degisim'] else 'false'}\n")
            f.write(f"tez_semboller={','.join(tez_semboller)}\n")
            f.write(f"tetiklenen_ozet={ozet}\n")

    return rapor["kod"]


if __name__ == "__main__":
    sys.exit(main())
