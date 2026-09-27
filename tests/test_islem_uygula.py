#!/usr/bin/env python3
"""islem_uygula.py testleri — otonom seans içi işlemin aritmetiği ve kapıları.

Buradaki testlerin hepsi "karar doğru mu?" değil, "bu sayılarla bu işlem yapılabilir mi?"
sorusunu sınıyor. Kararın içeriği AI'ın; aritmetik ve veri bütünlüğü scriptin.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import islem_uygula as iu  # noqa: E402

AN = datetime(2026, 9, 28, 15, 0, tzinfo=timezone.utc)
BUGUN = AN.date()


def portfoy():
    return {
        "nakit_usd": 16421.0,
        "pozisyonlar": [
            {"sembol": "MU", "adet": 33.6072, "giris_fiyati": 892.67,
             "maliyet_usd": 30000.0, "stop_haftalik_kapanis": 730},
            {"sembol": "NVDA", "adet": 65.11, "giris_fiyati": 230.36,
             "maliyet_usd": 15000.0, "stop_haftalik_kapanis": 190},
        ],
        "islem_gecmisi": [],
    }


def canli(fiyat=905.40, sembol="MU", kaynak=iu.CANLI_KAYNAK):
    return {sembol: {"fiyat": fiyat, "onceki_kapanis": 1082.28, "veri_kaynagi": kaynak}}


def karar(islem="KIRP", sembol="MU", **ek):
    k = {"sembol": sembol, "islem": islem, "adet": None, "tutar_usd": None,
         "yeni_stop": None, "gerekce": "test gerekçesi",
         "carpitma_isareti": "test işareti", "tetikleyici": "fiyat 905.40 < 941.62",
         "tez_degerlendirmesi": "test değerlendirmesi", "model": "test-model"}
    k.update(ek)
    return k


class DogrulamaKapilariTesti(unittest.TestCase):
    def dogrula(self, k, *, seans=True, veri=None, kilitler=None, pf=None):
        return iu.dogrula(k, pf or portfoy(), veri or canli(), seans,
                          kilitler or {}, BUGUN)

    def test_tut_karari_islem_uretmez(self):
        tamam, neden, _ = self.dogrula(karar("TUT"))
        self.assertFalse(tamam)
        self.assertIn("TUT", neden)

    def test_seans_kapaliyken_islem_yapilmaz(self):
        tamam, neden, _ = self.dogrula(karar(adet=5), seans=False)
        self.assertFalse(tamam)
        self.assertIn("seans kapalı", neden)

    def test_canli_olmayan_fiyat_kaynagi_reddedilir(self):
        tamam, neden, _ = self.dogrula(karar(adet=5),
                                       veri=canli(kaynak="gunluk_kapanis"))
        self.assertFalse(tamam)
        self.assertIn("canlı değil", neden)

    def test_fiyat_yoksa_islem_yapilmaz(self):
        tamam, neden, _ = self.dogrula(karar(adet=5), veri={"MU": {
            "fiyat": None, "veri_kaynagi": iu.CANLI_KAYNAK}})
        self.assertFalse(tamam)
        self.assertIn("fiyat yok", neden)

    def test_adet_elindekinden_fazla_olamaz(self):
        tamam, neden, _ = self.dogrula(karar(adet=100))
        self.assertFalse(tamam)
        self.assertIn("elindekinden fazla", neden)

    def test_nakit_yetmezse_al_reddedilir(self):
        tamam, neden, _ = self.dogrula(karar("AL", tutar_usd=50000))
        self.assertFalse(tamam)
        self.assertIn("nakit yetmiyor", neden)

    def test_portfoyde_olmayan_sembol_satilamaz(self):
        tamam, neden, _ = self.dogrula(karar("SAT", sembol="AMD"),
                                       veri=canli(sembol="AMD"))
        self.assertFalse(tamam)
        self.assertIn("portföyde yok", neden)

    def test_ayni_gun_ayni_yonde_ikinci_islem_engellenir(self):
        kilit = {f"{BUGUN.isoformat()}:MU:KIRP": "2026-09-28T14:00Z"}
        tamam, neden, _ = self.dogrula(karar(adet=5), kilitler=kilit)
        self.assertFalse(tamam)
        self.assertIn("zaten yapıldı", neden)

    def test_gecersiz_adet_ve_tutar(self):
        for k in (karar(adet=None), karar(adet=-3), karar(adet="çok"),
                  karar("AL", tutar_usd=0), karar("AL", tutar_usd=None)):
            tamam, neden, _ = self.dogrula(k)
            self.assertFalse(tamam, k)
            self.assertTrue("geçersiz" in neden, neden)

    def test_gecerli_kirp_karari_gecer(self):
        tamam, neden, ayrinti = self.dogrula(karar(adet=10))
        self.assertTrue(tamam, neden)
        self.assertAlmostEqual(ayrinti["tutar"], 10 * 905.40, places=2)

    def test_sat_karari_adeti_elindekine_esitler(self):
        tamam, _, ayrinti = self.dogrula(karar("SAT", adet=999))
        self.assertTrue(tamam)
        self.assertAlmostEqual(ayrinti["adet"], 33.6072, places=4)


class AritmetikTesti(unittest.TestCase):
    def test_kirp_adeti_ve_maliyeti_oransal_dusurur(self):
        pf = portfoy()
        ayrinti = {"adet": 10.0, "fiyat": 905.40, "tutar": 9054.0}
        kayit = iu.uygula(karar("KIRP", adet=10), pf, ayrinti, AN)
        poz = next(p for p in pf["pozisyonlar"] if p["sembol"] == "MU")
        self.assertAlmostEqual(poz["adet"], 23.6072, places=4)
        # 30000 * (23.6072 / 33.6072) = 21073.34
        self.assertAlmostEqual(poz["maliyet_usd"], 21073.34, places=2)
        self.assertAlmostEqual(pf["nakit_usd"], 16421.0 + 9054.0, places=2)
        self.assertEqual(kayit["islem"], "KIRP")
        self.assertEqual(kayit["kaynak"], "seans_ici_otonom")

    def test_sat_pozisyonu_tamamen_kaldirir(self):
        pf = portfoy()
        ayrinti = {"adet": 33.6072, "fiyat": 905.40, "tutar": 30428.36}
        kayit = iu.uygula(karar("SAT", adet=33.6072), pf, ayrinti, AN)
        self.assertEqual([p["sembol"] for p in pf["pozisyonlar"]], ["NVDA"])
        self.assertAlmostEqual(pf["nakit_usd"], 16421.0 + 30428.36, places=2)
        self.assertEqual(kayit["islem"], "SAT")

    def test_al_mevcut_pozisyona_eklerken_ortalama_girisi_yeniler(self):
        pf = portfoy()
        ayrinti = {"adet": 10.0, "fiyat": 905.40, "tutar": 9054.0}
        iu.uygula(karar("AL", sembol="MU", tutar_usd=9054.0), pf, ayrinti, AN)
        poz = next(p for p in pf["pozisyonlar"] if p["sembol"] == "MU")
        self.assertAlmostEqual(poz["adet"], 43.6072, places=4)
        self.assertAlmostEqual(poz["maliyet_usd"], 39054.0, places=2)
        # 39054 / 43.6072 = 895.59
        self.assertAlmostEqual(poz["giris_fiyati"], 895.59, places=2)
        self.assertAlmostEqual(pf["nakit_usd"], 16421.0 - 9054.0, places=2)

    def test_al_yeni_sembol_icin_pozisyon_acar(self):
        pf = portfoy()
        ayrinti = {"adet": 20.0, "fiyat": 500.0, "tutar": 10000.0}
        iu.uygula(karar("AL", sembol="AMD", tutar_usd=10000.0, yeni_stop=440), pf,
                  ayrinti, AN)
        poz = next(p for p in pf["pozisyonlar"] if p["sembol"] == "AMD")
        self.assertEqual(poz["giris_tarihi"], BUGUN.isoformat())
        self.assertEqual(poz["stop_haftalik_kapanis"], 440)

    def test_yeni_stop_mevcut_pozisyona_islenir(self):
        pf = portfoy()
        ayrinti = {"adet": 5.0, "fiyat": 905.40, "tutar": 4527.0}
        iu.uygula(karar("KIRP", adet=5, yeni_stop=820), pf, ayrinti, AN)
        poz = next(p for p in pf["pozisyonlar"] if p["sembol"] == "MU")
        self.assertEqual(poz["stop_haftalik_kapanis"], 820)

    def test_islem_gecmisine_saat_ve_kaynak_yazilir(self):
        pf = portfoy()
        iu.uygula(karar("KIRP", adet=5), pf,
                  {"adet": 5.0, "fiyat": 905.40, "tutar": 4527.0}, AN)
        kayit = pf["islem_gecmisi"][-1]
        self.assertEqual(kayit["saat_utc"], "15:00")
        self.assertEqual(pf["son_guncelleme"], BUGUN.isoformat())


class UctanUcaTesti(unittest.TestCase):
    """main() akışı: bekleyen_karar.json → portfoy.json + KARAR_GUNLUGU.md."""

    def kur(self, gecici, kararlar, seans=True, kaynak=iu.CANLI_KAYNAK):
        durum = os.path.join(gecici, "durum")
        os.makedirs(durum)
        iu.json_yaz(os.path.join(durum, "bekleyen_karar.json"),
                    {"zaman": "2026-09-28T15:00Z", "kararlar": kararlar})
        iu.json_yaz(os.path.join(durum, "ihlaller.json"),
                    {"seans_ici": seans, "veri": canli(kaynak=kaynak)})
        iu.PF_YOLU = os.path.join(gecici, "portfoy.json")
        iu.GUNLUK_YOLU = os.path.join(gecici, "KARAR_GUNLUGU.md")
        iu.json_yaz(iu.PF_YOLU, portfoy())
        with open(iu.GUNLUK_YOLU, "w", encoding="utf-8") as f:
            f.write("# Karar Günlüğü\n")
        return durum

    def kos(self, durum, *ek):
        eski = sys.argv
        sys.argv = ["islem_uygula.py", "--durum-dizin", durum, *ek]
        try:
            return iu.main()
        finally:
            sys.argv = eski

    def setUp(self):
        self._yollar = (iu.PF_YOLU, iu.GUNLUK_YOLU)

    def tearDown(self):
        iu.PF_YOLU, iu.GUNLUK_YOLU = self._yollar

    def test_uygulanan_islem_dosyalara_ve_gunluge_yazilir(self):
        with tempfile.TemporaryDirectory() as gecici:
            durum = self.kur(gecici, [karar("KIRP", adet=10)])
            self.assertEqual(self.kos(durum), 0)
            with open(iu.PF_YOLU, encoding="utf-8") as f:
                pf = json.load(f)
            with open(iu.GUNLUK_YOLU, encoding="utf-8") as f:
                gunluk = f.read()
            self.assertAlmostEqual(
                next(p["adet"] for p in pf["pozisyonlar"] if p["sembol"] == "MU"),
                23.6072, places=4)
            self.assertIn("S#1 — 2026-09-28", gunluk.replace(
                gunluk.split("S#1 — ")[1][:10], "2026-09-28"))
            self.assertIn("SEANS İÇİ KARAR", gunluk)
            self.assertIn("UYGULANDI", gunluk)
            self.assertIn("test işareti", gunluk)
            # Karar paketi tüketildi
            self.assertFalse(os.path.exists(
                os.path.join(durum, "bekleyen_karar.json")))
            with open(os.path.join(durum, "islem_kilidi.json"), encoding="utf-8") as f:
                self.assertTrue(json.load(f))

    def test_reddedilen_karar_gunluge_ve_bekleyen_notlara_yazilir(self):
        with tempfile.TemporaryDirectory() as gecici:
            durum = self.kur(gecici, [karar("KIRP", adet=10)], seans=False)
            self.assertEqual(self.kos(durum), 0)
            with open(iu.PF_YOLU, encoding="utf-8") as f:
                pf = json.load(f)
            with open(iu.GUNLUK_YOLU, encoding="utf-8") as f:
                gunluk = f.read()
            with open(os.path.join(durum, "bekleyen_notlar.md"), encoding="utf-8") as f:
                notlar = f.read()
            # Pozisyona dokunulmadı
            self.assertAlmostEqual(
                next(p["adet"] for p in pf["pozisyonlar"] if p["sembol"] == "MU"),
                33.6072, places=4)
            self.assertIn("UYGULANMADI", gunluk)
            self.assertIn("seans kapalı", gunluk)
            self.assertIn("KARAR UYGULANMADI", notlar)

    def test_dry_run_hicbir_dosyayi_degistirmez(self):
        with tempfile.TemporaryDirectory() as gecici:
            durum = self.kur(gecici, [karar("KIRP", adet=10)])
            with open(iu.PF_YOLU, encoding="utf-8") as f:
                once = f.read()
            self.assertEqual(self.kos(durum, "--dry-run"), 0)
            with open(iu.PF_YOLU, encoding="utf-8") as f:
                self.assertEqual(f.read(), once)
            self.assertTrue(os.path.exists(
                os.path.join(durum, "bekleyen_karar.json")))

    def test_karar_yoksa_sessizce_cikar(self):
        with tempfile.TemporaryDirectory() as gecici:
            durum = self.kur(gecici, [])
            self.assertEqual(self.kos(durum), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
