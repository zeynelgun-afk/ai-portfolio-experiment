#!/usr/bin/env python3
"""dedektor.py testleri — sahte fiyat serileriyle eşik, histerezis, cooldown, bant.

Ağ yok: `calistir()` saf fonksiyon, veriyi sözlük olarak alıyor. CLI modları
(`--dry-run`, `--sabit-veri`) subprocess ile ayrıca koşuluyor.

Koşum:  python -m unittest discover -s tests -v
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import dedektor  # noqa: E402

AN = datetime(2026, 9, 28, 15, 0, tzinfo=timezone.utc)  # Pazartesi, seans içi


def tez(kosullar, sembol="MU", iddia_id="MU-1"):
    return {sembol: {"tez_ozeti": "test", "iddialar": [
        {"id": iddia_id, "metin": "test iddiası", "kosullar": kosullar,
         "durum": "gecerli", "son_guncelleme": None, "tetikleyici": None}]}}


def veri(fiyat=900.0, onceki=1000.0, hacim=None, ort=None, bilanco=None, **ek):
    d = {"fiyat": fiyat, "onceki_kapanis": onceki, "hacim": hacim,
         "hacim_ort_20g": ort, "bilanco_tarihi": bilanco}
    d.update(ek)
    return {"MU": d}


def kosar(tezler, v, eski=None, cooldown=None, an=AN, stoplar=None, tam=False):
    return dedektor.calistir(tezler, v, stoplar or {"MU": 730},
                             eski or {}, cooldown or {}, an, tam)


class EsikTesti(unittest.TestCase):
    def test_fiyat_alti_esigi_asilinca_ihlal(self):
        r = kosar(tez([{"tip": "fiyat_alti", "deger": 941.62, "siddet": "iddia"}]),
                  veri(fiyat=905.40, onceki=1082.28))
        self.assertTrue(r["kosullar"]["MU-1#0"]["ihlal"])

    def test_esigin_ustunde_ihlal_yok(self):
        r = kosar(tez([{"tip": "fiyat_alti", "deger": 941.62, "siddet": "iddia"}]),
                  veri(fiyat=1000.0, onceki=1082.28))
        self.assertFalse(r["kosullar"]["MU-1#0"]["ihlal"])
        self.assertEqual(r["kod"], 0)

    def test_siddet_cikis_koduna_donusuyor(self):
        for siddet, beklenen in (("uyari", 0), ("iddia", 10), ("tez", 20)):
            k = [{"tip": "fiyat_alti", "deger": 941.62, "siddet": siddet}]
            durum = {}
            for _ in range(2):  # histerezisi geç
                r = kosar(tez(k), veri(fiyat=905.40, onceki=1082.28), eski=durum)
                durum = r["kosullar"]
            self.assertEqual(r["kod"], beklenen, f"şiddet {siddet}")

    def test_stop_yakinligi_yuzde_mesafeyle_olculuyor(self):
        k = [{"tip": "stop_yakinlik_pct", "deger": 5, "siddet": "iddia"}]
        yakin = kosar(tez(k), veri(fiyat=750.0, onceki=800.0))   # stop 730 → %+2.7
        uzak = kosar(tez(k), veri(fiyat=1000.0, onceki=1000.0))  # → %+37.0
        self.assertTrue(yakin["kosullar"]["MU-1#0"]["ihlal"])
        self.assertFalse(uzak["kosullar"]["MU-1#0"]["ihlal"])

    def test_hacim_orani_ust_yonlu_ihlal(self):
        k = [{"tip": "hacim_oran_20g", "deger": 3.0, "siddet": "iddia"}]
        patlama = kosar(tez(k), veri(hacim=62_000_000, ort=17_000_000))  # 3.6x
        normal = kosar(tez(k), veri(hacim=20_000_000, ort=17_000_000))   # 1.2x
        self.assertTrue(patlama["kosullar"]["MU-1#0"]["ihlal"])
        self.assertFalse(normal["kosullar"]["MU-1#0"]["ihlal"])

    def test_hacim_verisi_yoksa_kosul_atlanir(self):
        k = [{"tip": "hacim_oran_20g", "deger": 3.0, "siddet": "iddia"}]
        r = kosar(tez(k), veri(hacim=None, ort=None))
        self.assertNotIn("MU-1#0", r["kosullar"])
        self.assertEqual(r["kod"], 0)

    def test_gunluk_degisim_negatif_esik(self):
        k = [{"tip": "gunluk_degisim_pct", "deger": -7, "siddet": "tez"}]
        cakil = kosar(tez(k), veri(fiyat=905.40, onceki=1000.0))  # %-9.5
        hafif = kosar(tez(k), veri(fiyat=970.0, onceki=1000.0))   # %-3.0
        self.assertTrue(cakil["kosullar"]["MU-1#0"]["ihlal"])
        self.assertFalse(hafif["kosullar"]["MU-1#0"]["ihlal"])

    def test_sektor_etfi_kendi_serisinden_olculuyor(self):
        k = [{"tip": "sektor_etf_degisim_pct", "sembol": "SMH", "deger": -4,
              "siddet": "iddia"}]
        v = veri(fiyat=1000.0, onceki=1000.0)  # sembolün kendisi sakin
        v["SMH"] = {"fiyat": 596.20, "onceki_kapanis": 627.10}  # %-4.9
        r = kosar(tez(k), v)
        self.assertTrue(r["kosullar"]["MU-1#0"]["ihlal"])
        self.assertIn("SMH", r["kosullar"]["MU-1#0"]["aciklama"])

    def test_bilanco_yaklasmasi_ve_gecmis_bilanco(self):
        k = [{"tip": "bilanco_tarihi_yaklasti", "gun": 3, "siddet": "uyari"}]
        yakin = kosar(tez(k), veri(bilanco="2026-09-30"))  # 2 gün
        uzak = kosar(tez(k), veri(bilanco="2026-11-03"))
        gecmis = kosar(tez(k), veri(bilanco="2026-09-01"))
        self.assertTrue(yakin["kosullar"]["MU-1#0"]["ihlal"])
        self.assertFalse(uzak["kosullar"]["MU-1#0"]["ihlal"])
        self.assertNotIn("MU-1#0", gecmis["kosullar"])

    def test_bilanco_tarihi_yoksa_hata_vermez(self):
        k = [{"tip": "bilanco_tarihi_yaklasti", "gun": 3, "siddet": "uyari"}]
        for bozuk in (None, "", "bilinmiyor"):
            r = kosar(tez(k), veri(bilanco=bozuk))
            self.assertEqual(r["kod"], 0)

    def test_bilinmeyen_kosul_tipi_sessizce_atlanir(self):
        r = kosar(tez([{"tip": "henuz_yok", "deger": 1, "siddet": "tez"}]), veri())
        self.assertEqual(r["kod"], 0)


class HisterezisTesti(unittest.TestCase):
    KOSUL = [{"tip": "fiyat_alti", "deger": 941.62, "siddet": "iddia"}]

    def test_ilk_kontrol_teyit_etmez(self):
        r = kosar(tez(self.KOSUL), veri(fiyat=905.40, onceki=1082.28))
        k = r["kosullar"]["MU-1#0"]
        self.assertEqual((k["ardisik"], k["onayli"], r["kod"]), (1, False, 0))
        self.assertEqual(r["tetiklenen"], [])

    def test_ikinci_ardisik_kontrol_teyit_eder(self):
        v = veri(fiyat=905.40, onceki=1082.28)
        birinci = kosar(tez(self.KOSUL), v)
        ikinci = kosar(tez(self.KOSUL), v, eski=birinci["kosullar"])
        k = ikinci["kosullar"]["MU-1#0"]
        self.assertEqual((k["ardisik"], k["onayli"], ikinci["kod"]), (2, True, 10))
        self.assertEqual(len(ikinci["tetiklenen"]), 1)

    def test_arada_temizlenen_kosul_sayaci_sifirlar(self):
        t = tez(self.KOSUL)
        birinci = kosar(t, veri(fiyat=905.40, onceki=1082.28))
        # Bandın üstüne dönüş: 941.62 * 1.01 = 951.04
        temiz = kosar(t, veri(fiyat=960.0, onceki=1082.28), eski=birinci["kosullar"])
        yeniden = kosar(t, veri(fiyat=905.40, onceki=1082.28), eski=temiz["kosullar"])
        self.assertEqual(temiz["kosullar"]["MU-1#0"]["ardisik"], 0)
        self.assertEqual(yeniden["kosullar"]["MU-1#0"]["ardisik"], 1)
        self.assertFalse(yeniden["kosullar"]["MU-1#0"]["onayli"])

    def test_supheli_veri_uc_ardisik_kontrol_ister(self):
        # %-30 sapma: bozuk bar olabilir. Üç kontrol geçmeden tetiklenmez.
        v = veri(fiyat=700.0, onceki=1000.0)
        t = tez(self.KOSUL)
        durum, kodlar = {}, []
        for _ in range(3):
            r = kosar(t, v, eski=durum)
            durum = r["kosullar"]
            kodlar.append(r["kod"])
        self.assertEqual(kodlar, [0, 0, 10])
        self.assertTrue(durum["MU-1#0"]["veri_supheli"])
        self.assertEqual(durum["MU-1#0"]["gereken_ardisik"], 3)


class GeriDonusBandiTesti(unittest.TestCase):
    """850 altı tetikler, 858.5 üstü temizler — arada salınan fiyat sinyal üretmez."""
    KOSUL = [{"tip": "fiyat_alti", "deger": 850, "siddet": "iddia"}]

    def ihlalde(self, fiyat, eski):
        r = kosar(tez(self.KOSUL), veri(fiyat=fiyat, onceki=860.0), eski=eski)
        return r["kosullar"]["MU-1#0"]["ihlal"], r["kosullar"]

    def test_bant_icinde_ihlal_surer(self):
        ihlal, durum = self.ihlalde(845.0, {})
        self.assertTrue(ihlal)
        for fiyat in (851.0, 855.0, 858.0):  # eşiğin üstü ama bandın içi
            ihlal, durum = self.ihlalde(fiyat, durum)
            self.assertTrue(ihlal, f"{fiyat} bandın içinde, ihlal sürmeliydi")

    def test_bandin_ustunde_temizlenir(self):
        _, durum = self.ihlalde(845.0, {})
        ihlal, _ = self.ihlalde(859.0, durum)  # 850 * 1.01 = 858.5 üstü
        self.assertFalse(ihlal)

    def test_ihlalde_olmayan_kosul_bandin_altinda_tetiklenmez(self):
        ihlal, _ = self.ihlalde(852.0, {})  # eşiğin üstü, hiç ihlalde değildi
        self.assertFalse(ihlal)


class CooldownTesti(unittest.TestCase):
    KOSUL = [{"tip": "fiyat_alti", "deger": 941.62, "siddet": "iddia"}]

    def teyitli_durum(self):
        v = veri(fiyat=905.40, onceki=1082.28)
        birinci = kosar(tez(self.KOSUL), v)
        return v, birinci["kosullar"]

    def test_taze_cooldown_tetiklemeyi_engeller(self):
        v, durum = self.teyitli_durum()
        cd = {"MU-1": dedektor.iso(AN - timedelta(hours=1))}
        r = kosar(tez(self.KOSUL), v, eski=durum, cooldown=cd)
        self.assertTrue(r["kosullar"]["MU-1#0"]["onayli"])
        self.assertEqual(r["tetiklenen"], [])
        self.assertEqual(r["kod"], 0)
        self.assertTrue(r["kosullar"]["MU-1#0"]["cooldown"])

    def test_dort_saat_sonra_yeniden_tetiklenir(self):
        v, durum = self.teyitli_durum()
        cd = {"MU-1": dedektor.iso(AN - timedelta(hours=4, minutes=1))}
        r = kosar(tez(self.KOSUL), v, eski=durum, cooldown=cd)
        self.assertEqual(r["kod"], 10)

    def test_tez_seviyesi_cooldownu_pozisyon_bazli(self):
        k = [{"tip": "fiyat_alti", "deger": 941.62, "siddet": "tez"}]
        v = veri(fiyat=905.40, onceki=1082.28)
        durum = kosar(tez(k), v)["kosullar"]
        # iddia anahtarı tez seviyesini engellemez; engelleyen anahtar "tez:MU"
        acik = kosar(tez(k), v, eski=durum,
                     cooldown={"MU-1": dedektor.iso(AN)})
        kapali = kosar(tez(k), v, eski=durum,
                       cooldown={"tez:MU": dedektor.iso(AN)})
        self.assertEqual(acik["kod"], 20)
        self.assertEqual(kapali["kod"], 0)

    def test_bozuk_cooldown_damgasi_engellemez(self):
        v, durum = self.teyitli_durum()
        r = kosar(tez(self.KOSUL), v, eski=durum, cooldown={"MU-1": "bozuk"})
        self.assertEqual(r["kod"], 10)


class SeansVeTamYenilemeTesti(unittest.TestCase):
    def test_tam_yenileme_esik_asilmadan_kod_10(self):
        r = kosar(tez([{"tip": "fiyat_alti", "deger": 500, "siddet": "iddia"}]),
                  veri(fiyat=1000.0, onceki=1000.0), tam=True)
        self.assertEqual(r["kod"], 10)
        self.assertEqual(r["tetiklenen"], [])

    def test_tam_yenileme_tez_seviyesini_ezmez(self):
        k = [{"tip": "fiyat_alti", "deger": 941.62, "siddet": "tez"}]
        v = veri(fiyat=905.40, onceki=1082.28)
        durum = kosar(tez(k), v)["kosullar"]
        r = kosar(tez(k), v, eski=durum, tam=True)
        self.assertEqual(r["kod"], 20)

    def test_seans_penceresi(self):
        self.assertTrue(dedektor.seans_ici(datetime(2026, 9, 28, 14, 0, tzinfo=timezone.utc)))
        self.assertFalse(dedektor.seans_ici(datetime(2026, 9, 28, 21, 15, tzinfo=timezone.utc)))
        self.assertFalse(dedektor.seans_ici(datetime(2026, 9, 26, 15, 0, tzinfo=timezone.utc)))

    def test_uyari_seviyesi_isaret_uretir_kod_uretmez(self):
        k = [{"tip": "fiyat_alti", "deger": 941.62, "siddet": "uyari"}]
        v = veri(fiyat=905.40, onceki=1082.28)
        durum = kosar(tez(k), v)["kosullar"]
        r = kosar(tez(k), v, eski=durum)
        self.assertEqual(r["kod"], 0)
        self.assertEqual(len(r["isaretler"]), 1)


class CliTesti(unittest.TestCase):
    """--dry-run ve --sabit-veri: ağ yok, dosya yazımı yok."""

    def kos(self, *ek, dizin=None):
        with tempfile.TemporaryDirectory() as gecici:
            hedef = dizin or gecici
            p = subprocess.run(
                [sys.executable, os.path.join(BASE, "dedektor.py"),
                 "--sabit-veri", os.path.join(BASE, "tests", "ornek.json"),
                 "--durum-dizin", hedef, *ek],
                capture_output=True, text=True, cwd=BASE)
            return p, sorted(os.listdir(hedef))

    def test_sabit_veri_ile_calisir_ve_durum_yazar(self):
        p, dosyalar = self.kos()
        self.assertEqual(p.returncode, 0, p.stderr)  # ilk kontrol: histerezis bekliyor
        self.assertIn("ihlaller.json", dosyalar)
        self.assertIn("teyit bekliyor", p.stdout)

    def test_dry_run_hicbir_dosya_yazmaz(self):
        p, dosyalar = self.kos("--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(dosyalar, [])

    def test_iki_ardisik_kosum_tetikler(self):
        with tempfile.TemporaryDirectory() as gecici:
            for _ in range(2):
                p, _ = self.kos(dizin=gecici)
            # ornek.json: MU 905.40 → 941.62 altı (iddia) ve günlük %-16.3 → tez eşiği.
            # Ama %-16.3 sapma şüpheli değil (< %25), tez koşulu ikinci turda teyitlenir.
            self.assertEqual(p.returncode, 20, p.stdout + p.stderr)
            with open(os.path.join(gecici, "ihlaller.json"), encoding="utf-8") as f:
                durum = json.load(f)
        self.assertTrue(durum["tetiklenen"])
        self.assertTrue(any(t["siddet"] == "tez" for t in durum["tetiklenen"]))

    def test_tam_yenileme_bayragi_kodu_yukseltir(self):
        with tempfile.TemporaryDirectory() as gecici:
            p, _ = self.kos("--tam-yenileme", dizin=gecici)
        self.assertEqual(p.returncode, 10, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
