#!/usr/bin/env python3
"""AI Portföy Deneyi — otomatik güncelleme.

Yaptıkları (tamamı DENEY_KURALLARI.md'deki mekanik kurallar; takdir gerektiren
karar İÇERMEZ — al/sat tezleri oturumda AI tarafından verilir):
  1. Güncel kapanış fiyatlarını çeker (yfinance, anahtar gerekmez).
  2. Portföyü değerler, SPY/SMH kıyasını hesaplar.
  3. Stop kuralını uygular: son haftalık kapanış stop altındaysa pozisyonu
     kapatır (kural #3 — mekanik), işlemi ve günlük kaydını yazar.
  4. RAPOR.md ve gecmis.csv üretir; GitHub Actions için ihlal çıktısı verir.
"""

import csv
import json
import os
from datetime import date

import yfinance as yf

BASE = os.path.dirname(os.path.abspath(__file__))
PF_YOLU = os.path.join(BASE, "portfoy.json")
RAPOR_YOLU = os.path.join(BASE, "RAPOR.md")
GECMIS_YOLU = os.path.join(BASE, "gecmis.csv")
GUNLUK_YOLU = os.path.join(BASE, "KARAR_GUNLUGU.md")
IHLAL_YOLU = os.path.join(BASE, "STOP_IHLALI.md")


def kapanislari_cek(semboller):
    veri = yf.download(" ".join(semboller), period="10d", interval="1d",
                       auto_adjust=False, progress=False)["Close"]
    if hasattr(veri, "columns"):
        son = veri.ffill().iloc[-1]
        tarih = veri.index[-1].date()
        return {s: float(son[s]) for s in semboller}, tarih
    # tek sembol durumu
    return {semboller[0]: float(veri.ffill().iloc[-1])}, veri.index[-1].date()


def main():
    with open(PF_YOLU, encoding="utf-8") as f:
        pf = json.load(f)

    semboller = [p["sembol"] for p in pf["pozisyonlar"]] + ["SPY", "SMH"]
    fiyatlar, veri_tarihi = kapanislari_cek(semboller)
    bugun = date.today().isoformat()

    # --- Kural #3: mekanik stop kontrolü (haftalık kapanış bazlı) ---
    ihlaller = []
    kalanlar = []
    for p in pf["pozisyonlar"]:
        kapanis = fiyatlar[p["sembol"]]
        if kapanis < p["stop_haftalik_kapanis"]:
            tutar = round(p["adet"] * kapanis, 2)
            pf["nakit_usd"] = round(pf["nakit_usd"] + tutar, 2)
            pf["islem_gecmisi"].append({
                "tarih": bugun, "islem": "SAT (STOP)", "sembol": p["sembol"],
                "adet": p["adet"], "fiyat": kapanis, "tutar_usd": tutar,
            })
            getiri = (kapanis / p["giris_fiyati"] - 1) * 100
            ihlaller.append(
                f"- **{p['sembol']}**: kapanış {kapanis:.2f} $ < stop "
                f"{p['stop_haftalik_kapanis']} $ → pozisyon kapatıldı "
                f"({tutar:,.0f} $ nakde geçti, getiri %{getiri:+.1f})"
            )
        else:
            kalanlar.append(p)
    pf["pozisyonlar"] = kalanlar

    if ihlaller:
        with open(GUNLUK_YOLU, "a", encoding="utf-8") as f:
            f.write(f"\n---\n\n## OTOMATİK — {bugun} · STOP UYGULAMASI (kural #3)\n\n"
                    + "\n".join(ihlaller)
                    + "\n\nMekanik uygulama; yeniden giriş kararı bir sonraki "
                      "oturumda tezle birlikte değerlendirilir.\n")
        with open(IHLAL_YOLU, "w", encoding="utf-8") as f:
            f.write(f"# Stop ihlali — {bugun}\n\nVeri tarihi: {veri_tarihi}\n\n"
                    + "\n".join(ihlaller) + "\n")

    # --- Değerleme ---
    poz_deger = sum(p["adet"] * fiyatlar[p["sembol"]] for p in pf["pozisyonlar"])
    toplam = pf["nakit_usd"] + poz_deger
    baslangic = pf["baslangic_sermayesi_usd"]
    spy_val = baslangic * fiyatlar["SPY"] / pf["benchmark"]["SPY_referans"]
    smh_val = baslangic * fiyatlar["SMH"] / pf["benchmark"]["SMH_referans"]

    # --- Geçmiş (equity curve) ---
    yeni_dosya = not os.path.exists(GECMIS_YOLU)
    with open(GECMIS_YOLU, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if yeni_dosya:
            w.writerow(["tarih", "portfoy_usd", "spy_usd", "smh_usd"])
        w.writerow([bugun, f"{toplam:.2f}", f"{spy_val:.2f}", f"{smh_val:.2f}"])

    # --- Rapor ---
    satirlar = []
    for p in pf["pozisyonlar"]:
        fiyat = fiyatlar[p["sembol"]]
        deger = p["adet"] * fiyat
        getiri = (fiyat / p["giris_fiyati"] - 1) * 100
        stop_mesafe = (fiyat / p["stop_haftalik_kapanis"] - 1) * 100
        satirlar.append(
            f"| {p['sembol']} | {p['giris_fiyati']:.2f} | {fiyat:.2f} | "
            f"%{getiri:+.1f} | {deger:,.0f} | %{deger / toplam * 100:.1f} | "
            f"{p['stop_haftalik_kapanis']} (%{stop_mesafe:+.1f}) |"
        )

    rapor = f"""# Portföy Raporu — {bugun}

Veri: {veri_tarihi} kapanışları · Başlangıç: {baslangic:,.0f} $ (2026-08-05)

## Durum

| Hisse | Giriş | Son | Getiri | Değer $ | Ağırlık | Stop (mesafe) |
|---|---|---|---|---|---|---|
{chr(10).join(satirlar)}

**Nakit:** {pf['nakit_usd']:,.2f} $

## Skor

| | Değer | Getiri |
|---|---|---|
| **AI Portföyü** | {toplam:,.0f} $ | **%{(toplam / baslangic - 1) * 100:+.2f}** |
| SPY (aynı gün 100k) | {spy_val:,.0f} $ | %{(spy_val / baslangic - 1) * 100:+.2f} |
| SMH (aynı gün 100k) | {smh_val:,.0f} $ | %{(smh_val / baslangic - 1) * 100:+.2f} |

Fark vs SPY: **%{(toplam - spy_val) / baslangic * 100:+.2f}** · vs SMH: **%{(toplam - smh_val) / baslangic * 100:+.2f}**

## Stop kontrolü

{chr(10).join(ihlaller) if ihlaller else "İhlal yok — tüm pozisyonlar stop seviyelerinin üzerinde."}

*Otomatik rapor (guncelle.py). Kararlar ve tezler: KARAR_GUNLUGU.md*
"""
    with open(RAPOR_YOLU, "w", encoding="utf-8") as f:
        f.write(rapor)

    pf["son_guncelleme"] = bugun
    with open(PF_YOLU, "w", encoding="utf-8") as f:
        json.dump(pf, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # --- GitHub Actions çıktısı ---
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"stop_ihlali={'true' if ihlaller else 'false'}\n")
            f.write("ihlal_listesi="
                    + ", ".join(i.split("**")[1] for i in ihlaller) + "\n")

    print(f"Toplam: {toplam:,.2f} $ ({(toplam / baslangic - 1) * 100:+.2f}%) | "
          f"SPY: {(spy_val / baslangic - 1) * 100:+.2f}% | "
          f"SMH: {(smh_val / baslangic - 1) * 100:+.2f}% | "
          f"İhlal: {len(ihlaller)}")


if __name__ == "__main__":
    main()
