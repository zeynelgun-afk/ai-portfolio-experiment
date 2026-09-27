#!/usr/bin/env python3
"""Tez Nöbeti panelini üret: şablon + güncel tezler.json/portfoy.json → tek HTML.

Panel bir artifact olarak yayınlanıyor ve tez metinlerini yayın anındaki hâliyle
gömüyor. Şablonu depoda tutmanın sebebi bu: tezler her Cumartesi turunda değişiyor,
panel de yeniden üretilip yayınlanmalı. Elle düzenlenmiş tek seferlik bir HTML,
ikinci turda bayatlayacak bir yorum olurdu — panelin çözdüğü sorunun aynısı.

Canlı fiyat gömülmez: onu sayfa, izleyenin kendi FMP konnektöründen çeker.
Gömülen tek şey tez metinleri, eşikler, stop seviyeleri ve damga.

Kullanım:
    python panel/uret.py                 # panel/tez-nobeti.html üretir
    python panel/uret.py --cikti /yol.html
Sonra Claude oturumunda: Artifact aracıyla aynı URL'e yeniden yayınla.
"""

import argparse
import json
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SABLON = os.path.join(BASE, "panel", "tez-nobeti.sablon.html")
VARSAYILAN_CIKTI = os.path.join(BASE, "panel", "tez-nobeti.html")


def oku(ad):
    with open(os.path.join(BASE, ad), encoding="utf-8") as f:
        return json.load(f)


def son_tur_etiketi(varsayilan="KARAR_GUNLUGU.md (tur bulunamadı)"):
    """Günlükteki son haftalık tur başlığını etiket olarak döndür."""
    yol = os.path.join(BASE, "KARAR_GUNLUGU.md")
    if not os.path.exists(yol):
        return varsayilan
    son = None
    with open(yol, encoding="utf-8") as f:
        for satir in f:
            if satir.startswith("## #") and "HAFTALIK TUR" in satir:
                son = satir[3:].split("·")[0].strip()
    return f"KARAR_GUNLUGU.md {son}" if son else varsayilan


def main():
    ap = argparse.ArgumentParser(description="Tez Nöbeti panelini üret")
    ap.add_argument("--cikti", default=VARSAYILAN_CIKTI)
    args = ap.parse_args()

    tez = oku("tezler.json")
    pf = oku("portfoy.json")
    paket = {
        "damga": date.today().isoformat(),
        "kaynak_tur": son_tur_etiketi(),
        "nakit_usd": pf["nakit_usd"],
        "pozisyonlar": {p["sembol"]: {
            "adet": p["adet"],
            "giris_fiyati": p["giris_fiyati"],
            "stop": p.get("stop_haftalik_kapanis"),
            "bilanco": p.get("sonraki_bilanco"),
            "maliyet_usd": p.get("maliyet_usd"),
        } for p in pf["pozisyonlar"]},
        "tezler": {k: v for k, v in tez.items() if not k.startswith("_")},
    }

    with open(SABLON, encoding="utf-8") as f:
        sablon = f.read()
    if sablon.count("__VERI__") != 1:
        raise SystemExit("Şablonda tam olarak bir __VERI__ yer tutucusu olmalı")
    html = sablon.replace("__VERI__",
                          json.dumps(paket, ensure_ascii=False, separators=(",", ":")))
    with open(args.cikti, "w", encoding="utf-8") as f:
        f.write(html)

    iddia = sum(len(v["iddialar"]) for v in paket["tezler"].values())
    print(f"{args.cikti} yazıldı · {len(paket['tezler'])} pozisyon, {iddia} iddia, "
          f"kaynak: {paket['kaynak_tur']}")


if __name__ == "__main__":
    main()
