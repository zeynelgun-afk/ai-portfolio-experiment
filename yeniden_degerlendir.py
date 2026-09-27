#!/usr/bin/env python3
"""Olay güdümlü yeniden değerlendirme — yorumu yeniden yazan katman.

`dedektor.py` yalnızca "anlam değişti mi?" sorusunu deterministik yanıtlar. Bu script
değişen anlamı yazıya döker:

  kod 10 (iddia)  → yalnızca etkilenen iddia, küçük modelle yeniden yazılır.
                    Girdi: eski iddia + tetikleyen veri + zaman. Çıktı:
                    {metin, durum: gecerli|zayifladi|gecersiz}
  kod 20 (tez)    → pozisyonun TÜM tezi derin modelle yeniden değerlendirilir ve
                    uygulanabilir bir karar üretilir (durum/bekleyen_karar.json).
                    Kararı bu script UYGULAMAZ — uygulama islem_uygula.py'de,
                    deterministik doğrulamalardan sonra.

Bütçe: `MAX_LLM_CAGRI_HAFTA` (varsayılan 60) haftalık çağrı sınırı. Aşılırsa yalnızca
kod 20 çağrıları yapılır — tez seviyesi bir tezin tümüyle çökmesi demektir, bütçeye
kurban edilmez.

Modelin ürettiği JSON parse edilemezse iddia DEĞİŞTİRİLMEZ, yalnızca
`durum: "degerlendirilemedi"` işaretlenir. Yarım anlaşılmış bir çıktıyla tezi
yeniden yazmak, bayat yorumdan daha kötüdür.

Kullanım:
    python yeniden_degerlendir.py --kod 10
    python yeniden_degerlendir.py --kod 20
    python yeniden_degerlendir.py --tam-yenileme      # tüm iddialar, küçük model
    python yeniden_degerlendir.py --kod 10 --dry-run  # LLM çağrısı yok, prompt basılır
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import sayi_denetimi

BASE = os.path.dirname(os.path.abspath(__file__))
TEZLER_YOLU = os.path.join(BASE, "tezler.json")
PF_YOLU = os.path.join(BASE, "portfoy.json")

# Madde 5 (inceleme): adres sabit değil. OpenRouter kesintisinde LLM_BASE_URL'i
# başka bir OpenAI-uyumlu uca çevirmek kod değişikliği gerektirmesin.
VARSAYILAN_BASE_URL = "https://openrouter.ai/api/v1"
API_YOLU = "/chat/completions"
VARSAYILAN_HIZLI = "anthropic/claude-haiku-4.5"
VARSAYILAN_DERIN = "anthropic/claude-sonnet-4.5"
VARSAYILAN_BUTCE = 60
ZAMAN_ASIMI = 120
# Madde 1 (inceleme): geçici hata ve bozuk çıktı tek denemede pes etmeyi hak etmiyor.
DENEME_SAYISI = 3
GERI_CEKILME_TABAN = 2.0  # saniye; her denemede ikiye katlanır
BEKLE = time.sleep  # testler gerçek beklemeyi devre dışı bırakmak için değiştirir

GECERLI_DURUMLAR = {"gecerli", "zayifladi", "gecersiz"}
GECERLI_ISLEMLER = {"TUT", "AL", "SAT", "KIRP"}


def env(ad, varsayilan=""):
    """Env okumaları hep .strip()'li — Actions secret'larında sonda newline olabiliyor."""
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


# ------------------------------------------------------------------------ bütçe


def hafta_etiketi(an):
    yil, hafta, _ = an.isocalendar()
    return f"{yil}-W{hafta:02d}"


def butce_durumu(sayac_yolu, an):
    sayac = json_oku(sayac_yolu, {})
    if sayac.get("hafta") != hafta_etiketi(an):
        sayac = {"hafta": hafta_etiketi(an), "cagri": 0}
    sinir = VARSAYILAN_BUTCE
    ham = env("MAX_LLM_CAGRI_HAFTA")
    if ham:
        try:
            sinir = int(ham)
        except ValueError:
            print(f"UYARI: MAX_LLM_CAGRI_HAFTA sayı değil ({ham!r}) — {sinir} kullanılıyor")
    return sayac, sinir


# --------------------------------------------------------------------------- LLM


def api_url():
    taban = env("LLM_BASE_URL", VARSAYILAN_BASE_URL).rstrip("/")
    return taban + API_YOLU


def _tek_cagri(model, mesajlar, anahtar):
    """Tek HTTP çağrısı. (metin, yeniden_denenebilir) döndürür."""
    govde = json.dumps({
        "model": model,
        "messages": mesajlar,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    istek = urllib.request.Request(api_url(), data=govde, headers={
        "Authorization": f"Bearer {anahtar}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/zeynelgun-afk/ai-portfoy-deneyi",
        "X-Title": "AI Portfoy Deneyi - dedektor",
    })
    try:
        with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI) as yanit:
            veri = json.loads(yanit.read().decode("utf-8"))
        return veri["choices"][0]["message"]["content"], False
    except urllib.error.HTTPError as hata:
        # 4xx caller hatası — tekrar denemek aynı sonucu verir. 429 ve 5xx geçici.
        gecici = hata.code == 429 or hata.code >= 500
        print(f"HATA: LLM HTTP {hata.code} ({model})"
              + (" — yeniden denenecek" if gecici else " — kalıcı hata"))
        return None, gecici
    except (urllib.error.URLError, TimeoutError) as hata:
        print(f"HATA: LLM ağ hatası ({model}): {hata} — yeniden denenecek")
        return None, True
    except (KeyError, IndexError, ValueError) as hata:
        print(f"HATA: LLM yanıtı okunamadı ({model}): {hata} — yeniden denenecek")
        return None, True


def llm_cagir(model, sistem, kullanici, anahtar, denetim_kaynaklari=None,
              denetim_hazirla=None, bekle=None):
    """JSON döndüren LLM çağrısı — geçici hatada ve bozuk çıktıda yeniden dener.

    Üç sorun aynı döngüde ele alınıyor, çünkü üçünün de çaresi aynı: bir kez daha sor.
      1. Ağ / 429 / 5xx → katlanarak artan beklemeyle tekrar
      2. JSON ayıklanamadı → modele ne beklendiği hatırlatılarak tekrar
      3. Kaynaksız rakam → `sayi_denetimi` işaretledi; hangi rakam olduğu söylenerek
         tekrar. Prompt bir güvenlik duvarı değildir, bu kapı onu koda çevirir.

    `denetim_kaynaklari`: rakamların karşılaştırılacağı metinler (prompt + eski iddia).
    Boş verilirse rakam denetimi yapılmaz.
    `denetim_hazirla(cikti)`: çıktının HANGİ kısmının denetlendiğini belirler; döner
    `(denetlenecek_metin, ek_kaynaklar)`. Ayrım önemli: piyasa hakkındaki cümleler
    kaynak ister, ama modelin ürettiği KARAR parametreleri (satılacak adet, yeni stop
    seviyesi) piyasa iddiası değil — onların denetimi `islem_uygula.py`'nin
    aritmetiğidir. İkisi karıştırılırsa model hiçbir karar veremez.

    Döner: (sozluk, durum) · durum "tamam" | "parse_edilemedi" | "kaynaksiz_rakam".
    Sözlük None ise iddia DEĞİŞTİRİLMEMELİ.
    """
    bekle = bekle or BEKLE
    mesajlar = [{"role": "system", "content": sistem},
                {"role": "user", "content": kullanici}]
    son_durum = "parse_edilemedi"

    for deneme in range(1, DENEME_SAYISI + 1):
        metin, gecici = _tek_cagri(model, mesajlar, anahtar)
        if metin is None:
            if not gecici or deneme == DENEME_SAYISI:
                return None, "parse_edilemedi"
            gecikme = GERI_CEKILME_TABAN * (2 ** (deneme - 1))
            print(f"  {gecikme:.0f} sn beklenip yeniden denenecek "
                  f"({deneme}/{DENEME_SAYISI})")
            bekle(gecikme)
            continue

        cikti = json_ayikla(metin)
        if cikti is None:
            son_durum = "parse_edilemedi"
            if deneme == DENEME_SAYISI:
                break
            print(f"  JSON ayıklanamadı — hatırlatmayla yeniden sorulacak "
                  f"({deneme}/{DENEME_SAYISI})")
            mesajlar += [
                {"role": "assistant", "content": metin[:2000]},
                {"role": "user", "content":
                 "Yanıtın geçerli JSON değildi. Sadece istenen şemadaki JSON nesnesini "
                 "döndür: açıklama yok, markdown yok, kod bloğu yok."},
            ]
            continue

        if denetim_kaynaklari:
            if denetim_hazirla:
                denetlenecek, ek_kaynak = denetim_hazirla(cikti)
            else:
                denetlenecek, ek_kaynak = json.dumps(cikti, ensure_ascii=False), ()
            kaynaksiz = sayi_denetimi.kaynaksiz_rakamlar(
                denetlenecek, *denetim_kaynaklari, *ek_kaynak)
            if kaynaksiz:
                etiket = ", ".join(h for h, _ in kaynaksiz)
                son_durum = "kaynaksiz_rakam"
                if deneme == DENEME_SAYISI:
                    print(f"  KAYNAKSIZ RAKAM (son deneme): {etiket} — çıktı reddedildi")
                    break
                print(f"  KAYNAKSIZ RAKAM: {etiket} — düzeltme istenecek "
                      f"({deneme}/{DENEME_SAYISI})")
                mesajlar += [
                    {"role": "assistant", "content": metin[:2000]},
                    {"role": "user",
                     "content": sayi_denetimi.geri_besleme_metni(kaynaksiz)},
                ]
                continue

        return cikti, "tamam"

    return None, son_durum


def json_ayikla(metin):
    """Model ```json bloğu veya düz metin sarmalayabiliyor; ilk JSON nesnesini çek."""
    if not metin:
        return None
    ham = metin.strip()
    if ham.startswith("```"):
        ham = ham.split("```")[1]
        ham = ham[4:] if ham.lower().startswith("json") else ham
    bas, son = ham.find("{"), ham.rfind("}")
    if bas < 0 or son <= bas:
        return None
    try:
        return json.loads(ham[bas:son + 1])
    except json.JSONDecodeError:
        return None


# ------------------------------------------------------------------------ prompt

SISTEM_ORTAK = """Sen "AI Portföy Deneyi"nin seans içi yeniden değerlendirme katmanısın.
Deneyin tüzüğü (DENEY_KURALLARI.md) sana karar kısıtı koymaz; kayıt dürüstlüğü kuralları koyar:

- RAKAM UYDURMA. Yalnızca sana verilen veri bloğundaki sayıları kullan. Hafızandan fiyat,
  pazar payı, ürün adı, analist hedefi, F/K yazma. Veri bloğunda olmayan bir sayıyı
  cümlene koyma; gerekiyorsa tezi rakamsız kur.
- Yüzde yazarken tabanını belirt (girişe göre / önceki kapanışa göre).
- Temenni tez değildir. "Toparlayabilir", "bilanço güzel gelebilir", "bekleyip göreceğim"
  yasak. Tez, şimdiki zamanda, bir dayanağa bağlı tek cümledir.
- Fikir değiştirmek serbest, sessizce değiştirmek değil: eski iddiadan sapıyorsan
  saptığını yaz.
- Yanıtın YALNIZCA geçerli JSON olsun. Açıklama, markdown, kod bloğu ekleme."""

SISTEM_IDDIA = SISTEM_ORTAK + """

Görev: SANA VERİLEN TEK İDDİAYI yeniden yaz. Pozisyonun tümünü değerlendirmiyorsun,
işlem önermiyorsun. Yalnızca bu iddianın metni hâlâ doğru mu, tetikleyen veriye göre
nasıl yazılmalı.

Şema:
{"metin": "<tek paragraf, tetikleyen veriyi içeren güncel iddia>",
 "durum": "gecerli" | "zayifladi" | "gecersiz"}

durum anlamı: gecerli = iddia ayakta, veri onu bozmadı. zayifladi = iddia hâlâ
savunulabilir ama dayanağı inceldi. gecersiz = iddia artık doğru değil."""

SISTEM_TEZ = SISTEM_ORTAK + """

Görev: Bu pozisyonun TÜM tezini yeniden değerlendir ve uygulanabilir bir karar üret.
Karar senin; TUT da geçerli bir karardır. Kararı sen uygulamıyorsun — deterministik bir
script uygulayacak, o yüzden adet/tutar alanları eksiksiz ve veri bloğundaki nakit ve
adet sınırları içinde olmalı.

Şema:
{"tez_degerlendirmesi": "<pozisyonun tezi ne durumda, tetikleyen veri ne değiştirdi>",
 "yeni_tez_ozeti": "<tek cümle, güncel tez>",
 "iddia_durumlari": {"<iddia_id>": "gecerli" | "zayifladi" | "gecersiz"},
 "karar": {
   "islem": "TUT" | "AL" | "SAT" | "KIRP",
   "adet": <SAT/KIRP için satılacak adet; TUT/AL için null>,
   "tutar_usd": <AL için harcanacak nakit; diğerlerinde null>,
   "yeni_stop": <stop seviyesi değişiyorsa sayı, değişmiyorsa null>,
   "gerekce": "<neden bu karar — tetikleyen veriye bağlı>",
   "carpitma_isareti": "<neyi görürsem bu kararda yanıldığımı anlarım>"
 },
 "cumartesi_notu": "<haftalık tura taşınacak not; yoksa boş dize>"}

KIRP = pozisyonun bir kısmını sat (adet ver). SAT = tamamını sat (adet = elindeki tüm adet).
AL = mevcut pozisyona ekleme (tutar_usd, nakitten küçük ya da eşit)."""


def iddia_denetimi(cikti):
    """kod 10: yalnızca iddia metni denetlenir; `durum` alanı rakam içermez."""
    return str(cikti.get("metin", "")), ()


def tez_denetimi(cikti):
    """kod 20: prose denetlenir, karar parametreleri denetlenmez ama KAYNAK olur.

    Karar parametreleri (adet, tutar_usd, yeni_stop) modelin kararıdır, piyasa
    hakkında bir iddia değil. Gerekçe cümlesinde geçebilmeleri gerekir ("stop'u
    820'ye taşıyorum"), o yüzden izinli kümeye eklenirler; doğru oldukları
    islem_uygula.py'de aritmetikle sınanır.
    """
    karar = cikti.get("karar") or {}
    prose = " ".join(str(cikti.get(a, "")) for a in
                     ("tez_degerlendirmesi", "yeni_tez_ozeti", "cumartesi_notu"))
    prose += " " + " ".join(str(karar.get(a, "")) for a in
                            ("gerekce", "carpitma_isareti"))
    parametreler = " ".join(str(karar.get(a, "")) for a in
                            ("adet", "tutar_usd", "yeni_stop"))
    return prose, (parametreler,)


def iddia_promptu(sym, poz, iddia, tetik, veri, pf_poz, an):
    d = veri.get(sym, {})
    satirlar = [
        f"Zaman (UTC): {iso(an)}",
        f"Sembol: {sym}",
        f"Pozisyonun tez özeti: {poz.get('tez_ozeti', '-')}",
        "",
        f"YENİDEN YAZILACAK İDDİA ({iddia['id']}):",
        f"  metin: {iddia.get('metin', '-')}",
        f"  mevcut durum: {iddia.get('durum', '-')}",
        f"  son güncelleme: {iddia.get('son_guncelleme', '-')}",
        "",
        "TETİKLEYEN VERİ (eşik aşıldı, 2 ardışık kontrolde teyit edildi):",
        f"  koşul tipi: {tetik.get('kosul_tipi')}",
        f"  ölçüm: {tetik.get('olcum')} · eşik: {tetik.get('esik')}",
        f"  özet: {tetik.get('tetikleyici')}",
        "",
        "GÜNCEL VERİ:",
        f"  fiyat: {d.get('fiyat')} $ (kaynak: {d.get('veri_kaynagi')})",
        f"  önceki kapanış: {d.get('onceki_kapanis')} $",
        f"  bilanço tarihi: {d.get('bilanco_tarihi') or 'yok'}",
    ]
    if d.get("hacim") and d.get("hacim_ort_20g"):
        satirlar.append(f"  hacim / 20g ortalama: {d['hacim'] / d['hacim_ort_20g']:.2f}x")
    if pf_poz:
        satirlar += [
            f"  giriş fiyatı: {pf_poz.get('giris_fiyati')} $",
            f"  adet: {pf_poz.get('adet')}",
            f"  stop_haftalik_kapanis: {pf_poz.get('stop_haftalik_kapanis')} $",
        ]
    return "\n".join(satirlar)


def tez_promptu(sym, poz, tetikler, veri, pf_poz, nakit, an):
    d = veri.get(sym, {})
    satirlar = [
        f"Zaman (UTC): {iso(an)}",
        f"Sembol: {sym}",
        f"Mevcut tez özeti: {poz.get('tez_ozeti', '-')}",
        "",
        "MEVCUT İDDİALAR:",
    ]
    for idd in poz.get("iddialar", []):
        satirlar.append(f"  [{idd['id']}] ({idd.get('durum')}) {idd.get('metin')}")
    satirlar += ["", "TEZ SEVİYESİ TETİKLEYİCİLER (teyit edilmiş):"]
    for t in tetikler:
        satirlar.append(f"  {t.get('iddia_id')} · {t.get('kosul_tipi')}: "
                        f"{t.get('tetikleyici')} (eşik {t.get('esik')})")
    satirlar += [
        "",
        "GÜNCEL VERİ:",
        f"  fiyat: {d.get('fiyat')} $ (kaynak: {d.get('veri_kaynagi')})",
        f"  önceki kapanış: {d.get('onceki_kapanis')} $",
        f"  bilanço tarihi: {d.get('bilanco_tarihi') or 'yok'}",
    ]
    if d.get("hacim") and d.get("hacim_ort_20g"):
        satirlar.append(f"  hacim / 20g ortalama: {d['hacim'] / d['hacim_ort_20g']:.2f}x")
    for etf in ("SMH", "SPY"):
        e = veri.get(etf)
        if e and e.get("fiyat") and e.get("onceki_kapanis"):
            satirlar.append(f"  {etf} günlük: %{(e['fiyat'] / e['onceki_kapanis'] - 1) * 100:+.2f}")
    if pf_poz:
        satirlar += [
            "",
            "POZİSYON (portfoy.json):",
            f"  adet: {pf_poz.get('adet')} · giriş: {pf_poz.get('giris_fiyati')} $",
            f"  maliyet: {pf_poz.get('maliyet_usd')} $",
            f"  stop_haftalik_kapanis: {pf_poz.get('stop_haftalik_kapanis')} $",
            f"  sonraki bilanço: {pf_poz.get('sonraki_bilanco')}",
        ]
    satirlar += ["", f"NAKİT: {nakit} $ (AL kararında tutar_usd bunu aşamaz)"]
    return "\n".join(satirlar)


def tetik_birlestir(liste):
    """Bir iddia aynı turda birkaç koşuldan tetiklenebilir (fiyat + hacim + sektör).

    Tetikleyicileri sözlükte iddia_id ile saklamak, en bilgilendirici olanı (fiyat 50g
    altında) en zayıfının (sektör ETF'i %-4.9) üzerine yazıyordu. Hepsi prompt'a gider.
    """
    return {
        "kosul_tipi": ", ".join(t.get("kosul_tipi", "?") for t in liste),
        "olcum": "; ".join(f"{t.get('kosul_tipi')}={t.get('olcum')}" for t in liste),
        "esik": "; ".join(f"{t.get('kosul_tipi')}={t.get('esik')}" for t in liste),
        "tetikleyici": "; ".join(t.get("tetikleyici", "") for t in liste),
    }


# --------------------------------------------------------------------- yazma


def iddia_isaretle(iddia, durum, tetik_metni, an, yeni_metin=None):
    if yeni_metin:
        iddia["metin"] = yeni_metin
    iddia["durum"] = durum
    iddia["son_guncelleme"] = iso(an)
    iddia["tetikleyici"] = f"{iso(an)}, tetikleyici: {tetik_metni}" if tetik_metni else None


def not_ekle(yol, baslik, govde):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    yeni = not os.path.exists(yol)
    with open(yol, "a", encoding="utf-8") as f:
        if yeni:
            f.write("# Cumartesi turu için bekleyen notlar\n\n"
                    "Seans içi yeniden değerlendirme bu dosyaya yazar. Haftalık tur bu "
                    "notları okur, karara bağlar ve karara bağladığı notu dosyadan siler "
                    "(HAFTALIK_TALIMAT.md madde 9).\n")
        f.write(f"\n## {baslik}\n\n{govde}\n")


# ---------------------------------------------------------------------- akışlar


def kod10_akisi(tezler, ihlaller, pf, an, model, anahtar, sayac, sinir, dry, tam,
                atla=None):
    """Etkilenen iddiaları (ya da tam yenilemede hepsini) küçük modelle tazele.

    `atla`: tez seviyesinde ele alınmış iddia id'leri. Onlar derin modelin tam
    bağlamıyla değerlendirildi; aynı iddiayı ardından küçük modelle tekrar yazmak
    bağlamı daraltmak olurdu.
    """
    veri = ihlaller.get("veri", {})
    pf_poz = {p["sembol"]: p for p in pf.get("pozisyonlar", [])}
    atla = set(atla or ())
    gruplar = {}
    for t in ihlaller.get("tetiklenen", []):
        if t.get("siddet") == "iddia":
            gruplar.setdefault(t["iddia_id"], []).append(t)
    tetik_index = {iid: tetik_birlestir(liste) for iid, liste in gruplar.items()}

    if tam:
        hedefler = [(sym, poz, idd, tetik_index.get(idd["id"], {
            "kosul_tipi": "tam_yenileme", "olcum": None, "esik": None,
            "tetikleyici": "günlük toplu gözden geçirme (eşik aşılmadı)"}))
            for sym, poz in tezler.items() if not sym.startswith("_")
            for idd in poz.get("iddialar", []) if idd["id"] not in atla]
    else:
        hedefler = [(sym, poz, idd, tetik_index[idd["id"]])
                    for sym, poz in tezler.items() if not sym.startswith("_")
                    for idd in poz.get("iddialar", [])
                    if idd["id"] in tetik_index and idd["id"] not in atla]

    if not hedefler:
        print("kod 10: yeniden yazılacak iddia yok")
        return [], sayac

    guncellenen = []
    for sym, poz, iddia, tetik in hedefler:
        if sayac["cagri"] >= sinir:
            print(f"BÜTÇE: haftalık sınır ({sinir}) doldu — {iddia['id']} atlandı, "
                  "yalnızca kod 20 çağrıları yapılır")
            break
        prompt = iddia_promptu(sym, poz, iddia, tetik, veri, pf_poz.get(sym), an)
        if dry:
            print(f"--- {iddia['id']} promptu ({model}) ---\n{prompt}\n")
            continue
        sayac["cagri"] += 1
        # Rakam denetiminin kaynakları: prompt (verilen tüm veri) + iddianın eski
        # metni (o rakamlar geçen tur zaten denetlendi).
        cikti, durum = llm_cagir(model, SISTEM_IDDIA, prompt, anahtar,
                                 denetim_kaynaklari=(prompt, iddia.get("metin", "")),
                                 denetim_hazirla=iddia_denetimi)
        if not cikti or cikti.get("durum") not in GECERLI_DURUMLAR \
                or not str(cikti.get("metin", "")).strip():
            neden = {"kaynaksiz_rakam": "kaynaksız rakam ısrarla yazıldı",
                     "parse_edilemedi": "çıktı JSON olarak okunamadı"}.get(
                         durum, "çıktı şemaya uymadı")
            print(f"UYARI {iddia['id']}: {neden} — iddia metni DEĞİŞTİRİLMEDİ, "
                  "'degerlendirilemedi' işaretlendi")
            iddia_isaretle(iddia, "degerlendirilemedi", tetik.get("tetikleyici"), an)
            guncellenen.append(iddia["id"])
            continue
        iddia_isaretle(iddia, cikti["durum"], tetik.get("tetikleyici"), an,
                       str(cikti["metin"]).strip())
        guncellenen.append(iddia["id"])
        print(f"✓ {iddia['id']} → {cikti['durum']}")
    return guncellenen, sayac


def kod20_akisi(tezler, ihlaller, pf, an, model, anahtar, sayac, dry, notlar_yolu,
                karar_yolu):
    """Tez seviyesi: pozisyonun tümünü yeniden değerlendir, uygulanabilir karar üret."""
    veri = ihlaller.get("veri", {})
    pf_poz = {p["sembol"]: p for p in pf.get("pozisyonlar", [])}
    nakit = pf.get("nakit_usd", 0)

    # Tez seviyesi tetikleyicisi olan semboller işlenir; ama prompt'a o sembolün
    # BÜTÜN tetikleyicileri gider — iddia seviyesindekiler de bağlamın parçası.
    tumu, tez_semboller = {}, set()
    for t in ihlaller.get("tetiklenen", []):
        tumu.setdefault(t["sembol"], []).append(t)
        if t.get("siddet") == "tez":
            tez_semboller.add(t["sembol"])
    gruplar = {s: tumu[s] for s in tez_semboller}
    if not gruplar:
        print("kod 20: tez seviyesi tetikleyici yok")
        return [], sayac

    kararlar = []
    for sym, tetikler in gruplar.items():
        poz = tezler.get(sym)
        if not poz:
            continue
        prompt = tez_promptu(sym, poz, tetikler, veri, pf_poz.get(sym), nakit, an)
        if dry:
            print(f"--- {sym} tez promptu ({model}) ---\n{prompt}\n")
            continue
        # Tez seviyesi bütçeye takılmaz (bkz. modül başlığı); çağrı yine sayılır.
        sayac["cagri"] += 1
        eski_metinler = tuple(i.get("metin", "") for i in poz.get("iddialar", []))
        cikti, durum = llm_cagir(model, SISTEM_TEZ, prompt, anahtar,
                                 denetim_kaynaklari=(prompt, poz.get("tez_ozeti", ""))
                                 + eski_metinler,
                                 denetim_hazirla=tez_denetimi)
        tetik_metni = "; ".join(dict.fromkeys(
            t.get("tetikleyici", "") for t in tetikler))

        if not cikti or not str(cikti.get("tez_degerlendirmesi", "")).strip():
            neden = {"kaynaksiz_rakam": "kaynaksız rakam ısrarla yazıldı",
                     "parse_edilemedi": "çıktı JSON olarak okunamadı"}.get(
                         durum, "çıktı şemaya uymadı")
            print(f"UYARI {sym}: {neden} — iddialar DEĞİŞTİRİLMEDİ, işlem üretilmedi")
            for idd in poz.get("iddialar", []):
                if any(t["iddia_id"] == idd["id"] for t in tetikler):
                    iddia_isaretle(idd, "degerlendirilemedi", tetik_metni, an)
            not_ekle(notlar_yolu, f"{iso(an)} · {sym} · DEĞERLENDİRİLEMEDİ",
                     f"Tez seviyesi eşik aşıldı ({tetik_metni}) ama derin modelin "
                     f"çıktısı kullanılamadı: {neden}. İddialar değiştirilmedi, işlem "
                     "yapılmadı; karar Cumartesi turuna kaldı.")
            continue

        durumlar = cikti.get("iddia_durumlari") or {}
        for idd in poz.get("iddialar", []):
            yeni = durumlar.get(idd["id"])
            tetikleyen = any(t["iddia_id"] == idd["id"] for t in tetikler)
            if yeni in GECERLI_DURUMLAR:
                iddia_isaretle(idd, yeni, tetik_metni if tetikleyen else None, an)
            elif tetikleyen:
                iddia_isaretle(idd, "degerlendirilemedi", tetik_metni, an)
        if str(cikti.get("yeni_tez_ozeti", "")).strip():
            poz["tez_ozeti"] = str(cikti["yeni_tez_ozeti"]).strip()

        karar = cikti.get("karar") or {}
        islem = str(karar.get("islem", "")).upper()
        if islem not in GECERLI_ISLEMLER:
            print(f"UYARI {sym}: karar.islem geçersiz ({islem!r}) — işlem üretilmedi")
            islem = None
        if islem:
            kararlar.append({
                "sembol": sym,
                "islem": islem,
                "adet": karar.get("adet"),
                "tutar_usd": karar.get("tutar_usd"),
                "yeni_stop": karar.get("yeni_stop"),
                "gerekce": str(karar.get("gerekce", "")).strip(),
                "carpitma_isareti": str(karar.get("carpitma_isareti", "")).strip(),
                "tetikleyici": tetik_metni,
                "tez_degerlendirmesi": str(cikti["tez_degerlendirmesi"]).strip(),
                "model": model,
                "zaman": iso(an),
            })
            print(f"✓ {sym} tez yeniden değerlendirildi → karar: {islem}")

        cum_notu = str(cikti.get("cumartesi_notu", "")).strip()
        govde = [f"**Tetikleyici:** {tetik_metni}",
                 "", f"**Tez değerlendirmesi:** {cikti['tez_degerlendirmesi']}"]
        if islem:
            govde += ["", f"**Seans içi karar:** {islem}"
                          f" · gerekçe: {karar.get('gerekce', '-')}",
                      f"**Çarpıtma işareti:** {karar.get('carpitma_isareti', '-')}"]
        if cum_notu:
            govde += ["", f"**Cumartesi turu için not:** {cum_notu}"]
        not_ekle(notlar_yolu, f"{iso(an)} · {sym} · TEZ SEVİYESİ", "\n".join(govde))

    if kararlar and not dry:
        json_yaz(karar_yolu, {"zaman": iso(an), "kararlar": kararlar})
        print(f"{len(kararlar)} karar durum/bekleyen_karar.json'a yazıldı "
              "(uygulama islem_uygula.py'de)")
    return kararlar, sayac


def main():
    ap = argparse.ArgumentParser(description="Tetiklenen iddiaları/tezleri yeniden yaz")
    ap.add_argument("--kod", type=int, default=0, help="dedektor.py çıkış kodu (10/20)")
    ap.add_argument("--tam-yenileme", action="store_true",
                    help="tüm iddialar küçük modelle toplu gözden geçirilsin")
    ap.add_argument("--dry-run", action="store_true",
                    help="LLM çağrısı yapma, promptları bas")
    ap.add_argument("--durum-dizin", default=os.path.join(BASE, "durum"))
    args = ap.parse_args()

    anahtar = env("OPENROUTER_API_KEY")
    if not anahtar and not args.dry_run:
        print("OPENROUTER_API_KEY yok — yeniden değerlendirme atlandı "
              "(dedektör ölçmeye devam ediyor, yalnızca yorum tazelenmiyor)")
        return 0

    an = simdi()
    tezler = json_oku(TEZLER_YOLU, {})
    pf = json_oku(PF_YOLU, {"pozisyonlar": [], "nakit_usd": 0})
    ihlaller = json_oku(os.path.join(args.durum_dizin, "ihlaller.json"), {})
    if not ihlaller:
        print("durum/ihlaller.json yok — önce dedektor.py koşmalı")
        return 0

    sayac_yolu = os.path.join(args.durum_dizin, "llm_sayac.json")
    notlar_yolu = os.path.join(args.durum_dizin, "bekleyen_notlar.md")
    karar_yolu = os.path.join(args.durum_dizin, "bekleyen_karar.json")
    cooldown_yolu = os.path.join(args.durum_dizin, "cooldown.json")
    sayac, sinir = butce_durumu(sayac_yolu, an)
    butce_doldu = sayac["cagri"] >= sinir
    if butce_doldu:
        print(f"BÜTÇE DOLDU: {hafta_etiketi(an)} haftasında {sayac['cagri']}/{sinir} "
              "çağrı yapıldı — yalnızca kod 20 çağrıları yapılacak")

    hizli = env("OPENROUTER_MODEL_HIZLI", VARSAYILAN_HIZLI)
    derin = env("OPENROUTER_MODEL_DERIN", VARSAYILAN_DERIN)
    guncellenen, kararlar = [], []

    # Tez seviyesinde ele alınan iddialar, ardından küçük modelle tekrar yazılmaz.
    tez_iddialari = {t["iddia_id"] for t in ihlaller.get("tetiklenen", [])
                     if t.get("siddet") == "tez"}
    if args.kod >= 20:
        kararlar, sayac = kod20_akisi(tezler, ihlaller, pf, an, derin, anahtar, sayac,
                                      args.dry_run, notlar_yolu, karar_yolu)
    # Aynı koşumda hem tez hem iddia tetiklenmiş olabilir; ikisi de işlenir.
    if (args.kod >= 10 or args.tam_yenileme) and not butce_doldu:
        guncellenen, sayac = kod10_akisi(tezler, ihlaller, pf, an, hizli, anahtar,
                                         sayac, sinir, args.dry_run, args.tam_yenileme,
                                         atla=tez_iddialari)

    if args.dry_run:
        return 0

    if guncellenen or kararlar:
        json_yaz(TEZLER_YOLU, tezler)
        cooldown = json_oku(cooldown_yolu, {})
        for iid in guncellenen:
            cooldown[iid] = iso(an)
        for k in kararlar:
            cooldown[f"tez:{k['sembol']}"] = iso(an)
        json_yaz(cooldown_yolu, cooldown)
    json_yaz(sayac_yolu, sayac)

    gh_out = env("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"guncellenen_iddia={','.join(guncellenen)}\n")
            f.write(f"karar_sayisi={len(kararlar)}\n")
            f.write(f"llm_cagri={sayac['cagri']}/{sinir}\n")
    print(f"Haftalık LLM çağrısı: {sayac['cagri']}/{sinir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
