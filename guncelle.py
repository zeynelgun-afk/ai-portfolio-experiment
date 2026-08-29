#!/usr/bin/env python3
"""AI Portföy Deneyi — otomatik güncelleme.

Yaptıkları (yalnızca ölçüm ve raporlama; HİÇBİR karar vermez — tüzük sürüm 2'den
itibaren al/sat kararlarının tamamı AI'a aittir):
  1. Güncel kapanış fiyatlarını çeker (yfinance, anahtar gerekmez).
  2. Portföyü değerler, SPY/SMH kıyasını hesaplar.
  3. Çıkış seviyesinin altına düşen pozisyonları İŞARETLER — kapatmaz. Kapatma
     kararı haftalık turda AI'a aittir.
  4. RAPOR.md ve gecmis.csv üretir; GitHub Actions için uyarı çıktısı verir.
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
IHLAL_YOLU = os.path.join(BASE, "STOP_IHLALI.md")
TG_YOLU = os.path.join(BASE, "TELEGRAM.txt")


def kapanislari_cek(semboller):
    veri = yf.download(" ".join(semboller), period="10d", interval="1d",
                       auto_adjust=False, progress=False)["Close"]
    # yfinance sonda tümüyle boş bir gün döndürebiliyor. ffill fiyatı kurtarıyordu ama
    # tarih etiketi o boş günü gösteriyordu — rapor "28 Ağu kapanışı" derken fiyat aslında
    # 27 Ağu'ya aitti. Tarih, gerçekten veri olan son günden alınmalı.
    dolu = veri.dropna(how="all")
    if dolu.empty:
        raise RuntimeError("Kapanış verisi alınamadı: tüm günler boş")
    tarih = dolu.index[-1].date()
    if hasattr(veri, "columns"):
        son = veri.ffill().iloc[-1]
        return {s: float(son[s]) for s in semboller}, tarih
    # tek sembol durumu
    return {semboller[0]: float(veri.ffill().iloc[-1])}, tarih


def main():
    with open(PF_YOLU, encoding="utf-8") as f:
        pf = json.load(f)

    semboller = [p["sembol"] for p in pf["pozisyonlar"]] + ["SPY", "SMH"]
    fiyatlar, veri_tarihi = kapanislari_cek(semboller)
    bugun = date.today().isoformat()

    # --- Çıkış seviyesi kontrolü: yalnızca UYARI, infaz yok ---
    # Tüzük sürüm 2: kapatma kararı AI'ındır. Burada pozisyona dokunulmaz.
    ihlaller = []
    for p in pf["pozisyonlar"]:
        kapanis = fiyatlar[p["sembol"]]
        if kapanis < p["stop_haftalik_kapanis"]:
            getiri = (kapanis / p["giris_fiyati"] - 1) * 100
            ihlaller.append(
                f"- **{p['sembol']}**: kapanış {kapanis:.2f} $ < çıkış seviyesi "
                f"{p['stop_haftalik_kapanis']} $ (getiri %{getiri:+.1f}) "
                f"→ KARAR AI'A AİT: kapat, seviyeyi güncelle ya da gerekçeyle taşı"
            )

    if ihlaller:
        with open(IHLAL_YOLU, "w", encoding="utf-8") as f:
            f.write(f"# Çıkış seviyesi uyarısı — {bugun}\n\n"
                    f"Veri tarihi: {veri_tarihi}\n\n"
                    + "\n".join(ihlaller)
                    + "\n\nOtomatik kapatma YAPILMADI. Bu turda AI'ın kararı ve "
                      "gerekçesi KARAR_GUNLUGU.md'ye yazılır.\n")
    elif os.path.exists(IHLAL_YOLU):
        # Uyarı geçmişse bayrağı temizle; yoksa dosya kalıcı olarak asılı kalıyordu.
        os.remove(IHLAL_YOLU)

    # --- Değerleme ---
    poz_deger = sum(p["adet"] * fiyatlar[p["sembol"]] for p in pf["pozisyonlar"])
    toplam = pf["nakit_usd"] + poz_deger
    baslangic = pf["baslangic_sermayesi_usd"]
    spy_val = baslangic * fiyatlar["SPY"] / pf["benchmark"]["SPY_referans"]
    smh_val = baslangic * fiyatlar["SMH"] / pf["benchmark"]["SMH_referans"]

    # --- Geçmiş (equity curve; aynı günün kaydı varsa üzerine yazılır) ---
    eski_satirlar = []
    if os.path.exists(GECMIS_YOLU):
        with open(GECMIS_YOLU, newline="", encoding="utf-8") as f:
            eski_satirlar = [r for r in csv.reader(f)
                             if r and r[0] not in ("tarih", bugun)]
    with open(GECMIS_YOLU, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tarih", "portfoy_usd", "spy_usd", "smh_usd"])
        w.writerows(eski_satirlar)
        w.writerow([bugun, f"{toplam:.2f}", f"{spy_val:.2f}", f"{smh_val:.2f}"])

    # --- Rapor ---
    if ihlaller:
        stop_notu = (chr(10).join(ihlaller)
                     + "\n\n*Otomatik kapatma yapılmadı — karar AI'a aittir.*")
    else:
        stop_notu = "Uyarı yok — tüm pozisyonlar çıkış seviyelerinin üzerinde."
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

{stop_notu}

*Otomatik rapor (guncelle.py). Kararlar ve tezler: KARAR_GUNLUGU.md*
"""
    with open(RAPOR_YOLU, "w", encoding="utf-8") as f:
        f.write(rapor)

    pf["son_guncelleme"] = bugun
    with open(PF_YOLU, "w", encoding="utf-8") as f:
        json.dump(pf, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # --- Telegram özeti (workflow bu dosyayı gönderir) ---
    poz_ozet = "\n".join(
        f"• {p['sembol']}: {p['adet'] * fiyatlar[p['sembol']]:,.0f} $ "
        f"(fiyat {fiyatlar[p['sembol']]:.2f} $, %{(fiyatlar[p['sembol']] / p['giris_fiyati'] - 1) * 100:+.1f})"
        for p in pf["pozisyonlar"]
    )
    if ihlaller:
        stop_tg = "⚠️ Çıkış seviyesi altında (karar AI'da):\n" + "\n".join(
            i.replace("**", "") for i in ihlaller)
    else:
        stop_tg = "✅ Çıkış seviyesi uyarısı yok."
    with open(TG_YOLU, "w", encoding="utf-8") as f:
        f.write(
            f"📊 AI Portföy Deneyi — {bugun}\n\n"
            f"Toplam: {toplam:,.0f} $ (%{(toplam / baslangic - 1) * 100:+.2f})\n"
            f"SPY: %{(spy_val / baslangic - 1) * 100:+.2f} · "
            f"SMH: %{(smh_val / baslangic - 1) * 100:+.2f}\n"
            f"Fark vs SPY: %{(toplam - spy_val) / baslangic * 100:+.2f}\n\n"
            f"Pozisyonlar:\n{poz_ozet}\n"
            f"Nakit: {pf['nakit_usd']:,.0f} $\n\n"
            f"{stop_tg}\n\n"
            f"Detay: https://github.com/zeynelgun-afk/ai-portfoy-deneyi"
        )

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
